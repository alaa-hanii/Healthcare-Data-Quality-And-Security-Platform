# Data Quality Gate System

A 7-layer data pipeline for ingesting, profiling, validating, securing, warehousing, and visualizing data — with a **Streamlit** UI, a **FastAPI** backend, and **Apache Airflow** orchestration.

The UI (`shima.py`) is the single entry point for the whole pipeline. It holds no processing logic of its own — every action (uploading files, running a layer, moving to the next step) is sent as an HTTP request to the FastAPI backend, and the page renders whatever JSON comes back.

---

## 🧱 Pipeline Layers

| # | Layer | What it does |
|---|-------|---------------|
| 01 | **Ingestion** | Reads raw data from uploaded CSVs or a SQL Server instance using Apache Spark |
| 02 | **Profiling** | Runs statistical profiling per table and exports an HTML report (ZIP) |
| 03 | **Data Quality** | Rule-based checks (completeness, uniqueness, referential integrity) via Great Expectations |
| 04 | **Security** | Masks and encrypts sensitive fields with AES-256 (Fernet) |
| 05 | **Data Warehouse (DWH)** | Loads data into a star schema via SSIS (Staging → DWH) |
| 06 | **Power BI** | Displays a live, interactive dashboard connected to the DWH |
| 07 | **Orchestration** | Coordinates and schedules the full pipeline using Apache Airflow |

---

## 📸 Screenshots

![Landing Page](screenshots/landing.jpg)
![Six Layers Overview](screenshots/six-layers.jpg)
![Ingestion Layer](screenshots/ingestion.jpg)
![Profiling Layer](screenshots/profiling.jpg)

*(Add your screenshots to a `screenshots/` folder in the repo with these names, or update the paths above to match your files.)*

---

## ⚙️ Prerequisites

- Python 3.9+ (built/tested on 3.9.25, Anaconda distribution)
- Java JDK 17 (required by PySpark — set `JAVA_HOME`)
- Microsoft SQL Server (Developer or Express) reachable from the machine
- Microsoft ODBC Driver 17/18 for SQL Server
- Git
- Docker Desktop (for the Orchestration/Airflow layer)
- Power BI Desktop (only needed to republish the dashboard)

---

## 🚀 Setup

```bash
# clone the project
git clone https://github.com/USERNAME/data-quality-gate-system.git
cd data-quality-gate-system

# create and activate environment
conda create -n dqgate python=3.9
conda activate dqgate

# install dependencies
pip install -r requirements.txt
```

### Configuration

Before running on a new machine, update:
- `SQL_SERVER_INSTANCE` in `ProcessingLayer/ingestion/spark_loader.py` → your own SQL Server instance name
- The Power BI dashboard URL in `PowerBI.py`
- The `.dtsx` connection managers under `ProcessingLayer/DWH/DWH/` (for SSIS)

---

## ▶️ Running the project

Start each part in order:

```bash
# 1. Start SQL Server and confirm the databases are reachable

# 2. Start Docker + Airflow
docker compose up -d

# 3. Start the FastAPI backend
python -m uvicorn main:app --reload --port 8000

# 4. Start the Streamlit UI
streamlit run shima.py
```

Then open the app in your browser, log in, and run the layers in sequence from the Pipeline Navigator sidebar — or trigger the full pipeline from the Orchestration page.

---

## 🗂️ Project Structure

```
DataCatalogArchitecture/
├── ProcessingLayer/     # Ingestion, DWH (SSIS packages)
├── ServicesLayer/       # Profiling, Data Quality, Security services
├── ApplicationLayer/    # FastAPI backend (main.py)
├── UI/                  # Streamlit app (shima.py)
├── requirements.txt
└── docker-compose.yml
```

---

## 📝 Notes

- The login page is a UI-side check only (no real authentication yet) — hardening it into a proper `/auth/login` endpoint is a recommended next step before production use.
- Encryption keys are kept locally (`Keys/` folder or environment variables) and are **not** committed to source control.
