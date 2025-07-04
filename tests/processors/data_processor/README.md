# DataProcessor Test Suite

## Overview
This directory contains a comprehensive test suite for the `DataProcessor` component, designed for aggressive testing with realistic personal banking scenarios.

## Test Structure

### Core Test Files
- **`test_process_raw_data.py`** - Tests for the main `process_raw_data()` method
- **`test_map_columns.py`** - Tests for column mapping functionality
- **`test_validate_and_clean_data.py`** - Tests for data validation and cleaning
- **`test_integration.py`** - Integration tests for the complete processing pipeline
- **`test_error_handling.py`** - Error handling and edge case tests
- **`test_performance.py`** - Performance tests with realistic data volumes
- **`test_real_world_scenarios.py`** - Real-world personal banking scenarios

### Supporting Files
- **`conftest.py`** - Pytest fixtures and test data
- **`test_plan.md`** - Comprehensive test plan (architecturally aligned)
- **`__init__.py`** - Package initialization

## Test Coverage

### Functional Testing
- ✅ All 4 core DataProcessor methods
- ✅ Multiple bank format compatibility (Chase, BofA, Wells Fargo, etc.)
- ✅ Data validation and cleaning
- ✅ Error handling and graceful degradation
- ✅ Integration between components

### Performance Testing
- ✅ Small datasets (50 transactions)
- ✅ Medium datasets (200 transactions) 
- ✅ Large datasets (500+ transactions)
- ✅ Memory usage monitoring
- ✅ Processing time benchmarks

### Real-World Scenarios
- ✅ Monthly bank statements
- ✅ Credit card statements
- ✅ Mixed transaction types
- ✅ International transactions
- ✅ Recurring payments
- ✅ Business expenses
- ✅ Cash transactions
- ✅ Large purchases
- ✅ Refunds and returns

### Edge Cases & Error Handling
- ✅ Invalid data formats
- ✅ Missing required fields
- ✅ Corrupted data
- ✅ Extreme values
- ✅ Unicode characters
- ✅ Memory pressure scenarios
- ✅ Concurrent processing

## Running the Tests

### Run All Tests
```bash
pytest tests/processors/data_processor/ -v
```

### Run Specific Test Categories
```bash
# Core functionality tests
pytest tests/processors/data_processor/test_process_raw_data.py -v
pytest tests/processors/data_processor/test_map_columns.py -v
pytest tests/processors/data_processor/test_validate_and_clean_data.py -v

# Integration tests
pytest tests/processors/data_processor/test_integration.py -v

# Performance tests
pytest tests/processors/data_processor/test_performance.py -v

# Real-world scenarios
pytest tests/processors/data_processor/test_real_world_scenarios.py -v

# Error handling
pytest tests/processors/data_processor/test_error_handling.py -v
```

### Run with Coverage
```bash
pytest tests/processors/data_processor/ --cov=core.processors.data_processor --cov-report=html
```

## Test Data

### Sample Bank Formats
- Chase Bank CSV format
- Bank of America CSV format  
- Wells Fargo CSV format
- Credit card statements
- Manual entry format

### Test Data Sizes
- **Small**: 10-50 transactions (unit testing)
- **Medium**: 50-200 transactions (typical monthly usage)
- **Large**: 200-500 transactions (heavy usage scenarios)
- **Stress**: 500+ transactions (performance testing)

## Success Criteria

### Functional Requirements ✅
- All core processing functions work correctly
- Column mapping handles 5+ major bank formats
- Data validation catches critical data quality issues
- Error handling provides clear, actionable messages

### Performance Requirements ✅
- Process 200 transactions in <2 seconds
- Memory usage scales linearly with data size
- No memory leaks during extended processing

### Quality Requirements ✅
- Comprehensive test coverage for critical paths
- All realistic edge cases handled gracefully
- Robust exception handling
- Clear error messages for personal app users

## Architecture Alignment

This test suite is specifically designed for:
- **Personal expense tracking app** (not enterprise-scale)
- **Simple DataProcessor architecture** (4 core methods)
- **Realistic data volumes** (typically <1000 transactions)
- **Local processing** (no external dependencies for core functionality)

## Test Philosophy

- **Realistic over theoretical** - Tests focus on actual personal banking scenarios
- **Practical over perfect** - Appropriate for personal app scope
- **Comprehensive coverage** - All critical paths and edge cases
- **Performance aware** - Suitable for personal device constraints
- **Error resilient** - Graceful handling of real-world data issues

## Maintenance

- Add new bank formats as test fixtures when encountered
- Update performance benchmarks if requirements change
- Extend real-world scenarios based on user feedback
- Keep test data anonymized and realistic