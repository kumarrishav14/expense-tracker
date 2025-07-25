'''
Enhanced AI-Powered Data Processor

This module provides a sophisticated, multi-pass AI-driven data processor.
It is designed to robustly handle a wide variety of statement formats by
breaking down the analysis into three distinct, sequential passes:
1. Structural Analysis: Identifies machine-readable columns (date, amount).
2. Semantic Mapping: Identifies the human-readable description column.
3. Categorization: Applies business logic to the structured data.
'''

import pandas as pd
import json
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, List, Optional, Callable, Literal, Union
from enum import Enum
import math

from ai.ollama.factory import get_ollama_client
from core.database.db_interface import DatabaseInterface
from .abstract_processor import AbstractDataProcessor, StandardTransaction, enforce_output_schema

# --- Configuration ---
HEAD_SAMPLE_SIZE = 10
RANDOM_SAMPLE_SIZE = 5
TAIL_SAMPLE_SIZE = 10
CATEGORIZATION_BATCH_SIZE = 10
MAX_RETRIES = 1

# --- Schemas for LLM Validation ---

class AmountRepresentation(str, Enum):
    """Defines the structural patterns for representing transaction amounts."""
    DUAL_COLUMN_DEBIT_CREDIT = "dual_column_debit_credit"
    SINGLE_COLUMN_SIGNED = "single_column_signed"
    SINGLE_COLUMN_WITH_TYPE = "single_column_with_type"

class DateInfo(BaseModel):
    """Schema for date column and format."""
    column_name: str
    format_string: str

class AmountInfo(BaseModel):
    """Schema for amount representation details."""
    representation: AmountRepresentation
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    amount_column: Optional[str] = None
    type_column: Optional[str] = None
    debit_identifier: Optional[str] = None
    credit_identifier: Optional[str] = None

class StructuralInfo(BaseModel):
    """The expected JSON structure from the LLM in Pass 1."""
    date_info: DateInfo
    amount_info: AmountInfo

class SemanticMapping(BaseModel):
    """
    The expected JSON structure from the LLM in Pass 2.
    Can hold a single column name (str) or a list of columns (List[str]) for fallback.
    """
    description_column: Union[str, List[str]]

# --- ANSI color codes for debug printing ---
class DebugColors:
    PROMPT = '\033[94m'  # Blue
    LLM_OUTPUT = '\033[93m'  # Yellow
    ENDC = '\033[0m'

class EnhancedAIDataProcessor(AbstractDataProcessor):
    """
    A multi-pass AI processor that standardizes raw data through a sequential pipeline.
    """

    def __init__(self, debug: bool = False):
        """
        Initializes the Enhanced AI Data Processor.

        Args:
            debug: If True, enables printing of debug information.
        """
        self.db_interface = DatabaseInterface()
        self._debug = debug

    def _strip_codefence(self, text: str) -> str:
        """
        Strips code fence from the text if present.
        """
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _create_data_sample(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Constructs a composite sample from the head, random middle, and tail of the DataFrame.
        This provides a comprehensive view for structural analysis.
        """
        if len(df) <= HEAD_SAMPLE_SIZE + RANDOM_SAMPLE_SIZE + TAIL_SAMPLE_SIZE:
            return df

        head = df.head(HEAD_SAMPLE_SIZE)
        tail = df.tail(TAIL_SAMPLE_SIZE)
        
        middle_start_index = HEAD_SAMPLE_SIZE
        middle_end_index = len(df) - TAIL_SAMPLE_SIZE
        middle_sample_size = min(RANDOM_SAMPLE_SIZE, middle_end_index - middle_start_index)

        if middle_sample_size > 0:
            middle = df.iloc[middle_start_index:middle_end_index].sample(n=middle_sample_size, random_state=42)
            return pd.concat([head, middle, tail])
        else:
            return pd.concat([head, tail])

    def _execute_pass_1_structural_analysis(self, df_sample: pd.DataFrame) -> StructuralInfo:
        """
        Executes the first pass to identify the structural elements of the data:
        date column, date format, and amount representation.

        Args:
            df_sample: A representative sample of the raw DataFrame.

        Returns:
            A StructuralInfo object with the discovered schema.

        Raises:
            ValueError: If the LLM fails to return a valid structural schema.
        """
        sample_text = df_sample.to_csv(index=False)
        column_names = df_sample.columns.tolist()

        prompt = f"""
        You are a data structure analyst. Your task is to analyze the following data sample and determine the structure for dates and transaction amounts.

        Available columns: {column_names}

        You must identify:
        1.  **Date Information**:
            - The column containing the transaction date.
            - The Python `strftime` format string for that date (e.g., `%Y-%m-%d`, `%d/%m/%Y`).

        2.  **Amount Information**: Determine how amounts are represented from these options:
            - `{AmountRepresentation.DUAL_COLUMN_DEBIT_CREDIT.value}`: Separate columns for debits and credits amounts.
            - `{AmountRepresentation.SINGLE_COLUMN_SIGNED.value}`: A single column where debits are negative and credits are positive.
            - `{AmountRepresentation.SINGLE_COLUMN_WITH_TYPE.value}`: A single amount column accompanied by a type column that indicates debit or credit.

        3. If the amount representation is `{AmountRepresentation.DUAL_COLUMN_DEBIT_CREDIT.value}`, you must also identify:
            - The column for debits.
            - The column for credits.

        4. If the amount representation is `{AmountRepresentation.SINGLE_COLUMN_WITH_TYPE.value}`, you must also identify:
            - The column for amounts.
            - The column that indicates whether the amount is a debit or credit (e.g., "DR", "Debit", "CR", "Credit").
        
        5. If the amount representation is `{AmountRepresentation.SINGLE_COLUMN_SIGNED.value}`, you must identify:
            - The column for amounts.

        Respond with a single, valid JSON object conforming to the following schema:
        ```json
        {{
          "date_info": {{
            "column_name": "<column_name>",
            "format_string": "<strftime_format>"
          }},
          "amount_info": {{
            "representation": "<AmountRepresentation_enum_value>",
            "debit_column": "<column_name>", // Required for dual_column
            "credit_column": "<column_name>", // Required for dual_column
            "amount_column": "<column_name>", // Required for single_column_signed or single_column_with_type
            "type_column": "<column_name>", // Required for single_column_with_type
            "debit_identifier": "<text_in_type_column>", // e.g., "DR", "Debit"
            "credit_identifier": "<text_in_type_column>" // e.g., "CR", "Credit"
          }}
        }}
        ```

        Data Sample:
        ---
        {sample_text}
        ---

        Respond with only the JSON object.
        """

        if self._debug:
            print(f"\n{DebugColors.PROMPT}{'='*50}\n[PASS 1: STRUCTURAL PROMPT]\n{'='*50}\n{prompt}{DebugColors.ENDC}")

        ollama_client = get_ollama_client()
        response = ollama_client.generate_completion(prompt)

        if self._debug:
            print(f"\n{DebugColors.LLM_OUTPUT}{'='*50}\n[PASS 1: LLM RAW OUTPUT]\n{'='*50}\n{response}{DebugColors.ENDC}")

        response = self._strip_codefence(response)

        try:
            response_json = json.loads(response)
            structural_info = StructuralInfo(**response_json)
            return structural_info
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Failed to decode or validate LLM response for structural analysis: {e}")

    def _get_used_columns(self, structural_info: StructuralInfo) -> List[str]:
        """Extracts all column names that were identified in Pass 1."""
        used = {structural_info.date_info.column_name}
        amount_info = structural_info.amount_info
        if amount_info.representation == AmountRepresentation.DUAL_COLUMN_DEBIT_CREDIT:
            if amount_info.debit_column is not None:
                used.add(amount_info.debit_column)
            if amount_info.credit_column is not None:
                used.add(amount_info.credit_column)
        elif amount_info.representation in [AmountRepresentation.SINGLE_COLUMN_SIGNED, AmountRepresentation.SINGLE_COLUMN_WITH_TYPE]:
            if amount_info.amount_column is not None:
                used.add(amount_info.amount_column)
            if amount_info.type_column:
                used.add(amount_info.type_column)
        return [col for col in used if col is not None]

    def _execute_pass_2_semantic_mapping(self, df: pd.DataFrame, structural_info: StructuralInfo) -> SemanticMapping:
        """
        Executes the second pass to identify the transaction description column
        from the remaining, un-mapped columns.

        Args:
            df: The original DataFrame (for column context).
            structural_info: The result from Pass 1.

        Returns:
            A SemanticMapping object with the identified description column.
        """
        used_columns = self._get_used_columns(structural_info)
        remaining_columns = [col for col in df.columns if col not in used_columns]

        if not remaining_columns:
            raise ValueError("No columns remaining for description mapping.")

        sample_text = df[remaining_columns].head(HEAD_SAMPLE_SIZE).to_csv(index=False)

        prompt = f"""
        You are a financial data analyst. Your task is to identify the column that best represents the transaction **description** or **narrative**.

        The following columns have already been mapped for date and amount:
        {used_columns}

        From the remaining columns below, choose the one that provides the most meaningful description of the transaction.

        Remaining columns: {remaining_columns}

        Here is a sample of the data in the remaining columns:
        ---
        {sample_text}
        ---

        Respond with a single, valid JSON object with one key, "description_column", indicating your choice.
        Example:
        ```json
        {{
          "description_column": "Transaction Details"
        }}
        ```

        Respond with only the JSON object.
        """

        if self._debug:
            print(f"\n{DebugColors.PROMPT}{'='*50}\n[PASS 2: SEMANTIC PROMPT]\n{'='*50}\n{prompt}{DebugColors.ENDC}")

        ollama_client = get_ollama_client()
        response = ollama_client.generate_completion(prompt)

        if self._debug:
            print(f"\n{DebugColors.LLM_OUTPUT}{'='*50}\n[PASS 2: LLM RAW OUTPUT]\n{'='*50}\n{response}{DebugColors.ENDC}")

        response = self._strip_codefence(response)
        try:
            response_json = json.loads(response)
            semantic_mapping = SemanticMapping(**response_json)
            return semantic_mapping
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Failed to decode or validate LLM response for semantic mapping: {e}")

    def _find_best_fallback_description_column(self, columns: List[str]) -> Optional[str]:
        """Finds the best description column from a list based on common keywords."""
        COMMON_KEYWORDS = ['description', 'narrative', 'details', 'transaction', 'memo']
        for keyword in COMMON_KEYWORDS:
            for col in columns:
                if keyword in col.lower():
                    return col
        return None

    def _apply_mappings_to_dataframe(self, df: pd.DataFrame, structural_info: StructuralInfo, semantic_mapping: SemanticMapping) -> pd.DataFrame:
        """
        Uses pandas to transform the raw DataFrame into a standardized intermediate format.
        """
        mapped_data = pd.DataFrame()

        # 1. Map Transaction Date
        date_info = structural_info.date_info
        mapped_data['transaction_date'] = pd.to_datetime(df[date_info.column_name], format=date_info.format_string, errors='coerce').dt.strftime('%Y-%m-%d')

        # 2. Map Description
        if isinstance(semantic_mapping.description_column, list):
            # Fallback: concatenate multiple columns
            mapped_data['description'] = df[semantic_mapping.description_column].astype(str).agg(' - '.join, axis=1)
        else:
            mapped_data['description'] = df[semantic_mapping.description_column]

        # 3. Map Amount
        amount_info = structural_info.amount_info
        if amount_info.representation == AmountRepresentation.DUAL_COLUMN_DEBIT_CREDIT:
            debit = pd.to_numeric(df[amount_info.debit_column], errors='coerce').fillna(0)
            credit = pd.to_numeric(df[amount_info.credit_column], errors='coerce').fillna(0)
            mapped_data['amount'] = credit - debit
        elif amount_info.representation == AmountRepresentation.SINGLE_COLUMN_SIGNED:
            mapped_data['amount'] = pd.to_numeric(df[amount_info.amount_column], errors='coerce').fillna(0)
        elif amount_info.representation == AmountRepresentation.SINGLE_COLUMN_WITH_TYPE:
            amount = pd.to_numeric(df[amount_info.amount_column], errors='coerce').fillna(0)
            # Flip sign for debits
            debit_identifier = amount_info.debit_identifier if amount_info.debit_identifier is not None else ""
            debit_mask = df[amount_info.type_column].str.contains(debit_identifier, case=False)
            amount[debit_mask] = amount[debit_mask] * -1
            mapped_data['amount'] = amount

        # Drop rows where essential data could not be parsed
        mapped_data.dropna(subset=['transaction_date', 'description', 'amount'], inplace=True)
        return mapped_data

    def _prepare_category_prompt_data(self) -> Dict[str, List[str]]:
        """Fetches categories and transforms them into a hierarchical dictionary for the LLM prompt."""
        categories_df = self.db_interface.get_categories_table()
        hierarchy = {}
        parent_categories = categories_df[categories_df['parent_category'].isnull()]['name'].unique()
        for parent in parent_categories:
            hierarchy[parent] = []
        
        for _, row in categories_df.iterrows():
            if pd.notna(row['parent_category']) and row['parent_category'] in hierarchy:
                hierarchy[row['parent_category']].append(row['name'])
        return hierarchy

    def _process_categorization_batch(self, batch_df: pd.DataFrame, category_hierarchy: Dict[str, List[str]]) -> List[Dict]:
        """
        Processes a single batch of standardized data for categorization.
        """
        data_text = batch_df.to_csv(index=False)
        category_json_string = json.dumps(category_hierarchy, indent=2)

        prompt = f"""
        You are an expert financial data categorization AI. Your task is to analyze the following structured transaction data and assign a category and sub_category to each transaction.

        Follow these instructions precisely:
        1.  Assign a 'category' and 'sub_category' from the provided hierarchy.
        2.  If a transaction fits a parent category but no specific sub-category, leave 'sub_category' blank.
        3.  If no suitable category is found, assign 'category' to 'Other' and leave 'sub_category' blank.
        4.  Return a single, valid JSON array of objects. Each object must correspond to a row in the input.

        Here is the category hierarchy to use:
        ```json
        {category_json_string}
        ```

        Transaction Data:
        ---
        {data_text}
        ---

        Respond with only the JSON array. Each object must contain 'category' and 'sub_category'.
        """

        if self._debug:
            print(f"\n{DebugColors.PROMPT}{'='*50}\n[PASS 3: CATEGORIZATION PROMPT]\n{'='*50}\n{prompt}{DebugColors.ENDC}")

        ollama_client = get_ollama_client()
        llm_response = ollama_client.generate_completion(prompt)

        if self._debug:
            print(f"\n{DebugColors.LLM_OUTPUT}{'='*50}\n[PASS 3: LLM RAW OUTPUT]\n{'='*50}\n{llm_response}{DebugColors.ENDC}")

        try:
            parsed_json = json.loads(llm_response)
            if not isinstance(parsed_json, list) or len(parsed_json) != len(batch_df):
                raise ValueError("LLM did not return a valid JSON array of the correct length.")
            return parsed_json
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Skipping batch due to categorization error: {e}")
            return [] # Return empty list to skip the batch

    def _execute_pass_3_categorization(self, mapped_df: pd.DataFrame, on_progress: Optional[Callable[[float, str], None]]) -> pd.DataFrame:
        """
        Executes the final pass to categorize the clean, mapped data in batches.
        """
        if mapped_df.empty:
            return pd.DataFrame()

        category_hierarchy = self._prepare_category_prompt_data()
        all_results = []
        num_batches = math.ceil(len(mapped_df) / CATEGORIZATION_BATCH_SIZE)

        for i in range(num_batches):
            batch_start = i * CATEGORIZATION_BATCH_SIZE
            batch_end = batch_start + CATEGORIZATION_BATCH_SIZE
            batch_df = mapped_df.iloc[batch_start:batch_end]

            if on_progress:
                progress = 0.66 + ((i / num_batches) * 0.34)
                on_progress(progress, f"Categorizing batch {i+1}/{num_batches}...")

            retries = 0
            while retries <= MAX_RETRIES:
                try:
                    categorized_results = self._process_categorization_batch(batch_df, category_hierarchy)
                    if categorized_results:
                        # Combine original batch data with categorized results
                        batch_df.reset_index(drop=True, inplace=True)
                        categorized_df = pd.DataFrame(categorized_results)
                        merged_batch = pd.concat([batch_df, categorized_df], axis=1)
                        all_results.append(merged_batch)
                    break # Success
                except Exception as e:
                    retries += 1
                    print(f"Error processing batch {i+1}, attempt {retries}/{MAX_RETRIES+1}: {e}")
                    if retries > MAX_RETRIES:
                        print(f"Failed to process batch {i+1} after {MAX_RETRIES} retries. Skipping.")
                        break
        
        if not all_results:
            return pd.DataFrame()

        final_df = pd.concat(all_results, ignore_index=True)
        return final_df

    @enforce_output_schema
    def process_raw_data(self, df: pd.DataFrame, on_progress: Optional[Callable[[float, str], None]] = None) -> pd.DataFrame:
        """
        Orchestrates the three-pass pipeline to process the raw DataFrame.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty.")

        # --- Create Data Sample ---
        data_sample = self._create_data_sample(df)

        # --- Pass 1: Structural Analysis ---
        if on_progress:
            on_progress(0.0, "Starting structural analysis...")
        
        try:
            structural_info = self._execute_pass_1_structural_analysis(data_sample)
            if self._debug:
                print(f"\n[PASS 1 COMPLETE] Structural Info: {structural_info.model_dump_json(indent=2)}")
        except ValueError as e:
            # Critical failure, cannot proceed
            if on_progress:
                on_progress(1.0, f"Error: {e}")
            raise

        if on_progress:
            on_progress(0.33, "Structural analysis complete.")

        # --- Pass 2: Semantic Mapping ---
        if on_progress:
            on_progress(0.33, "Starting semantic mapping...")

        try:
            semantic_mapping = self._execute_pass_2_semantic_mapping(df, structural_info)
            if self._debug:
                print(f"\n[PASS 2 COMPLETE] Semantic Mapping: {semantic_mapping.model_dump_json(indent=2)}")
        except ValueError as e:
            # Non-critical failure, proceed with fallback
            if on_progress:
                on_progress(0.66, f"Warning: {e}. Using fallback for description.")
            # Create a fallback mapping by searching for common keywords
            used_columns = self._get_used_columns(structural_info)
            remaining_columns = [col for col in df.columns if col not in used_columns]
            
            best_fallback = self._find_best_fallback_description_column(remaining_columns)
            if best_fallback:
                semantic_mapping = SemanticMapping(description_column=best_fallback)
            else:
                # If no keyword match, resort to concatenating all remaining columns
                semantic_mapping = SemanticMapping(description_column=remaining_columns)


        if on_progress:
            on_progress(0.66, "Semantic mapping complete.")

        # --- Pass 3: Extraction & Categorization ---
        if on_progress:
            on_progress(0.66, "Applying mappings and preparing data...")

        mapped_df = self._apply_mappings_to_dataframe(df, structural_info, semantic_mapping)

        if self._debug:
            print(f"\n[INTERMEDIATE DF] Mapped DataFrame:\n{mapped_df.head()}")

        final_df = self._execute_pass_3_categorization(mapped_df, on_progress)

        if on_progress:
            on_progress(1.0, "Processing complete.")

        return final_df
