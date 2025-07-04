"""
Intelligent column mapping engine for data processor.

This module provides intelligent column mapping capabilities that can automatically
map raw DataFrame columns to standardized schema columns using fuzzy matching,
pattern recognition, and configurable mapping rules.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
import pandas as pd

from .schemas import ColumnMappingRule, ColumnType, ProcessingConfig
from .exceptions import ColumnMappingError


logger = logging.getLogger(__name__)


class ColumnMapper:
    """
    Intelligent column mapping engine.
    
    Maps raw DataFrame columns to standardized schema columns using multiple
    strategies including pattern matching, fuzzy string matching, and
    configurable mapping rules.
    """
    
    def __init__(self, config: ProcessingConfig):
        """
        Initialize the column mapper.
        
        Args:
            config: Processing configuration containing mapping rules
        """
        self.config = config
        self._default_rules = self._create_default_mapping_rules()
        self._compiled_patterns = self._compile_patterns()
    
    def map_columns(self, df: pd.DataFrame) -> Tuple[Dict[str, str], List[str]]:
        """
        Map DataFrame columns to standard schema columns.
        
        Args:
            df: Input DataFrame with raw column names
            
        Returns:
            Tuple of (column_mappings, unmapped_columns)
            - column_mappings: Dict mapping raw column names to standard column types
            - unmapped_columns: List of columns that couldn't be mapped
            
        Raises:
            ColumnMappingError: If required columns cannot be mapped
        """
        logger.info(f"Starting column mapping for {len(df.columns)} columns")
        
        raw_columns = list(df.columns)
        column_mappings = {}
        unmapped_columns = []
        
        # Apply mapping rules in order of priority
        for rule in self._get_all_mapping_rules():
            remaining_columns = [col for col in raw_columns if col not in column_mappings]
            
            if not remaining_columns:
                break
                
            mapped_column = self._apply_mapping_rule(rule, remaining_columns)
            if mapped_column:
                column_mappings[mapped_column] = rule.target_column
                logger.debug(f"Mapped '{mapped_column}' -> '{rule.target_column}'")
        
        # Identify unmapped columns
        unmapped_columns = [col for col in raw_columns if col not in column_mappings]
        
        # Check for missing required columns
        missing_required = self._check_required_columns(column_mappings)
        
        if missing_required:
            raise ColumnMappingError(
                f"Required columns not found: {missing_required}",
                unmapped_columns=unmapped_columns,
                missing_required_columns=missing_required
            )
        
        logger.info(f"Column mapping completed: {len(column_mappings)} mapped, {len(unmapped_columns)} unmapped")
        return column_mappings, unmapped_columns
    
    def _apply_mapping_rule(self, rule: ColumnMappingRule, columns: List[str]) -> Optional[str]:
        """
        Apply a single mapping rule to find the best matching column.
        
        Args:
            rule: Mapping rule to apply
            columns: List of available column names
            
        Returns:
            Best matching column name or None if no match found
        """
        best_match = None
        best_score = 0.0
        
        for column in columns:
            score = self._calculate_column_score(rule, column)
            if score > best_score and score >= rule.similarity_threshold:
                best_score = score
                best_match = column
        
        return best_match
    
    def _calculate_column_score(self, rule: ColumnMappingRule, column: str) -> float:
        """
        Calculate similarity score between a mapping rule and column name.
        
        Args:
            rule: Mapping rule to evaluate
            column: Column name to score
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        column_lower = column.lower().strip()
        scores = []
        
        # Pattern matching score
        pattern_score = self._calculate_pattern_score(rule, column_lower)
        if pattern_score > 0:
            scores.append(pattern_score)
        
        # Keyword similarity score
        keyword_score = self._calculate_keyword_score(rule, column_lower)
        if keyword_score > 0:
            scores.append(keyword_score)
        
        # Return maximum score if any matches found
        return max(scores) if scores else 0.0
    
    def _calculate_pattern_score(self, rule: ColumnMappingRule, column: str) -> float:
        """
        Calculate pattern matching score for a column.
        
        Args:
            rule: Mapping rule with patterns
            column: Column name to evaluate
            
        Returns:
            Pattern matching score (1.0 for exact match, 0.0 for no match)
        """
        for pattern in rule.patterns:
            if re.search(pattern, column, re.IGNORECASE):
                return 1.0
        return 0.0
    
    def _calculate_keyword_score(self, rule: ColumnMappingRule, column: str) -> float:
        """
        Calculate keyword similarity score for a column.
        
        Args:
            rule: Mapping rule with keywords
            column: Column name to evaluate
            
        Returns:
            Best keyword similarity score
        """
        if not rule.keywords:
            return 0.0
        
        best_score = 0.0
        for keyword in rule.keywords:
            # Direct substring match gets high score
            if keyword.lower() in column:
                score = 0.9
            else:
                # Use sequence matcher for fuzzy matching
                score = SequenceMatcher(None, keyword.lower(), column).ratio()
            
            best_score = max(best_score, score)
        
        return best_score
    
    def _get_all_mapping_rules(self) -> List[ColumnMappingRule]:
        """
        Get all mapping rules in priority order.
        
        Returns:
            List of mapping rules (custom rules first, then defaults)
        """
        # Custom rules from config take priority
        all_rules = list(self.config.mapping_rules)
        
        # Add default rules for any missing target columns
        configured_targets = {rule.target_column for rule in self.config.mapping_rules}
        for rule in self._default_rules:
            if rule.target_column not in configured_targets:
                all_rules.append(rule)
        
        return all_rules
    
    def _check_required_columns(self, mappings: Dict[str, str]) -> List[str]:
        """
        Check for missing required columns.
        
        Args:
            mappings: Current column mappings
            
        Returns:
            List of missing required column types
        """
        mapped_types = set(mappings.values())
        missing_required = []
        
        for rule in self._get_all_mapping_rules():
            if rule.required and rule.target_column not in mapped_types:
                missing_required.append(rule.target_column)
        
        return missing_required
    
    def _create_default_mapping_rules(self) -> List[ColumnMappingRule]:
        """
        Create default mapping rules for common bank statement formats.
        
        Returns:
            List of default mapping rules
        """
        return [
            # Date column mapping
            ColumnMappingRule(
                target_column=ColumnType.DATE,
                patterns=[
                    r'^date$',
                    r'^transaction[_\s]*date$',
                    r'^posting[_\s]*date$',
                    r'^value[_\s]*date$'
                ],
                keywords=['date', 'time', 'when', 'day'],
                similarity_threshold=0.6,
                required=True
            ),
            
            # Description column mapping
            ColumnMappingRule(
                target_column=ColumnType.DESCRIPTION,
                patterns=[
                    r'^description$',
                    r'^details$',
                    r'^particulars$',
                    r'^narrative$',
                    r'^memo$'
                ],
                keywords=['description', 'details', 'particulars', 'narrative', 'memo', 'reference'],
                similarity_threshold=0.6,
                required=True
            ),
            
            # Amount column mapping
            ColumnMappingRule(
                target_column=ColumnType.AMOUNT,
                patterns=[
                    r'^amount$',
                    r'^transaction[_\s]*amount$',
                    r'^debit$',
                    r'^credit$',
                    r'^value$'
                ],
                keywords=['amount', 'value', 'sum', 'total', 'debit', 'credit'],
                similarity_threshold=0.6,
                required=True
            ),
            
            # Balance column mapping
            ColumnMappingRule(
                target_column=ColumnType.BALANCE,
                patterns=[
                    r'^balance$',
                    r'^running[_\s]*balance$',
                    r'^available[_\s]*balance$',
                    r'^closing[_\s]*balance$'
                ],
                keywords=['balance', 'remaining', 'available'],
                similarity_threshold=0.7,
                required=False
            ),
            
            # Reference column mapping
            ColumnMappingRule(
                target_column=ColumnType.REFERENCE,
                patterns=[
                    r'^reference$',
                    r'^ref[_\s]*no$',
                    r'^transaction[_\s]*id$',
                    r'^cheque[_\s]*no$'
                ],
                keywords=['reference', 'ref', 'id', 'number', 'cheque'],
                similarity_threshold=0.7,
                required=False
            ),
            
            # Category column mapping
            ColumnMappingRule(
                target_column=ColumnType.CATEGORY,
                patterns=[
                    r'^category$',
                    r'^type$',
                    r'^classification$'
                ],
                keywords=['category', 'type', 'class', 'group'],
                similarity_threshold=0.7,
                required=False
            ),
            
            # Account column mapping
            ColumnMappingRule(
                target_column=ColumnType.ACCOUNT,
                patterns=[
                    r'^account$',
                    r'^account[_\s]*number$',
                    r'^from[_\s]*account$',
                    r'^to[_\s]*account$'
                ],
                keywords=['account', 'acc', 'from', 'to'],
                similarity_threshold=0.7,
                required=False
            )
        ]
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """
        Pre-compile regex patterns for better performance.
        
        Returns:
            Dictionary of compiled regex patterns
        """
        compiled = {}
        for rule in self._default_rules + self.config.mapping_rules:
            for pattern in rule.patterns:
                if pattern not in compiled:
                    try:
                        compiled[pattern] = re.compile(pattern, re.IGNORECASE)
                    except re.error as e:
                        logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        return compiled
    
    def get_standard_schema(self) -> Dict[str, type]:
        """
        Get the standard schema definition.
        
        Returns:
            Dictionary mapping column types to expected Python types
        """
        return {
            'transaction_date': 'datetime64[ns]',
            'description': 'object',
            'amount': 'float64',
            'balance': 'float64',
            'reference': 'object',
            'category': 'object',
            'sub_category': 'object',
            'account': 'object'
        }
    
    def validate_mappings(self, mappings: Dict[str, str], df: pd.DataFrame) -> List[str]:
        """
        Validate that column mappings are correct and columns exist.
        
        Args:
            mappings: Column mappings to validate
            df: DataFrame to validate against
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check that all mapped columns exist in DataFrame
        for raw_col, standard_col in mappings.items():
            if raw_col not in df.columns:
                errors.append(f"Mapped column '{raw_col}' not found in DataFrame")
        
        # Check for duplicate mappings to same standard column
        standard_cols = list(mappings.values())
        duplicates = [col for col in set(standard_cols) if standard_cols.count(col) > 1]
        for dup in duplicates:
            errors.append(f"Multiple columns mapped to '{dup}'")
        
        # Check that required columns are mapped
        required_types = [rule.target_column for rule in self._get_all_mapping_rules() if rule.required]
        mapped_types = set(mappings.values())
        missing = [req for req in required_types if req not in mapped_types]
        for miss in missing:
            errors.append(f"Required column type '{miss}' not mapped")
        
        return errors