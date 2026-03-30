"""
Evidence Protector — CLI
Usage:
    python cli.py <logfile> [--sensitivity 5.0]

Examples:
    python cli.py sample_logs/sensitivity_demo.log
    python cli.py sample_logs/apache_sample.log --sensitivity 3.0
    python cli.py /path/to/server.log --sensitivity 8.0
"""

import argparse
import sys
import os

# Allow imports from the web app's core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.detector import run_analysis
from config import DEFAULT_SENSITIVITY


def fmt_line(char, width=60):
    print(char * width)


def run_cli(filepath, sensitivity):
    if not os.path.isfile(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    print()
    fmt_line("=")
    print("  EVIDENCE PROTECTOR - Log Forensic Analysis")
    fmt_line("=")
    print(f"  File       : {os.path.basename(filepath)}")
    print(f"  Size       : {os.path.getsize(filepath) / 1024:.1f} KB")
    print(f"  Sensitivity: {sensitivity} (MAD z-score threshold)")
    fmt_line("-")

    print("  Analyzing... ", end="", flush=True)
    result = run_analysis(filepath, sensitivity=sensitivity)
    print("Done.\n")

    meta       = result.get("metadata", {})
    assessment = result.get("assessment", {})
    gaps       = result.get("gaps", [])

    # ── Summary ─────────────────────────────────────────────────
    fmt_line("=")
    print("  SUMMARY")
    fmt_line("-")
    print(f"  Format detected    : {result.get('format_detected', 'Unknown')}")
    print(f"  Total lines        : {meta.get('total_lines', 0):,}")
    print(f"  Valid lines        : {meta.get('valid_lines', 0):,}")
    print(f"  Malformed lines    : {meta.get('malformed_count', 0):,}")
    print(f"  Out-of-order lines : {meta.get('out_of_order_count', 0):,}")
    print(f"  Log duration       : {assessment.get('gap_time_human', 'N/A')}")
    print(f"  First timestamp    : {meta.get('first_timestamp', 'N/A')}")
    print(f"  Last timestamp     : {meta.get('last_timestamp', 'N/A')}")
    print(f"  Processing time    : {meta.get('processing_time_ms', 0)} ms")

    mad = meta.get("mad_stats", {})
    if mad:
        print(f"  Median interval    : {mad.get('median_interval', 0):.2f}s")
        print(f"  MAD scaled         : {mad.get('mad_scaled', 0):.3f}s")

    # ── Integrity Score ─────────────────────────────────────────
    fmt_line("=")
    print("  LOG INTEGRITY SCORE")
    fmt_line("-")
    score   = assessment.get("integrity_score", 100)
    verdict = assessment.get("verdict", "UNKNOWN")
    bar_len = int(score / 2)
    bar     = "#" * bar_len + "-" * (50 - bar_len)
    print(f"  Score  : {score}%")
    print(f"  Verdict: {verdict}")
    print(f"  [{bar}]")

    counts = assessment.get("severity_counts", {})
    print(f"\n  CRITICAL : {counts.get('CRITICAL', 0)}")
    print(f"  HIGH     : {counts.get('HIGH', 0)}")
    print(f"  MEDIUM   : {counts.get('MEDIUM', 0)}")
    print(f"  LOW      : {counts.get('LOW', 0)}")

    # ── Findings ────────────────────────────────────────────────
    findings = assessment.get("findings", [])
    if findings:
        fmt_line("=")
        print("  FINDINGS")
        fmt_line("-")
        for f in findings:
            print(f"  * {f}")

    # ── Gap Details ─────────────────────────────────────────────
    fmt_line("=")
    print(f"  GAPS DETECTED ({len(gaps)} total, sorted by severity)")
    fmt_line("=")

    if not gaps:
        print("  No suspicious gaps found at this sensitivity level.")
    else:
        for g in gaps:
            sev   = g.get("severity_label", "?")
            score = g.get("severity_score", 0)
            dur   = g.get("duration_human", "?")
            start = g.get("start_time", "?").replace("T", " ")
            end   = g.get("end_time", "?").replace("T", " ")
            sl    = g.get("start_line", "?")
            el    = g.get("end_line", "?")
            z     = g.get("modified_z_score", 0)

            fmt_line("-")
            print(f"  GAP #{g.get('id')}  |  {sev}  |  Score: {score}/100")
            print(f"  Duration   : {dur}")
            print(f"  From       : {start}  (line {sl})")
            print(f"  To         : {end}  (line {el})")
            print(f"  Z-score    : {z}")

    fmt_line("=")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evidence Protector — forensic log gap analysis"
    )
    parser.add_argument("logfile", help="Path to the log file to analyze")
    parser.add_argument(
        "--sensitivity", "-s",
        type=float,
        default=DEFAULT_SENSITIVITY,
        help=f"MAD z-score threshold (default: {DEFAULT_SENSITIVITY}). "
             "Lower = flag more gaps. Higher = only extreme gaps."
    )
    args = parser.parse_args()
    run_cli(args.logfile, args.sensitivity)
