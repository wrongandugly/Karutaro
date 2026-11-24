#!/usr/bin/env python3
"""Intake — turns a GitHub issue opened from the Karutaro page into a
new want in wants.json. The page form builds the issue body with fixed
lines plus the marker <!-- karutaro:quero -->. No marker, no want."""
import json, os, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
WANTS_FILE = BASE / "wants.json"
JST = timezone(timedelta(hours=9))

body = os.environ.get("ISSUE_BODY") or ""
issue_no = os.environ.get("ISSUE_NUMBER") or ""

if "<!-- karutaro:quero -->" not in body:
    print("no karutaro marker — not a page want, skipping intake")
    raise SystemExit(0)


def field(label):
    m = re.search(rf"^{label}:\s*(.+)$", body, re.M)
    return m.group(1).strip() if m else ""


what = field("O quê")
if not what:
    print("no 'O quê' line — skipping intake")
    raise SystemExit(0)

ceiling_raw = field("Teto (¥)").replace(",", "").replace("¥", "").strip()
ceiling = int(ceiling_raw) if ceiling_raw.isdigit() else None
details = field("Detalhes")
deadline = field("Prazo") or None

wants = []
if WANTS_FILE.exists():
    wants = json.loads(WANTS_FILE.read_text(encoding="utf-8"))
number = max([w.get("number", 0) for w in wants], default=0) + 1
want = {
    "number": number,
    "what": what,
    "ceiling": ceiling,
    "details": details,
    "deadline": deadline,
    "posted_at": datetime.now(JST).isoformat(timespec="seconds"),
    "active": True,
    "via_issue": int(issue_no) if issue_no.isdigit() else None,
}
wants.append(want)
WANTS_FILE.write_text(json.dumps(wants, ensure_ascii=False, indent=1),
                      encoding="utf-8")
print(f"QUERO Nº {number} registered from issue #{issue_no}: {what}")
