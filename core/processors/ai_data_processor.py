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
from typing import Dict, List

from ai.ollama.factory import get_ollama_client
from core.database.db_interface import DatabaseInterface
from .abstract_processor import AbstractDataProcessor, StandardTransaction, enforce_output_schema

class AIDataProcessor(AbstractDataProcessor):
    """
    An AI-driven processor that uses an LLM to convert raw DataFrames into a
    standardized format. It follows the contract defined by AbstractDataProcessor.
    """

    def __init__(self):
        """
        Initializes the AI Data Processor.
        """
        self.db_interface = DatabaseInterface()

    def _prepare_category_prompt_data(self, categories_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Transforms the category DataFrame into a hierarchical dictionary for the LLM prompt.

        Args:
            categories_df: DataFrame from db_interface.get_categories_table().

        Returns:
            A dictionary where keys are parent categories and values are lists of their sub-categories.
        """
        hierarchy = {}
        # Initialize parent categories
        parent_categories = categories_df[categories_df['parent_category'].isnull()]['name'].unique()
        for parent in parent_categories:
            hierarchy[parent] = []
        
        # Populate sub-categories
        for _, row in categories_df.iterrows():
            if pd.notna(row['parent_category']):
                if row['parent_category'] in hierarchy:
                    hierarchy[row['parent_category']].append(row['name'])
        return hierarchy

    def _create_llm_prompt(self, df_text: str, category_hierarchy: Dict[str, List[str]]) -> str:
        """
        Engineers a detailed prompt for the LLM, including the category hierarchy.

        Args:
            df_text: The raw transaction data serialized as a CSV string.
            category_hierarchy: A hierarchical dictionary of categories.

        Returns:
            A string containing the full prompt for the LLM.
        """
        # Convert the hierarchy to a JSON string for clear presentation in the prompt
        category_json_string = json.dumps(category_hierarchy, indent=2)

        return f"""
        You are an expert financial data extraction and categorization AI. Your task is to analyze the following raw transaction data from bank statements, which is in a CSV format, and convert it into a structured JSON output.

        Follow these instructions precisely:
        1.  Analyze each row in the provided data.
        2.  For each row, extract the transaction description, date, and amount.
        3.  The 'description' field in your output MUST be the original description from the raw data.
        4.  The 'transaction_date' must be in 'YYYY-MM-DD' format.
        5.  The 'amount' must be a floating-point number. Represent credits as positive numbers and debits as negative numbers. The balance amount should be ignonred.
        6.  Assign a 'category' and 'sub_category' to each transaction based on the provided hierarchy. The 'category' must be one of the parent keys in the JSON structure. The 'sub_category' must be one of the items from the corresponding list.
        7.  If a transaction clearly fits a parent category but not a specific sub-category, you may leave the 'sub_category' blank.
        8.  If no suitable category is found, assign 'category' to 'Other' and leave 'sub_category' blank.
        9.  Return the output as a single, valid JSON array of objects. Do not include any other text or explanations in your response.
        **You should not split a single row into multiple objects. Each row in the input should correspond to a single object in the output.**

        Here is the category hierarchy to use:
        ```json
        {category_json_string}
        ```

        Here is the raw data:
        ---
        {df_text}
        ---

        Respond with only the JSON array with each json object having below fields:
            "transaction_date",
            "description",
            "amount",
            "category",
            "sub_category"
        """

    @enforce_output_schema
    def process_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes a raw DataFrame using the LLM to standardize and categorize it.
        The method is decorated with @enforce_output_schema from the parent class.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty.")

        # Serialize DataFrame to a CSV string for the LLM
        data_text = df.to_csv(index=False)
        
        # Fetch and prepare categories from the database to guide the LLM
        categories_df = self.db_interface.get_categories_table()
        category_hierarchy = self._prepare_category_prompt_data(categories_df)

        # Create the prompt and get the LLM response
        prompt = self._create_llm_prompt(data_text, category_hierarchy)
        
        # Get a fresh Ollama client to ensure the latest settings are used
        ollama_client = get_ollama_client()
        llm_response = ollama_client.generate_completion(prompt)
        print(f"\n****LLM Response:****\n {llm_response}")
        try:
            # Parse the JSON response from the LLM
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
                    # Validate each record against the Pydantic model
                    validated_transaction = StandardTransaction(**record)
                    validated_records.append(validated_transaction.model_dump())
                except ValidationError as e:
                    print(f"Skipping a record due to validation error: {e}")
                    continue
            
            if not validated_records:
                raise ValueError("No valid transaction records were processed from the LLM response.")

            # Convert the list of validated dictionaries to a DataFrame
            return pd.DataFrame(validated_records)

        except json.JSONDecodeError:
            raise ValueError("Failed to decode JSON from the LLM response.")
        except Exception as e:
            # Catch any other unexpected errors during processing
            raise ValueError(f"An unexpected error occurred while processing the LLM response: {e}")
