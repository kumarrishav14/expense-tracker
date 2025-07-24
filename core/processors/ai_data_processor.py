"""
AI-Powered Data Processor

This module provides an advanced, AI-driven data processor that leverages a
Large Language Model (LLM) to structure and categorize raw transaction data.
It is designed to handle a wide variety of bank statement formats without
relying on hard-coded rules.
"""

import pandas as pd
import json
from pydantic import ValidationError
from typing import Dict, List, Optional, Callable
import math

from ai.ollama.factory import get_ollama_client
from core.database.db_interface import DatabaseInterface
from .abstract_processor import AbstractDataProcessor, StandardTransaction, enforce_output_schema

# Configurable parameters for batch processing
BATCH_SIZE = 15
MAX_RETRIES = 1
DATE_SAMPLE_SIZE = 20

# ANSI color codes for debug printing
class DebugColors:
    PROMPT = '\033[94m'  # Blue
    LLM_OUTPUT = '\033[93m'  # Yellow
    ENDC = '\033[0m'

class AIDataProcessor(AbstractDataProcessor):
    """
    An AI-driven processor that uses an LLM to convert raw DataFrames into a
    standardized format. It follows the contract defined by AbstractDataProcessor.
    """

    def __init__(self, debug: bool = False):
        """
        Initializes the AI Data Processor.

        Args:
            debug: If True, enables printing of debug information like prompts and LLM responses.
        """
        self.db_interface = DatabaseInterface()
        self._debug = debug

    def _prepare_category_prompt_data(self, categories_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Transforms the category DataFrame into a hierarchical dictionary for the LLM prompt.

        Args:
            categories_df: DataFrame from db_interface.get_categories_table().

        Returns:
            A dictionary where keys are parent categories and values are lists of their sub-categories.
        """
        hierarchy = {}
        parent_categories = categories_df[categories_df['parent_category'].isnull()]['name'].unique()
        for parent in parent_categories:
            hierarchy[parent] = []
        
        for _, row in categories_df.iterrows():
            if pd.notna(row['parent_category']) and row['parent_category'] in hierarchy:
                hierarchy[row['parent_category']].append(row['name'])
        return hierarchy

    def _discover_date_format(self, df_sample: pd.DataFrame) -> str:
        """
        Pass 1: Asks the LLM to identify the date format string.
        """
        sample_text = df_sample.to_csv(index=False)
        
        prompt = f"""
        You are a date format expert. Your task is to analyze the following sample data and identify the Python strftime format string for the date column.

        - The date column is the one that contains dates. It could be named anything.
        - Provide only the strftime format string and nothing else. For example: `%Y-%m-%d` or `%d/%m/%Y`.

        Here is the data sample:
        ---
        {sample_text}
        ---

        Respond with only the strftime format string.
        """
        
        if self._debug:
            print(f"\n{DebugColors.PROMPT}{'='*50}\n[DATE DISCOVERY PROMPT]\n{'='*50}\n{prompt}{DebugColors.ENDC}")
        
        ollama_client = get_ollama_client()
        response = ollama_client.generate_completion(prompt).strip()
        
        if not response.startswith('%'):
            raise ValueError(f"LLM returned an invalid date format string: {response}")
            
        print(f"Discovered date format: {response}")
        return response

    def _create_llm_prompt(self, df_text: str, category_hierarchy: Dict[str, List[str]], date_format_string: str) -> str:
        """
        Engineers a detailed prompt for the LLM, including the category hierarchy and date format.
        Args:
            df_text: The raw transaction data serialized as a CSV string.
            category_hierarchy: A hierarchical dictionary of categories.

        Returns:
            A string containing the full prompt for the LLM.
        """
        category_json_string = json.dumps(category_hierarchy, indent=2)

        return f"""
        You are an expert financial data extraction and categorization AI. Your task is to analyze the following raw transaction data and convert it into a structured JSON output.

        Follow these instructions precisely:
        1.  Extract the transaction description, date, and amount.
        2.  The 'description' MUST be the original description from the raw data.
        3.  The 'transaction_date' MUST be in 'YYYY-MM-DD' format. The raw date format is '{date_format_string}'. You must convert it correctly.
        4.  The 'amount' must be a number. Credits are positive, debits are negative.
        5.  Assign a 'category' and 'sub_category' from the provided hierarchy.
        6.  If a transaction clearly fits a parent category but not a specific sub-category, you may leave the 'sub_category' blank.
        7.  If no suitable category is found, assign 'category' to 'Other' and leave 'sub_category' blank.
        8.  Return a single, valid JSON array of objects. Do not include any other text.
        **You should not split a single row into multiple objects. Each row in the input should correspond to a single object in the output. All columns represeting closing balance should be ignored**
        Here is the category hierarchy to use:
        ```json
        {category_json_string}
        ```

        Raw Data:
        ---
        {df_text}
        ---

        Respond with only the JSON array with each json object having below fields:
            "transaction_date" - this should be strcitly in YYYY-MM-DD format,
            "description",
            "amount" - positve for credits and negative for debits,
            "category",
            "sub_category"
        """

    def _process_batch(self, batch_df: pd.DataFrame, category_hierarchy: Dict[str, List[str]], date_format_string: str) -> List[Dict]:
        """
        Processes a single batch of data using the LLM.
        """
        data_text = batch_df.to_csv(index=False)
        prompt = self._create_llm_prompt(data_text, category_hierarchy, date_format_string)
        if self._debug:
            print(f"\n{DebugColors.PROMPT}{'='*50}\n[PROCESSING PROMPT - BATCH]\n{'='*50}\n{prompt}{DebugColors.ENDC}")
        
        ollama_client = get_ollama_client()
        llm_response = ollama_client.generate_completion(prompt)

        if self._debug:
            print(f"\n{DebugColors.LLM_OUTPUT}{'='*50}\n[LLM RAW OUTPUT - BATCH]\n{'='*50}\n{llm_response}{DebugColors.ENDC}")
        
        if llm_response.startswith("```json"):
            llm_response = llm_response[8:].strip()
        if llm_response.endswith("```"):
            llm_response = llm_response[:-3].strip()
            
        parsed_json = json.loads(llm_response)
        if not isinstance(parsed_json, list):
            raise ValueError("LLM did not return a JSON array.")

        validated_records = []
        for record in parsed_json:
            try:
                validated_transaction = StandardTransaction(**record)
                validated_records.append(validated_transaction.model_dump())
            except ValidationError as e:
                print(f"Skipping a record due to validation error: {e}")
                continue
        
        return validated_records

    @enforce_output_schema
    def process_raw_data(self, df: pd.DataFrame, on_progress: Optional[Callable[[float, str], None]] = None) -> pd.DataFrame:
        """
        Processes a raw DataFrame using a two-pass model to ensure accurate date handling.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty.")

        # --- Pass 1: Date Format Discovery ---
        if on_progress:
            on_progress(0.0, "Discovering date format...")
        try:
            sample_df = df.head(DATE_SAMPLE_SIZE)
            date_format_string = self._discover_date_format(sample_df)
        except Exception as e:
            raise ValueError(f"Failed to discover date format: {e}")

        # --- Pass 2: Batch Processing ---
        categories_df = self.db_interface.get_categories_table()
        category_hierarchy = self._prepare_category_prompt_data(categories_df)
        
        all_results = []
        num_batches = math.ceil(len(df) / BATCH_SIZE)

        for i in range(num_batches):
            batch_start = i * BATCH_SIZE
            batch_end = batch_start + BATCH_SIZE
            batch_df = df.iloc[batch_start:batch_end]
            
            retries = 0
            while retries <= MAX_RETRIES:
                try:
                    validated_records = self._process_batch(batch_df, category_hierarchy, date_format_string)
                    all_results.extend(validated_records)
                    
                    if on_progress:
                        progress = 0.05 + (((i + 1) / num_batches) * 0.95)
                        on_progress(progress, f"Successfully processed batch {i+1}/{num_batches}")
                    
                    break
                
                except Exception as e:
                    retries += 1
                    print(f"Error processing batch {i+1}, attempt {retries}/{MAX_RETRIES+1}: {e}")
                    if retries > MAX_RETRIES:
                        if on_progress:
                            progress = 0.05 + (((i + 1) / num_batches) * 0.95)
                            on_progress(progress, f"Failed to process batch {i+1} after {MAX_RETRIES} retries. Skipping.")
                        break

        if not all_results:
            return pd.DataFrame()

        return pd.DataFrame(all_results)

