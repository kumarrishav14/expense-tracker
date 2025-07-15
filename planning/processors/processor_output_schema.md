# Processor Output Schema Contract

**Version**: 1.0
**Date**: 2025-07-15

This document defines the official, standardized output schema that **all** data processors (`RuleBasedDataProcessor`, `AIDataProcessor`, etc.) must produce after their internal processing is complete.

The `@enforce_output_schema` decorator is responsible for guaranteeing that every DataFrame passed to the `db_interface` strictly adheres to this contract.

## Guaranteed Output DataFrame Schema

| Column Name | Data Type | Required | Description |
|---|---|---|---|
| `description` | `str` | Yes | The transaction description. Cannot be null, can be an empty string. |
| `transaction_date` | `datetime64[ns]` | Yes | The date of the transaction. Cannot be NaT (Not a Time). |
| `amount` | `float` | Yes | The transaction amount. Negative for debits, positive for credits. Cannot be NaN. |
| `category` | `str` | No | The assigned primary category. Defaults to a non-null value (e.g., "Other"). |
| `sub_category` | `str` | No | The assigned sub-category. Defaults to a non-null value (e.g., an empty string). |

### Notes:

- **Column Order**: The decorator will enforce this specific column order.
- **Null Values**: No null values (`None`, `NaN`, `NaT`) are permitted in the final output for the specified columns.
- **Extraneous Columns**: Any additional columns generated during processing will be dropped by the decorator.
