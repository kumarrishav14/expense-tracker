# Data Processor Micro-Architecture

## **Component Overview**

The `data_processor` component serves as the **Data Transformation and Validation Engine** that converts raw parsed bank statement data into standardized pandas DataFrames compatible with `db_interface`. It handles intelligent column mapping, data validation, AI-powered categorization, and ensures data quality before persistence.

## **Position in System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    FILE PARSERS                                 │
│  PDF Parser │ CSV Parser │ Text Parser │ Manual Entry           │
└─────────────┬───────────────────────────────────────────────────┘
              │ Raw Pandas DataFrames (any column names/structure)
┌─────────────▼───────────────────────────────────────────────────┐
│                  DATA_PROCESSOR COMPONENT                       │
│              (Data Transformation Engine)                      │
│  • Intelligent Column Mapping                                  │
│  • Data Validation & Cleaning                                  │
│  • AI-Powered Categorization                                   │
│  • Format Standardization                                      │
└─────────────┬───────────────────────────────────────────────────┘
              │ Standardized DataFrames (db_interface compatible)
┌─────────────▼───────────────────────────────────────────────────┐
│                  DB_INTERFACE COMPONENT                         │
│              (Simple Data Access Layer)                        │
└─────────────────────────────────────────────────────────────────┘
```

## **Core Responsibilities**

### **Primary Responsibilities**

| Responsibility | Description | Input | Output |
|----------------|-------------|-------|--------|
| **Column Mapping** | Intelligent mapping of raw columns to standard schema | Raw DataFrame with any columns | Mapped DataFrame with standard columns |
| **Data Validation** | Business logic validation and data quality checks | Mapped DataFrame | Validated DataFrame + Error Report |
| **AI Categorization** | Category prediction for each transaction | Transaction descriptions | Category assignments with confidence |
| **Data Cleaning** | Format standardization and data normalization | Raw/inconsistent data | Clean, standardized data |
| **Error Handling** | Comprehensive validation error reporting | Invalid data | Detailed error reports for user action |

### **What data_processor Does NOT Handle**

| Responsibility | Owner Component | Rationale |
|----------------|-----------------|-----------|
| **File Parsing** | File Parser Components | Format-specific parsing logic |
| **Database Operations** | db_interface/db_manager | Data persistence responsibility |
| **UI Presentation** | Streamlit Components | User interface concerns |
| **Database Constraints** | db_interface | Database-level validation |

## **Data Flow Architecture**

### **Processing Pipeline**

```
Raw Data Input → Column Mapping → Data Validation → AI Categorization → Format Standardization → Output
      ↓              ↓              ↓                ↓                    ↓
   Any Format → Standard Columns → Clean Data → Categorized Data → db_interface Ready
```

### **Detailed Data Transformation Flow**

```
Step 1: Raw Data Analysis
├─ Analyze column names and data types
├─ Detect data patterns and formats
├─ Identify potential mapping candidates
└─ Generate mapping confidence scores

Step 2: Intelligent Column Mapping
├─ Map amount columns (amount, debit, credit, transaction_amount)
├─ Map date columns (date, transaction_date, posting_date)
├─ Map description columns (description, memo, details, narrative)
├─ Handle missing columns with defaults
└─ Generate mapping report

Step 3: Data Validation & Cleaning
├─ Validate required fields presence
├─ Clean and standardize date formats
├─ Normalize amount values (handle negatives, currency symbols)
├─ Clean description text (remove extra spaces, special chars)
└─ Generate validation error report

Step 4: AI Categorization
├─ Send descriptions to AI backend
├─ Receive category predictions with confidence scores
├─ Handle AI service failures gracefully
├─ Apply fallback categorization rules
└─ Generate categorization report

Step 5: Format Standardization
├─ Apply final data type conversions
├─ Add system timestamps
├─ Generate final DataFrame
└─ Prepare operation result
```

## **Component Architecture**

### **Simplified Class Structure**

```
DataProcessor:
├─ Column Mapping: Simple field mapping with basic patterns
├─ Data Validation: Essential validation and cleaning
├─ AI Integration: Simple row-by-row AI categorization
└─ Processing Pipeline: Straightforward step-by-step processing
```

### **Simplified Public Interface**

```
class DataProcessor:
    """Simple data processing for personal expense tracking"""
    
    # Main Processing Method
    def process_raw_data(
        self, 
        raw_df: pd.DataFrame
    ) -> ProcessingResult
    
    # Helper Methods
    def map_columns(self, raw_df: pd.DataFrame) -> pd.DataFrame
    def validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame
    def add_ai_categories(self, df: pd.DataFrame) -> pd.DataFrame
```

## **Intelligent Column Mapping Strategy**

### **Column Mapping Rules**

```
Standard Schema Target:
├─ amount: float (required)
├─ transaction_date: datetime (required)
├─ description: str (optional)
├─ category: str (optional, from AI)
├─ sub_category: str (optional, from AI)
├─ ai_confidence: float (optional, from AI)
├─ created_at: datetime (system generated)
└─ updated_at: datetime (system generated)

Raw Column Mapping Patterns:
├─ Amount Columns:
│   ├─ Primary: ["amount", "transaction_amount", "value", "sum"]
│   ├─ Debit: ["debit", "debit_amount", "withdrawal", "outgoing"]
│   ├─ Credit: ["credit", "credit_amount", "deposit", "incoming"]
│   └─ Combined: Handle debit/credit combination logic
├─ Date Columns:
│   ├─ Primary: ["date", "transaction_date", "posting_date"]
│   ├─ Secondary: ["value_date", "effective_date", "process_date"]
│   └─ Formats: Auto-detect date formats and time zones
├─ Description Columns:
│   ├─ Primary: ["description", "memo", "details", "narrative"]
│   ├─ Secondary: ["reference", "remarks", "comment", "note"]
│   └─ Combined: Merge multiple description fields if needed
└─ Metadata Columns:
    ├─ Reference: ["ref", "reference_number", "transaction_id"]
    ├─ Balance: ["balance", "running_balance", "account_balance"]
    └─ Ignore: System-specific columns that don't map
```

### **Enhanced Mapping Algorithm**

```
Column Mapping Process:
├─ Step 1: Exact Name Matching
│   └─ Direct match with standard column names
├─ Step 2: Keyword Matching
│   ├─ Look for "amount", "debit", "credit" keywords
│   ├─ Look for "date", "transaction" keywords  
│   └─ Look for "description", "memo" keywords
├─ Step 3: Data Type Check
│   ├─ Numeric columns → potential amount fields
│   ├─ Date columns → potential date fields
│   └─ String columns → potential description fields
├─ Step 4: Field Combination Logic
│   ├─ Detect debit/credit column pairs
│   ├─ Identify multiple description fields
│   ├─ Handle multiple date fields with priority
│   └─ Plan field combination strategy
└─ Step 5: Validation & Mapping
    ├─ Ensure required fields can be created
    ├─ Execute field combination logic
    └─ Return mapping result with success/failure
```

## **Field Combination Architecture**

### **Amount Field Combination Strategy**

```
Amount Field Scenarios:
├─ Single Amount Column:
│   ├─ Direct mapping to 'amount'
│   ├─ Handle signed values (negative = debit, positive = credit)
│   └─ Clean currency symbols and formatting
├─ Separate Debit/Credit Columns:
│   ├─ Combine into single 'amount' column
│   ├─ Debit values → negative amounts
│   ├─ Credit values → positive amounts
│   ├─ Handle rows with both debit and credit (validation error)
│   └─ Handle rows with neither (zero amount or skip)
├─ Multiple Amount Columns:
│   ├─ Priority order: "Amount" > "Transaction Amount" > "Posted Amount"
│   ├─ Use first non-empty value found
│   └─ Log which column was selected
└─ Amount with Direction Column:
    ├─ Combine amount with separate direction indicator
    ├─ Direction values: "DR"/"CR", "Debit"/"Credit", "Out"/"In"
    └─ Apply sign based on direction
```

### **Date Field Combination Strategy**

```
Date Field Scenarios:
├─ Single Date Column:
│   ├─ Direct mapping to 'transaction_date'
│   ├─ Auto-detect and parse date format
│   └─ Validate date reasonableness
├─ Multiple Date Columns:
│   ├─ Priority order: "Transaction Date" > "Posted Date" > "Value Date"
│   ├─ Use first valid date found
│   ├─ Ensure all dates in row are consistent (within reason)
│   └─ Log which date column was selected
├─ Date and Time Columns:
│   ├─ Combine separate date and time columns
│   ├─ Create datetime object
│   └─ Default to date-only if time parsing fails
└─ Date Format Variations:
    ├─ Auto-detect common formats (DD/MM/YYYY, MM-DD-YYYY, etc.)
    ├─ Handle different separators (/, -, .)
    └─ Parse month names (Jan, January, 01)
```

### **Description Field Combination Strategy**

```
Description Field Scenarios:
├─ Single Description Column:
│   ├─ Direct mapping to 'description'
│   ├─ Clean whitespace and formatting
│   └─ Handle empty descriptions gracefully
├─ Multiple Description Columns:
│   ├─ Concatenate with " | " separator
│   ├─ Priority order: "Description" > "Memo" > "Details" > "Reference"
│   ├─ Skip empty fields in concatenation
│   └─ Limit total description length (e.g., 500 chars)
├─ Structured Description Fields:
│   ├─ Merchant + Location → "Merchant | Location"
│   ├─ Reference + Details → "Reference: Details"
│   └─ Custom combination patterns for known formats
└─ No Description Fields:
    ├─ Use reference number if available
    ├─ Use transaction type if available
    └─ Leave empty if no descriptive information
```

## **Data Validation Framework**

### **Simple Validation Rules**

```
Essential Validations:
├─ Required Fields Check:
│   ├─ Amount field is present and numeric
│   ├─ Date field is present and parseable
│   └─ No completely empty rows
├─ Data Cleaning:
│   ├─ Clean amount values (remove currency symbols)
│   ├─ Parse dates to standard format
│   ├─ Clean description text (trim whitespace)
│   └─ Handle missing values appropriately
└─ Basic Quality Check:
    ├─ Amount values are reasonable (not zero, not extreme)
    ├─ Dates are within last 10 years
    └─ Description length is reasonable
```

### **Data Cleaning Operations**

```
Data Cleaning Pipeline:
├─ Amount Field Cleaning:
│   ├─ Remove currency symbols ($, €, ₹, etc.)
│   ├─ Handle negative amount representations
│   ├─ Normalize decimal separators (. vs ,)
│   ├─ Remove thousands separators
│   └─ Convert to standard float format
├─ Date Field Cleaning:
│   ├─ Auto-detect date formats (DD/MM/YYYY, MM-DD-YYYY, etc.)
│   ├─ Handle timezone information
│   ├─ Convert to standard datetime format
│   ├─ Validate date reasonableness
│   └─ Handle partial dates (missing day/month)
├─ Description Field Cleaning:
│   ├─ Trim whitespace and normalize spacing
│   ├─ Remove special characters and encoding artifacts
│   ├─ Standardize text case (title case for consistency)
│   ├─ Handle multi-line descriptions
│   └─ Extract structured information (merchant names, etc.)
└─ General Data Cleaning:
    ├─ Handle null/empty value representations
    ├─ Remove completely empty rows
    ├─ Standardize boolean representations
    ├─ Clean up categorical data
    └─ Apply data type conversions
```

## **Simple AI Integration**

### **Row-by-Row AI Processing**

```
Simple AI Processing:
├─ For each transaction row:
│   ├─ Extract description text
│   ├─ Send to AI backend (one at a time)
│   ├─ Receive category prediction
│   ├─ Add category to DataFrame
│   └─ Continue to next row
├─ Error Handling:
│   ├─ AI service unavailable → leave category empty
│   ├─ AI response invalid → leave category empty
│   └─ Continue processing remaining rows
└─ Simple Result:
    ├─ Add category and ai_confidence columns
    ├─ Leave empty if AI fails
    └─ User can categorize manually later
```

## **Error Handling and Reporting**

### **Error Classification System**

```
Error Types and Handling:
├─ Critical Errors (Stop Processing):
│   ├─ No mappable amount column found
│   ├─ No mappable date column found
│   ├─ All data rows are invalid
│   ├─ Unsupported data format
│   └─ System resource limitations exceeded
├─ Validation Errors (Partial Processing):
│   ├─ Invalid amount values in specific rows
│   ├─ Unparseable dates in specific rows
│   ├─ Data type conversion failures
│   ├─ Business rule violations
│   └─ Duplicate transaction detection
├─ Warning Conditions (Continue with Caution):
│   ├─ Low confidence column mappings
│   ├─ Missing optional fields
│   ├─ AI categorization failures
│   ├─ Data quality concerns
│   └─ Unusual data patterns
└─ Informational Messages (Processing Notes):
    ├─ Successful processing statistics
    ├─ Data transformation summaries
    ├─ AI categorization results
    ├─ Performance metrics
    └─ Recommendations for data improvement
```

### **Result Structures**

```
ProcessingResult:
├─ success: bool
├─ processed_df: pd.DataFrame (standardized format)
├─ total_rows: int
├─ successful_rows: int
├─ failed_rows: int
├─ warnings: List[ProcessingWarning]
├─ errors: List[ProcessingError]
├─ mapping_report: ColumnMappingResult
├─ validation_report: ValidationResult
├─ categorization_report: CategorizationResult
├─ processing_time: float
└─ recommendations: List[str]

ProcessingError:
├─ error_type: str
├─ error_code: str
├─ message: str
├─ row_indices: List[int]
├─ column_name: Optional[str]
├─ suggested_fix: str
└─ severity: str (critical, error, warning, info)

ColumnMappingResult:
├─ mapped_columns: Dict[str, str]
├─ unmapped_columns: List[str]
├─ mapping_confidence: Dict[str, float]
├─ mapping_method: Dict[str, str]
├─ suggestions: List[MappingSuggestion]
└─ requires_user_review: bool
```

## **Configuration and Customization**

### **Configurable Components**

```
Configuration Areas:
├─ Column Mapping Rules:
│   ├─ Custom column name patterns
│   ├─ Bank-specific mapping templates
│   ├─ User-defined mapping overrides
│   └─ Confidence threshold settings
├─ Validation Rules:
│   ├─ Amount range validations
│   ├─ Date range restrictions
│   ├─ Description length limits
│   └─ Custom business rules
├─ AI Integration Settings:
│   ├─ AI backend configuration
│   ├─ Batch size optimization
│   ├─ Confidence thresholds
│   └─ Fallback categorization rules
└─ Processing Behavior:
    ├─ Error handling strategies
    ├─ Performance optimization settings
    ├─ Logging and monitoring levels
    └─ User interaction preferences
```

### **Bank-Specific Templates**

```
Template System:
├─ Pre-configured Mapping Templates:
│   ├─ Major bank statement formats
│   ├─ Credit card statement formats
│   ├─ Digital wallet export formats
│   └─ Investment account formats
├─ Template Selection Logic:
│   ├─ Auto-detect bank format from data patterns
│   ├─ User-selectable template options
│   ├─ Template confidence scoring
│   └─ Fallback to generic mapping
├─ Template Customization:
│   ├─ User can modify existing templates
│   ├─ Create custom templates for specific sources
│   ├─ Save successful mappings as new templates
│   └─ Share templates across processing sessions
└─ Template Management:
    ├─ Template versioning and updates
    ├─ Template validation and testing
    ├─ Template import/export functionality
    └─ Template performance analytics
```

## **Performance and Scalability**

### **Processing Optimization**

```
Performance Strategies:
├─ Data Processing Optimization:
│   ├─ Vectorized pandas operations for large datasets
│   ├─ Efficient memory usage for DataFrame operations
│   ├─ Parallel processing for independent operations
│   └─ Streaming processing for very large files
├─ AI Integration Optimization:
│   ├─ Batch AI requests to minimize API calls
│   ├─ Cache AI predictions for similar descriptions
│   ├─ Asynchronous AI processing where possible
│   └─ Smart batching based on description similarity
├─ Memory Management:
│   ├─ Process large datasets in chunks
│   ├─ Clean up intermediate DataFrames
│   ├─ Optimize data types for memory efficiency
│   └─ Monitor memory usage during processing
└─ Caching Strategies:
    ├─ Cache successful column mappings
    ├─ Cache AI categorization results
    ├─ Cache validation rule results
    └─ Cache processing templates
```

## **Integration Contracts**

### **Input Contract (from File Parsers)**

```
Expected Input:
├─ raw_df: pd.DataFrame with any column structure
├─ source_type: str (pdf, csv, text, manual)
├─ source_metadata: Dict (file info, parsing details)
└─ processing_hints: Optional[Dict] (user guidance)

Input Assumptions:
├─ DataFrame contains transaction-like data
├─ At least one column contains amount information
├─ At least one column contains date information
├─ Data is already parsed from source format
└─ Basic data type inference has been performed
```

### **Output Contract (to db_interface)**

```
Guaranteed Output:
├─ Standardized DataFrame with required columns:
│   ├─ amount: float (required)
│   ├─ transaction_date: datetime (required)
│   ├─ description: str (optional, may be empty)
│   ├─ category: str (optional, from AI)
│   ├─ sub_category: str (optional, from AI)
│   ├─ ai_confidence: float (optional, 0.0-1.0)
│   ├─ created_at: datetime (system timestamp)
│   └─ updated_at: datetime (system timestamp)
├─ Data quality guarantees:
│   ├─ All required fields are present and valid
│   ├─ Data types match db_interface expectations
│   ├─ No null values in required fields
│   ├─ Dates are within reasonable ranges
│   └─ Amounts are valid numeric values
├─ Processing metadata:
│   ├─ Success/failure status
│   ├─ Error details for failed rows
│   ├─ Processing statistics and metrics
│   ├─ AI categorization results
│   └─ Recommendations for user action
```

## **Simple Testing Strategy**

### **Essential Testing Requirements**

```
Basic Test Categories:
├─ Column Mapping Tests:
│   ├─ Exact name matching (amount, date, description)
│   ├─ Keyword matching (debit/credit, transaction_date, memo)
│   ├─ Data type detection (numeric, date, string)
│   └─ Missing required fields handling
├─ Data Validation Tests:
│   ├─ Required field validation (amount, date present)
│   ├─ Data cleaning (currency symbols, date parsing)
│   ├─ Basic quality checks (reasonable amounts, valid dates)
│   └─ Error handling for invalid data
├─ AI Integration Tests:
│   ├─ Successful AI categorization
│   ├─ AI service failure handling (continue processing)
│   ├─ Row-by-row processing validation
│   └─ Empty category handling when AI fails
└─ End-to-End Tests:
    ├─ Complete processing pipeline (raw → standardized)
    ├─ Common bank statement formats
    ├─ Integration with db_interface format
    └─ Error reporting for user feedback
```

## **Future Enhancements**

### **Phase 2 - Advanced Features**

```
Enhanced Intelligence:
├─ Machine learning for improved column mapping
├─ User feedback integration for mapping accuracy
├─ Advanced duplicate detection algorithms
├─ Smart data quality scoring
└─ Predictive data validation

Advanced AI Integration:
├─ Multiple AI backend support
├─ AI model fine-tuning based on user corrections
├─ Context-aware categorization (merchant, amount, date)
├─ Automatic subcategory detection
└─ Spending pattern analysis
```

### **Phase 3 - Enterprise Features**

```
Advanced Processing:
├─ Real-time data processing capabilities
├─ Advanced data reconciliation features
├─ Multi-currency support and conversion
├─ Complex transaction splitting
└─ Advanced fraud detection patterns

Integration Enhancements:
├─ Direct bank API integration
├─ Multiple data source consolidation
├─ Advanced export/import capabilities
├─ Third-party service integrations
└─ Advanced analytics and reporting
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-02  
**Component Phase**: Core Implementation  
**Dependencies**: system_architecture.md, db_interface_micro_architecture.md  
**Integration Points**: File Parsers → data_processor → db_interface