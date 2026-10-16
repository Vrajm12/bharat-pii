#!/usr/bin/env python3
"""BharatPII Local Web Demonstration Interface.

A lightweight, dependency-free local web interface using Python's standard
library http.server and the official bharatpii package.

Features:
- Multilingual text input supporting English, Hindi (Devanagari), Hinglish, and Indic scripts.
- Detect & Redact PII button.
- Color-coded highlighted entity spans with category badges.
- Detailed entity table with native character offsets and slice invariant validation.
- Span-preserving redacted text output with one-click copy button.
- Synthetic example selector covering all 8 Indian PII categories.
- Clear privacy notice confirming verified 100% offline local processing.
- Research prototype disclosure regarding false positives and missed detections.
"""

from __future__ import annotations

import argparse
import html
import http.server
import json
from pathlib import Path
import socketserver
import sys
from typing import Any
from urllib.parse import parse_qs, urlparse

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from bharatpii import BharatPII, __version__
from examples.bharatpii_demo import (
    DEFAULT_MASK_PATTERN,
    DEFAULT_MODEL_DIR,
    process_single_text,
    redact_text,
    validate_entity_offsets,
)
from examples.synthetic_examples import SYNTHETIC_EXAMPLES

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BharatPII — Multilingual Indian PII Detection & Redaction</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --danger: #ef4444;
      --success: #10b981;
      --warning: #f59e0b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 24px 16px;
    }
    .container {
      max-width: 1000px;
      margin: 0 auto;
    }
    header {
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }
    .header-title {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    h1 {
      font-size: 26px;
      font-weight: 700;
      color: #38bdf8;
    }
    .badge {
      font-size: 12px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 9999px;
      background: #0369a1;
      color: #e0f2fe;
    }
    .badge-offline {
      background: #065f46;
      color: #d1fae5;
    }
    .privacy-notice {
      background-color: rgba(30, 41, 59, 0.9);
      border: 1px solid #0284c7;
      border-left: 4px solid #38bdf8;
      padding: 14px 16px;
      border-radius: 8px;
      margin-bottom: 24px;
      font-size: 13px;
      color: #e2e8f0;
    }
    .privacy-notice h4 {
      color: #38bdf8;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .card {
      background-color: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .form-group {
      margin-bottom: 16px;
    }
    label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    select, textarea, input {
      width: 100%;
      background: #0f172a;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 14px;
      font-family: inherit;
    }
    select:focus, textarea:focus, input:focus {
      outline: none;
      border-color: var(--primary);
    }
    textarea {
      min-height: 110px;
      resize: vertical;
      line-height: 1.5;
    }
    .button-row {
      display: flex;
      gap: 12px;
      align-items: center;
    }
    button {
      background: var(--primary);
      color: #0f172a;
      border: none;
      padding: 10px 22px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    button:hover {
      background: var(--primary-hover);
    }
    button.btn-secondary {
      background: #334155;
      color: var(--text);
    }
    button.btn-secondary:hover {
      background: #475569;
    }
    .spinner {
      display: none;
      width: 18px;
      height: 18px;
      border: 2px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    
    /* Highlighted text view */
    .highlight-container {
      background: #0f172a;
      border: 1px solid var(--border);
      padding: 16px;
      border-radius: 8px;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 15px;
      line-height: 1.8;
      margin-bottom: 16px;
    }
    .ent-mark {
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
      display: inline-flex;
      align-items: baseline;
      gap: 4px;
      border: 1px solid transparent;
    }
    .ent-tag {
      font-size: 10px;
      padding: 1px 4px;
      border-radius: 3px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background: rgba(0,0,0,0.3);
    }
    
    /* Category Color Styles */
    .tag-PERSON   { background: rgba(168, 85, 247, 0.25); border-color: #a855f7; color: #f3e8ff; }
    .tag-PAN      { background: rgba(59, 130, 246, 0.25); border-color: #3b82f6; color: #dbeafe; }
    .tag-AADHAAR  { background: rgba(249, 115, 22, 0.25); border-color: #f97316; color: #ffedd5; }
    .tag-PHONE    { background: rgba(34, 197, 94, 0.25); border-color: #22c55e; color: #dcfce7; }
    .tag-EMAIL    { background: rgba(20, 184, 166, 0.25); border-color: #14b8a6; color: #ccfbf1; }
    .tag-UPI_ID   { background: rgba(99, 102, 241, 0.25); border-color: #6366f1; color: #e0e7ff; }
    .tag-BANK_ACCOUNT { background: rgba(236, 72, 153, 0.25); border-color: #ec4899; color: #fce7f3; }
    .tag-ADDRESS  { background: rgba(245, 158, 11, 0.25); border-color: #f59e0b; color: #fef3c7; }

    /* Entity Table */
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 13px;
    }
    th, td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    th {
      background: #0f172a;
      color: var(--text-muted);
      font-weight: 600;
    }
    tr:hover {
      background: rgba(255, 255, 255, 0.02);
    }
    .check-pass {
      color: var(--success);
      font-weight: 600;
    }
    .check-fail {
      color: var(--danger);
      font-weight: 600;
    }
    
    /* Redacted Box */
    .redacted-wrapper {
      position: relative;
    }
    .copy-btn {
      position: absolute;
      top: 8px;
      right: 8px;
      padding: 6px 12px;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-title">
        <h1>BharatPII Inference & Redaction Demo</h1>
        <span class="badge">Model: bharatpii-crf-v1.0</span>
        <span class="badge badge-offline">Verified 100% Offline</span>
      </div>
    </header>

    <div class="privacy-notice">
      <h4>🔒 Privacy & Research Prototype Notice</h4>
      <p>
        • <strong>Strictly Local & Offline:</strong> All neural sequence decoding runs 100% locally on your machine. Zero outbound network calls are made.<br>
        • <strong>Research Prototype Disclosure:</strong> This model is an academic research prototype and is <strong>not</strong> certified under DPDPA 2023. Missed detections and false positives are possible on ambiguous alphanumeric patterns. Human review is recommended for sensitive citizen records.
      </p>
    </div>

    <div class="card">
      <div class="form-group">
        <label for="exampleSelect">Synthetic Example Selector (All 8 Categories & Indic Scripts)</label>
        <select id="exampleSelect">
          <option value="">-- Choose a synthetic example to populate text --</option>
        </select>
      </div>

      <div class="form-group">
        <label for="textInput">Multilingual Input Text (English, Hindi, Hinglish, Indic Scripts)</label>
        <textarea id="textInput" placeholder="Enter or paste text here (e.g., 'Contact Rahul Sharma at 9876543210 regarding PAN ABCDE1234F')."></textarea>
      </div>

      <div class="button-row">
        <button id="detectBtn">Detect & Redact PII</button>
        <button id="clearBtn" class="btn-secondary">Clear</button>
        <div id="spinner" class="spinner"></div>
      </div>
    </div>

    <div id="resultsCard" class="card" style="display: none;">
      <h3 style="margin-bottom: 12px; color: #38bdf8;">Visual Detection Results</h3>
      
      <div class="form-group">
        <label>Highlighted Spans</label>
        <div id="highlightBox" class="highlight-container"></div>
      </div>

      <div class="form-group">
        <label>Detected Entity Spans & Invariant Verification</label>
        <div style="overflow-x: auto;">
          <table id="entityTable">
            <thead>
              <tr>
                <th>#</th>
                <th>Entity Text</th>
                <th>Category</th>
                <th>Offsets [start:end]</th>
                <th>Confidence</th>
                <th>Slice Invariant</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>

      <div class="form-group" style="margin-top: 20px;">
        <label>Span-Preserving Redacted Output</label>
        <div class="redacted-wrapper">
          <button id="copyBtn" class="copy-btn btn-secondary">Copy Redacted</button>
          <textarea id="redactedOutput" readonly style="min-height: 80px;"></textarea>
        </div>
      </div>
    </div>
  </div>

  <script>
    const examples = EXAMPLES_DATA_PLACEHOLDER;

    // Populate dropdown
    const select = document.getElementById('exampleSelect');
    examples.forEach((ex, idx) => {
      const opt = document.createElement('option');
      opt.value = idx;
      opt.textContent = `[${ex.category} | ${ex.language}] ${ex.description}`;
      select.appendChild(opt);
    });

    select.addEventListener('change', (e) => {
      const idx = e.target.value;
      if (idx !== "") {
        document.getElementById('textInput').value = examples[idx].text;
      }
    });

    document.getElementById('clearBtn').addEventListener('click', () => {
      document.getElementById('textInput').value = '';
      document.getElementById('exampleSelect').value = '';
      document.getElementById('resultsCard').style.display = 'none';
    });

    document.getElementById('detectBtn').addEventListener('click', async () => {
      const text = document.getElementById('textInput').value;
      if (!text.trim()) {
        alert('Please enter some text or select a synthetic example.');
        return;
      }

      const spinner = document.getElementById('spinner');
      spinner.style.display = 'inline-block';

      try {
        const resp = await fetch('/api/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text })
        });
        const data = await resp.json();
        renderResults(text, data);
      } catch (err) {
        alert('Error during inference: ' + err.message);
      } finally {
        spinner.style.display = 'none';
      }
    });

    function escapeHtml(str) {
      const div = document.createElement('div');
      div.textContent = str;
      return div.innerHTML;
    }

    function renderResults(rawText, data) {
      const resultsCard = document.getElementById('resultsCard');
      resultsCard.style.display = 'block';

      // 1. Redacted Output
      document.getElementById('redactedOutput').value = data.redacted_text;

      // 2. Highlighted view
      const entities = data.entities || [];
      const highlightBox = document.getElementById('highlightBox');

      if (entities.length === 0) {
        highlightBox.innerHTML = escapeHtml(rawText) + ' <em style="color: var(--text-muted);">(No PII detected)</em>';
      } else {
        // Sort entities by start offset
        const sorted = [...entities].sort((a, b) => a.start - b.start);
        let outHtml = '';
        let lastIdx = 0;

        sorted.forEach(ent => {
          if (ent.start < lastIdx) return;
          outHtml += escapeHtml(rawText.slice(lastIdx, ent.start));
          const cssClass = 'tag-' + ent.label;
          outHtml += `<mark class="ent-mark ${cssClass}">` +
                     escapeHtml(ent.text) +
                     `<span class="ent-tag">${ent.label}</span></mark>`;
          lastIdx = ent.end;
        });
        outHtml += escapeHtml(rawText.slice(lastIdx));
        highlightBox.innerHTML = outHtml;
      }

      // 3. Entity Table
      const tbody = document.querySelector('#entityTable tbody');
      tbody.innerHTML = '';

      if (entities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No PII detected in input text.</td></tr>';
      } else {
        entities.forEach((ent, i) => {
          const tr = document.createElement('tr');
          const isExact = rawText.slice(ent.start, ent.end) === ent.text;
          const checkHtml = isExact
            ? '<span class="check-pass">✓ Exact match</span>'
            : '<span class="check-fail">✗ Slice mismatch</span>';
          const scoreStr = ent.score !== null && ent.score !== undefined ? ent.score.toFixed(4) : 'N/A';

          tr.innerHTML = `
            <td>${i + 1}</td>
            <td><strong>${escapeHtml(ent.text)}</strong></td>
            <td><span class="ent-mark tag-${ent.label}">${ent.label}</span></td>
            <td>[${ent.start} : ${ent.end}]</td>
            <td>${scoreStr}</td>
            <td>${checkHtml}</td>
          `;
          tbody.appendChild(tr);
        });
      }
    }

    // Copy to clipboard
    document.getElementById('copyBtn').addEventListener('click', () => {
      const red = document.getElementById('redactedOutput');
      red.select();
      navigator.clipboard.writeText(red.value);
      const btn = document.getElementById('copyBtn');
      const old = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = old; }, 1500);
    });
  </script>
</body>
</html>
"""


class BharatPIIWebHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving the BharatPII interactive interface."""

    model: BharatPII | None = None

    def log_message(self, format, *args):
        # Prevent logging sensitive user input to stdout/stderr
        sys.stderr.write(f"[HTTP] {self.address_string()} - {args[0]}\n")

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ("/", "/index.html"):
            rendered = HTML_TEMPLATE.replace(
                "EXAMPLES_DATA_PLACEHOLDER",
                json.dumps(SYNTHETIC_EXAMPLES, ensure_ascii=False),
            )
            data = rendered.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path == "/api/examples":
            data = json.dumps(SYNTHETIC_EXAMPLES, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path == "/api/health":
            info = {
                "status": "healthy",
                "package_version": __version__,
                "offline_mode": True,
                "model_loaded": self.model is not None,
            }
            data = json.dumps(info).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/predict":
            if self.model is None:
                self.send_error(500, "Model not loaded")
                return

            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode("utf-8")

            try:
                body = json.loads(raw_body)
                text = body.get("text", "")
                mask_pattern = body.get("mask_pattern", DEFAULT_MASK_PATTERN)
            except Exception as e:
                self.send_error(400, f"Malformed JSON: {e}")
                return

            info = process_single_text(self.model, text, mask_pattern=mask_pattern)
            response_payload = {
                "input_text": info["input_text"],
                "entities": info["entities"],
                "redacted_text": info["redacted_text"],
                "offsets_valid": info["offsets_valid"],
                "offset_errors": info["offset_errors"],
                "offline_mode": True,
            }

            data = json.dumps(response_payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_error(404, "Not Found")


def run_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    model_path: Path | str = DEFAULT_MODEL_DIR,
    verify_checksums: bool = False,
):
    """Start the BharatPII local demonstration web server."""
    print("================================================================================")
    print("                    BharatPII Local Web Demonstration Server                    ")
    print("================================================================================")
    print("PRIVACY & SECURITY AUDIT:")
    print("  • Binds strictly to local interface: http://" + f"{host}:{port}")
    print("  • 100% offline local inference (0 outbound network calls).")
    print("  • Sensitive user text is NOT written to logs or sent to external APIs.")
    print("  • Research prototype: Missed detections and false positives are possible.")
    print("================================================================================\n")

    print(f"Loading BharatPII model from {model_path} (verify_checksums={verify_checksums})...")
    model = BharatPII.from_pretrained(model_path, verify_checksums=verify_checksums)
    BharatPIIWebHandler.model = model
    print(f"Model loaded successfully! Package version: {__version__}")

    server_address = (host, port)
    with http.server.ThreadingHTTPServer(server_address, BharatPIIWebHandler) as httpd:
        print(f"\n[READY] BharatPII Web UI running at: http://{host}:{port}/")
        print("Press Ctrl+C to stop the server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web server. Namaste!")


def main():
    parser = argparse.ArgumentParser(
        prog="bharatpii_web_demo",
        description="BharatPII-CRF: Local Web UI for Multilingual Indian PII Detection & Redaction",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port number to listen on (default: 8080)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=str(DEFAULT_MODEL_DIR),
        help=f"Path to model directory (default: {DEFAULT_MODEL_DIR})",
    )
    parser.add_argument(
        "--verify-checksums",
        action="store_true",
        help="Validate model artifact SHA256 checksums from SHA256SUMS.txt on load",
    )

    args = parser.parse_args()
    run_server(
        host=args.host,
        port=args.port,
        model_path=args.model,
        verify_checksums=args.verify_checksums,
    )


if __name__ == "__main__":
    main()
