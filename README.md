# Evidence Protector

A Flask-based web application for uploading, analyzing, and exporting log files — designed to detect anomalies and protect the integrity of digital evidence.

---


## Overview

Evidence Protector is a lightweight web tool that helps investigators, analysts, and security professionals detect tampering or anomalies in log files. By applying statistical analysis (MAD z-score) to uploaded logs, it flags suspicious gaps or irregularities that may indicate evidence manipulation.

---

## Features

- **Log Upload** — Upload log files directly through the browser interface.
- **Anomaly Detection** — Automatically flags suspicious time gaps and outliers using Median Absolute Deviation (MAD) z-score analysis.
- **Configurable Sensitivity** — Tune the detection threshold to balance precision and recall.
- **Export Reports** — Download analysis results for documentation or further review.
- **Clean Web UI** — Simple, accessible interface built with HTML, CSS, and JavaScript.

---

## Project Structure

```
Evidence-Protector/
├── api/
│   ├── upload.py       # Handles file upload endpoints
│   ├── analyze.py      # Core analysis API routes
│   └── export.py       # Report export endpoints
├── core/               # Internal analysis logic (parsing, anomaly detection)
├── sample_logs/        # Example log files for testing
├── static/             # CSS and JavaScript assets
├── templates/
│   └── index.html      # Main web interface (Jinja2 template)
├── app.py              # Application factory and entry point
├── config.py           # App-wide configuration constants
├── requirements.txt    # Python dependencies
└── .gitignore
```

---

## Requirements

- Python 3.8+
- Flask 3.0+

Install all dependencies with:

```bash
pip install -r requirements.txt
```

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/Nash-E/Evidence-Protector.git
cd Evidence-Protector
```

2. **Create and activate a virtual environment** 

```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run the application**

```bash
python app.py
```

5. **Open your browser and navigate to:**

```
http://localhost:5000
```

---

## Usage

1. Open the app at `http://localhost:5000`.
2. Upload a log file using the upload interface.
3. The application will parse the log and run anomaly detection.
4. Review flagged entries in the results view.
5. Export the analysis report if needed.

---

## Configuration

Edit `config.py` to adjust application behaviour:

```python
APP_VERSION = '1.0.0'

# Minimum gap (in seconds) between log entries before it is considered for analysis
MIN_GAP_ABSOLUTE_SECONDS = 30

# MAD z-score multiplier — higher values = less sensitive detection
DEFAULT_SENSITIVITY = 5.0
```

| Parameter | Default | Description |

| `MIN_GAP_ABSOLUTE_SECONDS` | `30` | Gaps smaller than this (in seconds) are ignored during analysis |
| `DEFAULT_SENSITIVITY` | `5.0` | MAD z-score threshold; increase to reduce false positives |


---

## How It Works

Evidence Protector parses uploaded log files and extracts timestamps from each entry. It then computes the time gaps between consecutive entries and applies **Median Absolute Deviation (MAD) z-score** analysis to identify statistically unusual gaps.

A gap is flagged as suspicious when:

```
|gap - median(gaps)| / MAD > DEFAULT_SENSITIVITY
```

This approach is robust to outliers compared to standard deviation, making it well-suited for log files that may already contain some irregularities.

---

## Sample Logs

The `sample_logs/` directory contains example log files you can use to test the application right away. Load any of these through the upload interface to see the analysis pipeline in action.


---

## License

This project does not currently specify a license. Please contact the repository owner before using it in production or redistributing it.

---
