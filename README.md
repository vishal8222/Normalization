# 🗄️ Database Normalizer Tool

A web-based tool that takes raw, denormalized data (CSV, Excel, PDF), uses **real SQL queries internally** to process and normalize it step-by-step through **1NF → 2NF → 3NF**, and exports results as **Excel/PDF reports** with **visualizations**.

## 🚀 Features

- **Multi-format Upload**: CSV, Excel (.xlsx), and PDF file upload with drag & drop
- **Real SQL Processing**: All normalization is done using actual SQL queries (CREATE TABLE, INSERT INTO...SELECT)
- **Step-by-Step Analysis**: Shows violations, explanations, and SQL for each normal form
- **Visual Reports**: ER diagrams, before/after comparison charts
- **Downloadable Exports**: Excel (.xlsx) with 7 styled sheets, PDF with full report, SQL DDL file
- **History & Search**: Full-text search (SQLite FTS5) across past normalization sessions
- **Interactive Swagger Docs**: Auto-generated API documentation at `/docs`

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Internal DB | SQLite (runs actual SQL for normalization) |
| Search | SQLite FTS5 (full-text search) |
| Excel Export | OpenPyXL (styled workbooks) |
| PDF Export | FPDF2 (formatted reports) |
| PDF Input | pdfplumber (table extraction) |
| Frontend | HTML, CSS, JavaScript, Chart.js |

## 📦 Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd db-normalizer

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The server starts at **http://localhost:8000**

## 🎯 How to Use

1. **Upload** your denormalized CSV/Excel/PDF file
2. **Define** the primary key and functional dependencies
3. Click **Normalize** — the tool detects violations and decomposes tables
4. **View** step-by-step results with SQL queries used
5. **Download** Excel report, PDF report, or SQL DDL file

## 📊 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload CSV/Excel/PDF file |
| `POST` | `/api/dependencies` | Define functional dependencies |
| `POST` | `/api/normalize` | Run full normalization |
| `GET` | `/api/export/excel/{id}` | Download Excel report |
| `GET` | `/api/export/pdf/{id}` | Download PDF report |
| `GET` | `/api/export/sql/{id}` | Download SQL file |
| `GET` | `/api/history` | List past sessions |
| `GET` | `/api/search?q=...` | Full-text search |

## 📁 Project Structure

```
db-normalizer/
├── main.py                 # FastAPI app entry point
├── config.py               # Configuration & paths
├── requirements.txt
├── engine/
│   ├── parser.py           # CSV/Excel/PDF parsing
│   ├── dependency.py       # Functional dependency analysis
│   ├── normalizer.py       # Core 1NF/2NF/3NF logic (SQL-based)
│   ├── sql_generator.py    # MySQL/Oracle DDL generation
│   └── sql_logger.py       # SQL query logging
├── export/
│   ├── excel_export.py     # Styled Excel report (OpenPyXL)
│   └── pdf_export.py       # PDF report (FPDF2)
├── db/
│   ├── sqlite_engine.py    # SQLite session management
│   └── fts_search.py       # Full-text search (FTS5)
├── models/
│   └── schemas.py          # Pydantic data models
├── routers/
│   ├── upload.py           # Upload endpoints
│   ├── normalize.py        # Normalization endpoints
│   ├── export.py           # Export endpoints
│   └── history.py          # History & search endpoints
├── visualization/
│   └── er_diagram.py       # ER diagram data generation
├── templates/
│   └── index.html          # Web UI
├── static/
│   ├── css/style.css       # Styling
│   └── js/
│       ├── app.js          # Frontend logic
│       └── er_diagram.js   # SVG ER diagram renderer
└── sample_data/
    └── students.csv        # Sample denormalized data
```

## 🧪 Sample Data

The included `sample_data/students.csv` contains intentional violations:

| Violation | Example |
|---|---|
| **1NF** | `Courses` column has "Math,Science" (not atomic) |
| **2NF** | `Instructors` depends on `Courses`, not the full key |
| **3NF** | `DeptPhone` depends on `Department`, not on `StudentID` |

## 📝 Key Concepts Demonstrated

- **Database Normalization** (1NF, 2NF, 3NF, atomicity, functional dependencies)
- **SQL DDL** (CREATE TABLE, PRIMARY KEY, FOREIGN KEY)
- **REST API Design** (FastAPI with proper request/response models)
- **File Processing** (CSV, Excel, PDF parsing)
- **Full-Text Search** (SQLite FTS5)
- **Report Generation** (styled Excel & PDF exports)

## 📄 License

MIT
