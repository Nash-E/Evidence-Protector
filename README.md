# Evidence Protector

A forensic log analysis tool that detects temporal gaps in server logs — the most reliable indicator of log tampering. Available as a web app and a command-line tool.

---

## Overview

When a hacker breaks into a system, one of their first actions is to delete log entries that reveal their activity. Removing entries from a continuous log creates a **temporal gap** — a jump in time. Evidence Protector detects these gaps using **Median Absolute Deviation (MAD) z-score** analysis, a statistically robust method that self-calibrates to each log file's natural rhythm.

---

## Features

- **Multi-format log parsing** — Apache/Nginx, HDFS, Syslog, ISO 8601, and more
- **O(1) memory streaming** — processes files of any size line-by-line, never loads the full file into memory
- **MAD z-score gap detection** — self-calibrating baseline, robust to existing irregularities
- **Configurable sensitivity** — tune the detection threshold from 2 (catch everything) to 15 (extreme gaps only)
- **Context-aware severity scoring** — composite 0–100 score using 8 signals:
  - Statistical anomaly (z-score)
  - Absolute gap duration
  - Proportion of total log time
  - Log activity density drop around the gap
  - Time of day (off-hours gaps scored higher)
  - Day of week (weekend gaps scored higher)
  - Position in log (gaps near start/end scored higher)
  - Gap clustering (multiple nearby gaps scored higher)
- **Risk factor tags** — plain-English labels explaining what raised a gap's score (e.g. "Off-hours (night)", "Near log end", "Clustered gaps")
- **Log Integrity Score** — 0–100 score with verdict (Highly Intact / Mostly Intact / Suspicious / Compromised)
- **Visual timeline** — colour-coded gap visualization across the log's full time range
- **Export** — download results as HTML report, CSV, or JSON
- **Config file support** — `config.toml` controls default sensitivity, port, upload folder, and more
- **CLI tool** — run analysis directly from the terminal with `--sensitivity` and `--config` flags

---

## Requirements

- Python 3.11+
- Flask 3.0+

```bash
pip install -r requirements.txt
```

---

## Installation

```bash
git clone https://github.com/Nash-E/Evidence-Protector.git
cd Evidence-Protector
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

---

## Running the Web App

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

1. Upload a log file
2. Adjust the sensitivity slider if needed
3. Click **Analyze**
4. Review flagged gaps, risk factor tags, and the integrity score
5. Export the report as HTML, CSV, or JSON

---

## Running the CLI

```bash
python cli.py <logfile> [--sensitivity 5.0] [--config config.toml]
```

**Examples:**

```bash
# Analyze with default sensitivity (from config.toml)
python cli.py sample_logs/apache_sample.log

# Raise sensitivity to catch more gaps
python cli.py sample_logs/sensitivity_demo.log --sensitivity 3.0

# Use a custom config file
python cli.py /path/to/server.log --config my_settings.toml
```

**Short flags:** `-s` for `--sensitivity`, `-c` for `--config`

---

## Configuration

Copy `config.toml.example` to `config.toml` and edit as needed:

```toml
[analysis]
default_sensitivity = 5.0   # 2 = very sensitive, 15 = extreme only
min_gap_seconds     = 30    # gaps shorter than this are never flagged

[server]
port          = 5000
debug         = false
upload_folder = "uploads"
```

Settings in `config.toml` are loaded at startup. The CLI `--sensitivity` flag always overrides the config file value.

---

## How It Works

1. The log file is read line-by-line (O(1) memory — no full-file load)
2. Timestamps are extracted via format-specific regex
3. Time deltas between consecutive entries are collected
4. The **median** and **MAD** of all deltas are computed
5. Each delta is scored with a modified z-score: `0.6745 × (delta − median) / MAD_scaled`
6. Deltas exceeding the sensitivity threshold are flagged as gaps
7. Each gap receives a composite severity score (0–100) using 8 contextual signals
8. Results are returned as JSON and rendered in the UI or printed to the terminal

---

## Project Structure

```
Evidence-Protector/
├── api/
│   ├── upload.py           # File upload endpoint
│   ├── analyze.py          # Analysis API route
│   └── export.py           # HTML / CSV / JSON export
├── core/
│   ├── detector.py         # Main analysis engine (streaming pass + gap classification)
│   ├── scorer.py           # Composite severity scoring (8 signals)
│   ├── parser.py           # Line-by-line timestamp extraction
│   ├── formats.py          # Log format definitions and auto-detection
│   └── suggestions.py      # Findings text and integrity score
├── sample_logs/            # Example log files for testing
├── static/                 # CSS and JavaScript
├── templates/
│   └── index.html          # Web interface
├── app.py                  # Flask app factory and entry point
├── cli.py                  # Command-line interface
├── config.py               # Loads config.toml and exposes constants
├── config.toml             # User-editable settings (git-ignored)
├── config.toml.example     # Template for config.toml
└── requirements.txt
```

---

## Sample Logs

The `sample_logs/` directory includes ready-to-use test files:

| File | Format | Purpose |
|---|---|---|
| `apache_sample.log` | Apache/Nginx | General testing |
| `hdfs_sample.log` | HDFS | Hadoop-style log testing |
| `syslog_sample.log` | Syslog | Linux system log testing |
| `iso8601_sample.log` | ISO 8601 | Standard timestamp testing |
| `sensitivity_demo.log` | Apache | Demonstrates the sensitivity slider — gaps at z≈4 and z≈6 disappear as threshold increases |

---

## License

This project does not currently specify a license. Please contact the repository owner before using it in production or redistributing it.
