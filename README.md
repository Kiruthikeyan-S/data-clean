# DataFlow — Clean, Validated Structured Data Application

A modern, minimalist web application for converting structured and unstructured data files into clean, standardized, validated data with export support (JSON, CSV, Excel).

---

## 🛠 Features

- **Supported Formats**:
  - **Structured**: CSV, Excel (`.xlsx`, `.xls`), JSON
  - **Unstructured / Documents**: PDF (native + scanned OCR), Images (`.jpg`, `.jpeg`, `.png`, `.webp`), TXT, DOCX, EML
- **Data Cleansing**: Whitespace stripping, duplicate removal, unicode normalization, control character removal, null standardization (`N/A`, `null`, `None` -> `None`).
- **Data Normalization**: ISO dates (`YYYY-MM-DD`), Title Case names, E.164 phone numbers, syntax-checked emails, numeric currency stripping (`$`, `₹`, `€`, `INR`, `USD`).
- **Entity Extraction**: Rule-based entity extraction for Name, DOB, Dates, Email, Phone, Address, City, Postal Code, ID Numbers, Amount, Organization.
- **Validation**: Pydantic schema validation.
- **Export Options**: Download clean data as JSON, CSV, or Excel (.xlsx).
- **History**: Local browser history of processed files with instant re-inspection and deletion.
- **No AI Cliches**: Clean, functional enterprise data-tool UI.

---

## 🚀 Getting Started

### 1. Launch Unified Application

Run the Python launcher:
```powershell
python run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

### 2. Run in Development Mode

**Backend:**
```powershell
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```powershell
cd frontend
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 📁 Project Structure

```
data clean/
├── backend/
│   ├── cleaning/              # Text cleaner & DataFrame cleaner
│   ├── extractors/            # Image, PDF, TXT, DOCX, Email extractors
│   ├── extraction/            # Rule-based field extractor & schema mapper
│   ├── normalization/         # Normalizers (date, name, phone, email, amount)
│   ├── models/                # Pydantic models & schemas
│   ├── routes/                # FastAPI routes (process, export, health)
│   ├── utils/                 # File detection & classification
│   ├── pipeline.py            # Master processing pipeline
│   ├── main.py                # FastAPI app entrypoint
│   └── test_pipeline.py       # Unit test suite
├── frontend/
│   ├── src/
│   │   ├── components/        # Header, FileUpload, ResultTable, etc.
│   │   ├── pages/             # UploadPage, ProcessingPage, ResultPage, HistoryPage
│   │   ├── services/          # API service client
│   │   └── types/             # TypeScript interfaces
│   └── package.json
├── sample_data/               # Sample test files (CSV, Excel, JSON, TXT, DOCX, EML)
├── run.py                     # Single-command runner
└── README.md
```
