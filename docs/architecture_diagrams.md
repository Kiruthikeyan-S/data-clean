# DataFlow — Architecture & System Diagrams

This document contains the official architectural blueprints for **DataFlow**:
1. **Dual-Ingestion Enterprise Architecture** (From Input to Decision Support)
2. **Business Analytics & Predictive Demand Pipeline**
3. **Physical & Component Deployment Architecture**
4. **Cascading Extraction & Data Quality Verification Flow**

---

## 1. Dual-Ingestion Enterprise Architecture

DataFlow adopts a dual-path ingestion architecture where structured files (CSV, XLSX, JSON) and unstructured documents (PDF, TXT, DOCX, Images, EML) follow specialized preprocessing tracks before converging into a unified dataset for AI modeling and decision support.

```mermaid
flowchart TD
    classDef inputStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef processStyle fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e;
    classDef unifyStyle fill:#fef08a,stroke:#ca8a04,stroke-width:2px,color:#854d0e;
    classDef aiStyle fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e40af;
    classDef decisionStyle fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#15803d;

    subgraph INGESTION["1. Dual Ingestion Track"]
        SD["Structured Data<br/>(CSV, Excel, JSON)"]:::inputStyle
        UD["Unstructured Data<br/>(PDF, TXT, DOCX, Images, EML)"]:::inputStyle
    end

    subgraph PREPROCESSING["2. Specialized Cleaning & Normalization Track"]
        PP["Preprocessing<br/>• Missing Value Imputation<br/>• Exact Duplicate Deduplication<br/>• Type Coercion & Whitespace Strip<br/>• 7 Quality Dimensions Audit"]:::processStyle
        TP["Text Processing<br/>• OCR & Text Stream Extraction<br/>• Unicode NFKC Normalization<br/>• Control Character Stripping<br/>• Delimited Text Table Detection"]:::processStyle
    end

    subgraph EXTRACTION["3. Feature & Schema Extraction"]
        FE["Feature Extraction<br/>• Fast-Path Deterministic Regex (< 5ms)<br/>• Pipe / Tab Delimited Table Parser<br/>• Key-Value & Label Matcher<br/>• Semantic AI Fallback (Groq / LLaMA)"]:::unifyStyle
    end

    subgraph UNIFICATION["4. Unified Data Layer"]
        UDAT["Unified Dataset<br/>• Dynamic Schema Alignment<br/>• Relational Multi-Entity Linking<br/>• Clean Standardized Records"]:::unifyStyle
    end

    subgraph AI_MODELING["5. AI Modeling & Machine Learning"]
        AIM["AI Modeling<br/>• Historical Sales Velocity (Units / Day)<br/>• 30-Day Demand Projection (V × 30)<br/>• 90% Confidence Bounds (z = 1.645)<br/>• Stockout Decay Projection"]:::aiStyle
    end

    subgraph DECISION_SUPPORT["6. Executive Decision Support"]
        DS["Decision Support<br/>• Automated Reorder Action Directives<br/>• Stock Urgency (Critical / Medium / Healthy)<br/>• Total Revenue & Average Transaction Value (ATV)"]:::decisionStyle
    end

    SD --> PP
    UD --> TP
    PP --> FE
    TP --> FE
    FE --> UDAT
    UDAT --> AIM
    AIM --> DS
```

---

## 2. Business Analytics & Predictive Demand Pipeline

How inventory stock levels, sales transactions, and historical velocity convert into automated procurement actions and executive metrics:

```mermaid
flowchart LR
    classDef mathStyle fill:#f1f5f9,stroke:#475569,stroke-width:2px,color:#1e293b;
    classDef calcStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef alertStyle fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#991b1b;
    classDef okStyle fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#15803d;

    TX["Sales History & Transactions"]:::mathStyle --> VEL["Daily Velocity Calculation<br/>V = Units Sold / Observed Days"]:::calcStyle
    VEL --> PRED["Predicted 30-Day Demand<br/>D = V × 30 Days"]:::calcStyle
    PRED --> BOUNDS["90% Confidence Bounds<br/>Lower: D - (1.645 × SE)<br/>Upper: D + (1.645 × SE)"]:::calcStyle
    
    STOCK["Current Warehouse Stock"]:::mathStyle --> COMP{"Stock vs Upper Bound"}
    BOUNDS --> COMP

    COMP -->|Stock < Upper Bound & Days <= 7| CRIT["CRITICAL URGENCY<br/>Reorder: Upper - Stock + 7-Day Safety Stock"]:::alertStyle
    COMP -->|Stock < Upper Bound & Days > 7| MED["MEDIUM ATTENTION<br/>Schedule upcoming purchase order"]:::calcStyle
    COMP -->|Stock >= Upper Bound| HEALTHY["HEALTHY STATUS<br/>Stock covers 30-day forecast horizon"]:::okStyle
```

---

## 3. Physical & Component Deployment Architecture

```mermaid
graph TB
    subgraph Client_Layer ["Presentation Layer (Frontend SPA)"]
        Browser["User Web Browser (Chrome, Edge, Safari)"]
        SPA["React 19 + TypeScript + Vite SPA<br/>(Port: 5173 / 8080)"]
        Inspector["Data Quality & 12 Fundamentals Inspector"]
        OCRView["Form Parser & Document Split-Viewer"]
        AnalyticsView["Business Analytics & Demand Dashboard"]
        TableGrid["Paginated Results Table (25 rows/page)"]
        
        Browser --> SPA
        SPA --> Inspector
        SPA --> OCRView
        SPA --> AnalyticsView
        SPA --> TableGrid
    end

    subgraph Gateway_Layer ["API Gateway & Routing Layer"]
        Uvicorn["Uvicorn ASGI Server (Port: 8080)"]
        FastAPI["FastAPI Web Framework"]
        Router["API Router (/api/process, /api/process-batch, /api/export)"]
        
        SPA -->|HTTP Multipart & JSON| Uvicorn
        Uvicorn --> FastAPI
        FastAPI --> Router
    end

    subgraph Core_Engine ["Processing Engine (Python 3.10 - 3.14)"]
        MasterPipeline["pipeline.py (Master Orchestrator)"]
        FileDetector["utils/file_detector.py (Magic Byte & MIME Sniffer)"]
        TextProcessor["cleaning/text_cleaner.py & extractors/"]
        StructuredProcessor["cleaning/structured_cleaner.py"]
        FieldExtractor["extraction/field_extractor.py (Regex & Pipe Tables)"]
        AIExtractor["extraction/ai_extractor.py (LLM Semantic Parser)"]
        Auditor["cleaning/data_auditor.py (7 Quality Dimensions)"]
        Profiler["quality/data_quality_profiler.py (Vectorized Stats)"]
        Forecaster["analytics/demand_predictor.py (Gaussian Demand Model)"]
        BusinessEngine["analytics/business_analytics.py (Revenue & ATV)"]

        Router --> MasterPipeline
        MasterPipeline --> FileDetector
        MasterPipeline --> TextProcessor
        MasterPipeline --> StructuredProcessor
        MasterPipeline --> FieldExtractor
        FieldExtractor -.->|Complex Fallback| AIExtractor
        MasterPipeline --> Auditor
        MasterPipeline --> Profiler
        MasterPipeline --> Forecaster
        MasterPipeline --> BusinessEngine
    end

    subgraph Cloud_AI ["External Cloud AI Services"]
        Groq["Groq Cloud LLM API (openai/gpt-oss-120b, llama-3.3-70b)"]
        AIExtractor -->|Secure HTTPS| Groq
    end
```

---

## 4. Cascading Extraction & Data Quality Verification Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client
    participant API as FastAPI Gateway
    participant Pipe as Pipeline Orchestrator
    participant Rule as Deterministic Rule Engine
    participant LLM as Groq Cloud AI
    participant Audit as 7-Dimension Auditor
    participant BI as Business Forecaster

    User->>API: Upload File (CSV, TXT, PDF, etc.)
    API->>Pipe: process_file_pipeline()
    Pipe->>Pipe: Detect MIME & Magic Bytes
    alt Structured Input (CSV / Excel / JSON)
        Pipe->>Pipe: Vectorized Type Clean & Deduplicate
    else Unstructured Input (PDF / TXT / Image)
        Pipe->>Pipe: OCR & Unicode Normalization
        Pipe->>Rule: Try Delimited Table / Regex Rules
        alt Rule Matches (>90% confidence)
            Rule-->>Pipe: Extracted Records (< 5ms)
        else Narrative / Free-form Text
            Pipe->>LLM: Semantic Extract (Groq LLaMA)
            LLM-->>Pipe: Extracted JSON Schema
        end
    end
    Pipe->>Audit: Vectorized 7-Dimension Quality Audit
    Audit-->>Pipe: Dimension Scores, Outliers, Issue Logs
    Pipe->>BI: Compute Velocity, Demand & Stockout Alerts
    BI-->>Pipe: Business Metrics & Reorder Recommendations
    Pipe-->>API: ProcessResponse (Structured Data, Audit, BI)
    API-->>User: Render Interactive Dashboard & Reports
```
