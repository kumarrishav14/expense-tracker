# Personal Expense Tracking Tool - System Architecture

## **System Overview**

A personal expense tracking application that automatically categorizes bank transactions using AI, provides comprehensive expense analysis, and offers an intuitive web-based interface for financial management.

## **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              STREAMLIT FRONTEND                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │  Dashboard  │ │ Statement   │ │  Expense    │ │ AI Chatbot  │ │  Settings   │ │
│  │     Tab     │ │ Input Tab   │ │Analysis Tab │ │     Tab     │ │     Tab     │ │
│  │ ┌─────────┐ │ │             │ │ ┌─────────┐ │ │ ┌─────────┐ │ │             │ │
│  │ │Dashboard│ │ │             │ │ │Analysis │ │ │ │Chatbot  │ │ │             │ │
│  │ │Processor│ │ │             │ │ │Processor│ │ │ │Processor│ │ │             │ │
│  │ └─────────┘ │ │             │ │ └─────────┘ │ │ └─────────┘ │ │             │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │ Raw Pandas DataFrames
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                          DATA INTERFACE LAYER                                   │
│                            (db_interface.py)                                    │
│                     ┌─────────────────────────────────┐                        │
│                     │   Simple Data Access Layer      │                        │
│                     │  • Raw Transaction DataFrames   │                        │
│                     │  • Raw Category DataFrames      │                        │
│                     │  • Basic Filtering Support      │                        │
│                     │  • Data Persistence Operations  │                        │
│                     └─────────────────────────────────┘                        │
└─────┬───────────────────────────────────────────────────────────┬─────────────┘
      │                                                           │
┌─────▼─────────────────────────────┐                ┌───────────▼──────────────┐
│        DATA PROCESSING            │                │      AI BACKEND          │
│         PIPELINE                  │                │    (Ollama Integration)  │
│  ┌─────────────────────────────┐  │                │  ┌─────────────────────┐ │
│  │      File Parser            │  │                │  │  Category Predictor │ │
│  │  • PDF Statement Parser    │  │                │  │  • Transaction     │ │
│  │  • CSV Statement Parser    │  │                │  │    Classification   │ │
│  │  • Text Statement Parser   │  │                │  │  • Pattern Learning │ │
│  └─────────────────────────────┘  │                │  └─────────────────────┘ │
│  ┌─────────────────────────────┐  │                │  ┌─────────────────────┐ │
│  │    Data Processor           │  │                │  │   AI Chatbot        │ │
│  │  • Data Validation          │  │                │  │  • Expense Queries  │ │
│  │  • Data Standardization     │  │                │  │  • Financial Advice │ │
│  │  • Business Rule Engine     │  │                │  │  • Trend Analysis   │ │
│  │  • Duplicate Detection      │  │                │  └─────────────────────┘ │
│  └─────────────────────────────┘  │                └──────────────────────────┘
└───────────────┬───────────────────┘
                │
┌───────────────▼───────────────────┐
│        DATABASE LAYER             │
│      (SQLAlchemy + SQLite)        │
│  ┌─────────────────────────────┐  │
│  │      Database Manager      │  │
│  │  • CRUD Operations          │  │
│  │  • Session Management       │  │
│  │  • Transaction Handling     │  │
│  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │
│  │      Data Models            │  │
│  │  • Transaction Model        │  │
│  │  • Category Model           │  │
│  │  • User Settings Model      │  │
│  └─────────────────────────────┘  │
└───────────────────────────────────┘
```

## **Core Architectural Principles**

### **1. Raw Data Access with Component Processing**
Components get **raw pandas DataFrames** from `db_interface` and handle their own processing:

```
Data Flow Pattern:
Frontend Components ← Raw DataFrames ← db_interface ← Database
        ↓
Component Processors (Dashboard, Analysis, AI)
        ↓
Processed Data for UI Display
```

### **2. Layered Architecture**
- **Presentation Layer**: Streamlit UI components with embedded processors
- **Data Interface Layer**: Simple data access with basic filtering
- **Business Logic Layer**: Component-specific processing and AI integration
- **Persistence Layer**: Database operations and models

### **3. Modular Component Processing**
- Each UI component handles its own business logic and data processing
- `db_interface` provides raw data access only
- Components are independently testable and maintainable
- Clear separation of concerns between data access and processing

## **Component Architecture**

### **Frontend Layer (Streamlit)**

#### **Dashboard Tab**
```
Responsibilities:
├─ Get raw transaction data from db_interface
├─ Process data using Dashboard Processor:
│   ├─ Calculate financial KPIs
│   ├─ Generate transaction summaries
│   ├─ Create category-wise spending analysis
│   ├─ Compute monthly/yearly trends
│   └─ Prepare visualization data
└─ Display processed results in UI

Data Flow:
Raw Transactions → Dashboard Processor → Processed Analytics → UI Display
```

#### **Statement Input Tab**
```
Responsibilities:
├─ File upload interface (PDF, CSV, Text)
├─ Data preview and validation
├─ Manual transaction entry
├─ Bulk import progress tracking
└─ Error handling and user feedback

Data Flow:
User Upload → File Parser → Data Processor → db_interface → Database
                                                    ↓
                                            Updated DataFrames → UI Refresh
```

#### **Expense Analysis Tab**
```
Responsibilities:
├─ Get raw transaction data from db_interface
├─ Process data using Analysis Processor:
│   ├─ Apply advanced filtering and search
│   ├─ Perform custom date range analysis
│   ├─ Generate category-wise breakdowns
│   ├─ Create spending pattern visualizations
│   ├─ Compute trend analysis
│   └─ Prepare export data
└─ Display analysis results in UI

Data Flow:
Raw Transactions → Analysis Processor → Custom Analytics → UI Display
```

#### **AI Chatbot Tab**
```
Responsibilities:
├─ Get raw transaction data from db_interface
├─ Process queries using Chatbot Processor:
│   ├─ Parse natural language expense queries
│   ├─ Generate financial advice and insights
│   ├─ Explain spending patterns
│   ├─ Provide budget recommendations
│   ├─ Perform interactive data exploration
│   └─ Format responses for UI
└─ Display chatbot responses in UI

Data Flow:
User Query + Raw Transactions → Chatbot Processor → AI Analysis → UI Response
```

#### **Settings Tab**
```
Responsibilities:
├─ Get raw category data from db_interface
├─ Category management operations:
│   ├─ Create, update, delete categories
│   ├─ Manage category hierarchy
│   ├─ Bulk category operations
│   └─ Category validation
├─ AI model configuration
├─ Data export/import settings
├─ User preferences management
└─ System maintenance tools

Data Flow:
Raw Categories → Settings Management → Updated Categories → db_interface
```

### **Data Interface Layer (db_interface.py)**

#### **Core Responsibilities**
```
Primary Functions:
├─ Raw data access with basic filtering
├─ DataFrame ↔ Database translation
├─ Data persistence operations
├─ Transaction management
└─ Error handling and recovery

Raw DataFrame Provision:
├─ transactions_df: Raw transaction data
├─ categories_df: Raw category hierarchy
├─ Basic filtering: date range, category, amount
└─ No processing: Components handle their own analysis
```

#### **Data Synchronization Strategy**
```
Update Pattern:
1. Component requests data modification
2. db_interface validates and processes
3. Database updated atomically
4. All cached DataFrames refreshed
5. Dependent components notified
6. UI components re-render with new data
```

### **AI Backend Layer (Ollama Integration)**

#### **Category Predictor Service**
```
Responsibilities:
├─ Transaction description analysis
├─ Category prediction based on patterns
├─ Confidence scoring
├─ Learning from user corrections
└─ Batch processing for imports

Input/Output:
Input: Transaction DataFrames (description, amount, date)
Output: Prediction DataFrames (category, sub_category, confidence)
```

#### **AI Chatbot Service**
```
Responsibilities:
├─ Natural language query processing
├─ Financial data analysis
├─ Insight generation
├─ Recommendation engine
└─ Conversational interface

Data Integration:
├─ Reads from all DataFrames via db_interface
├─ Generates analysis DataFrames
├─ Provides structured responses
└─ Updates AI insights DataFrames
```

### **Data Processing Pipeline**

#### **File Parser**
```
Supported Formats:
├─ PDF bank statements
├─ CSV transaction exports
├─ Delimited text files
└─ Manual entry forms

Output: Raw transaction DataFrames
```

#### **Data Processor**
```
Processing Pipeline:
├─ Data validation and cleaning
├─ Format standardization
├─ Business rule application
├─ Duplicate detection
├─ AI category prediction
└─ Quality assurance

Output: Validated transaction DataFrames
```

### **Database Layer**

#### **Data Models**
```
Transaction Model:
├─ id, description, amount
├─ transaction_date, category_id
├─ ai_confidence, embedding
└─ created_at, updated_at

Category Model:
├─ id, name, parent_id
├─ ai_keywords, user_rules
└─ created_at, updated_at

Settings Model:
├─ user_preferences
├─ ai_configuration
└─ system_settings
```

## **Data Flow Architecture**

### **Primary Data Flows**

#### **1. Statement Import Flow**
```
User Upload → File Parser → Data Processor → AI Categorization → db_interface → Database
                                                                        ↓
Dashboard ← Analysis Tab ← Expense Analysis ← Updated DataFrames ← db_interface
```

#### **2. Manual Transaction Entry**
```
Statement Input Tab → Data Validation → db_interface → Database
                                              ↓
All UI Tabs ← Updated DataFrames ← db_interface
```

#### **3. AI Analysis Flow**
```
User Query → AI Chatbot → Data Analysis → db_interface (read) → Response Generation
                                                ↓
AI Insights DataFrames → Dashboard/Analysis Tabs
```

#### **4. Category Management Flow**
```
Settings Tab → Category CRUD → db_interface → Database
                                     ↓
All Components ← Updated Category DataFrames ← db_interface
```

### **Cross-Component Communication**

All inter-component communication happens through **standardized DataFrame contracts**:

```
DataFrame Contracts:
├─ transactions_df: Standard transaction format
├─ categories_df: Hierarchical category structure
├─ analysis_df: Aggregated financial metrics
├─ predictions_df: AI category predictions
└─ insights_df: AI-generated recommendations
```

## **Technology Stack**

### **Frontend**
- **Streamlit**: Web UI framework
- **Plotly/Altair**: Data visualization
- **Pandas**: Data manipulation

### **Backend**
- **Python**: Core application language
- **SQLAlchemy**: ORM and database abstraction
- **SQLite**: Local database storage
- **Ollama**: Local AI model hosting

### **Data Processing**
- **Pandas**: DataFrame operations
- **PyPDF2/pdfplumber**: PDF parsing
- **python-dateutil**: Date parsing
- **scikit-learn**: Data preprocessing

### **AI/ML**
- **Ollama**: Local LLM hosting
- **Sentence Transformers**: Text embeddings
- **NumPy**: Numerical computations

## **Deployment Architecture**

### **Local Development**
```
Single Machine Deployment:
├─ Streamlit app (localhost:8501)
├─ Ollama service (localhost:11434)
├─ SQLite database (local file)
└─ File storage (local directory)
```

### **Production Considerations**
```
Future Scalability:
├─ Docker containerization
├─ Cloud database migration
├─ API service separation
└─ Multi-user support
```

## **Security Architecture**

### **Data Protection**
```
Security Measures:
├─ Local data storage (no cloud exposure)
├─ File system permissions
├─ Input validation and sanitization
├─ SQL injection prevention
└─ Secure file handling
```

### **AI Model Security**
```
AI Safety:
├─ Local model execution (no data sharing)
├─ Input sanitization for AI queries
├─ Output validation and filtering
└─ Model access controls
```

## **Performance Architecture**

### **Caching Strategy**
```
Multi-Level Caching:
├─ Streamlit session state (UI state)
├─ DataFrame caching (db_interface)
├─ Database query caching (SQLAlchemy)
└─ AI model caching (Ollama)
```

### **Optimization Targets**
```
Performance Goals:
├─ < 2s transaction import (100 rows)
├─ < 1s UI tab switching
├─ < 3s AI category prediction
└─ < 5s complex analysis queries
```

## **Error Handling & Resilience**

### **Error Boundaries**
```
Error Handling Layers:
├─ UI Layer: User-friendly error messages
├─ Data Interface: Transaction rollback
├─ Processing: Data validation errors
├─ AI Backend: Model failure handling
└─ Database: Connection and constraint errors
```

### **Recovery Mechanisms**
```
Failure Recovery:
├─ Automatic retry for transient errors
├─ Graceful degradation for AI failures
├─ Data backup and restore capabilities
└─ Manual intervention interfaces
```

## **Development Guidelines**

### **Component Integration Rules**
1. **All data access** must go through `db_interface`
2. **No direct database access** from UI components
3. **Standardized DataFrame schemas** for all data exchange
4. **Error handling** at every component boundary
5. **Logging and monitoring** for all operations

### **Data Consistency Rules**
1. **Single source of truth**: Database via db_interface
2. **Atomic operations**: All-or-nothing data updates
3. **State synchronization**: Immediate DataFrame updates
4. **Cache invalidation**: Automatic on data changes
5. **Conflict resolution**: Last-write-wins with user notification

## **Future Extensibility**

### **Planned Enhancements**
```
Phase 2 Features:
├─ Multi-user support
├─ Cloud synchronization
├─ Mobile app integration
├─ Advanced AI features
└─ Third-party integrations
```

### **Architecture Evolution**
```
Scalability Path:
├─ Microservices separation
├─ API-first architecture
├─ Event-driven updates
├─ Distributed caching
└─ Cloud-native deployment
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-02  
**Architecture Phase**: Foundation Design  
**Target Implementation**: Personal Expense Tracking MVP