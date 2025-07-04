# DataProcessor Test Suite

## Overview
Comprehensive test suite for the simplified DataProcessor implementation following the micro-architecture specification.

## Current Status: AI Backend Disabled

⚠️ **Important**: AI categorization functionality is currently disabled as the AI backend is not yet implemented.

### What's Working
- ✅ Column mapping from raw data to standard schema
- ✅ Data validation and cleaning
- ✅ Error handling and edge cases
- ✅ Integration tests for complete pipeline
- ✅ Basic functionality tests

### What's Disabled (TODO)
- ❌ AI-powered categorization logic
- ❌ Category assignment based on description keywords
- ❌ Sub-category assignment based on amounts
- ❌ Related assertions in integration tests

## Test Files

### Active Test Files
- `conftest.py` - Shared fixtures and test data
- `test_basic_functionality.py` - Core functionality (AI assertions commented)
- `test_map_columns.py` - Column mapping logic (fully active)
- `test_validate_and_clean_data.py` - Data cleaning (fully active)
- `test_integration.py` - End-to-end pipeline (AI assertions commented)
- `test_error_handling.py` - Error conditions (AI assertions commented)

### Disabled Test Files
- `test_add_ai_categories_disabled.py` - AI categorization structure tests only
- `test_add_ai_categories_full.py.disabled` - Full AI tests (renamed, disabled)

## Running Tests

### Run All Active Tests
```bash
cd tests/processors/data_processor
pytest -v
```

### Run Specific Test Categories
```bash
# Column mapping tests (fully functional)
pytest test_map_columns.py -v

# Data validation tests (fully functional)
pytest test_validate_and_clean_data.py -v

# Basic functionality (AI assertions commented)
pytest test_basic_functionality.py -v

# Integration tests (AI assertions commented)
pytest test_integration.py -v

# Error handling (AI assertions commented)
pytest test_error_handling.py -v

# AI structure tests only
pytest test_add_ai_categories_disabled.py -v
```

### Coverage Report
```bash
pytest --cov=core.processors.data_processor --cov-report=html
```

## TODO Comments

All AI-related assertions are marked with:
```python
# TODO: Enable when AI backend is available - <description>
```

Search for these comments to quickly find what needs to be enabled when AI backend is ready.

## Enabling AI Tests

When AI backend becomes available:

1. **Update DataProcessor**: Implement actual AI categorization logic
2. **Uncomment Assertions**: Remove TODO comments and enable assertions
3. **Rename Test File**: `test_add_ai_categories_full.py.disabled` → `test_add_ai_categories.py`
4. **Update Fixtures**: Enable expected categories in `conftest.py`
5. **Run Full Suite**: Verify all tests pass with AI functionality

## Test Coverage

### Current Coverage (AI Disabled)
- **Column Mapping**: 100% ✅
- **Data Validation**: 100% ✅
- **Error Handling**: 100% ✅
- **Basic Functionality**: ~90% (AI assertions disabled)
- **Integration**: ~85% (AI assertions disabled)
- **AI Categorization**: Structure only (~20%)

### Expected Coverage (AI Enabled)
- **Overall Target**: 90%+ line coverage
- **All Components**: 100% when AI backend available

## Test Data

### Available Fixtures
- `standard_raw_data` - Perfect bank statement format
- `variant_column_names_data` - Different naming conventions
- `debit_credit_format_data` - Separate debit/credit columns
- `messy_data` - Mixed valid/invalid data
- `large_dataset` - Performance testing data
- `currency_symbols_data` - Various currency formats
- `duplicate_transactions_data` - Duplicate detection testing
- `edge_case_amounts` - Boundary value testing

### Real-World Test Cases
- Multiple bank statement formats
- Common CSV/Excel structures
- Error recovery scenarios
- Edge cases and boundary conditions

## Maintenance

### When Adding New Tests
1. Follow existing naming conventions
2. Use appropriate fixtures from `conftest.py`
3. Mark AI-dependent assertions with TODO comments
4. Update this README if adding new test categories

### When AI Backend is Ready
1. Search for all `TODO: Enable when AI backend is available` comments
2. Uncomment and update assertions
3. Enable full AI categorization test file
4. Update expected test data in fixtures
5. Verify full test suite passes

---

**Last Updated**: 2025-01-02  
**AI Backend Status**: Not Available  
**Test Framework**: pytest  
**Coverage Target**: 90%+ (when AI enabled)