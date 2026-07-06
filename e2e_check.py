"""End-to-end persistence verification script."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import time

import requests

BASE = "http://127.0.0.1:8001/api"


def wait_for_server(url: str, timeout: int = 30) -> bool:
    for _ in range(timeout):
        time.sleep(1)
        try:
            if requests.get(url, timeout=2).status_code == 200:
                return True
        except Exception:
            pass
    return False


def verify_live_db_schema() -> None:
    conn = sqlite3.connect("resume_screening.db")
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(screening_results)")
    cols = {row[1] for row in cur.fetchall()}
    conn.close()
    required = {
        "keyword_score", "qualifications_score",
        "matched_keywords", "missing_keywords",
        "matched_qualifications", "missing_qualifications",
        "recommendation", "recommendation_reason",
        "ai_suggestions", "improvements",
    }
    missing = required - cols
    if missing:
        print(f"FAIL: live DB missing columns: {missing}")
        sys.exit(1)
    print("PASS: all Phase 6 columns present in live DB")


env = os.environ.copy()
env["TRANSFORMERS_NO_TF"] = "1"
env["TF_ENABLE_ONEDNN_OPTS"] = "0"

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.main:app",
     "--host", "127.0.0.1", "--port", "8001"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    env=env,
)

try:
    if not wait_for_server(f"{BASE}/health"):
        out = proc.stdout.read().decode(errors="replace")
        print("Server failed to start:\n", out[:800])
        sys.exit(1)

    print("Server ready")

    # --- health ---
    r = requests.get(f"{BASE}/health", timeout=5)
    print("health:", r.status_code, r.json())

    # --- schema check (always) ---
    verify_live_db_schema()

    # --- resumes ---
    resumes = requests.get(f"{BASE}/resumes", timeout=5).json()
    print(f"resumes in DB: {len(resumes)}")

    if not resumes:
        print("No resumes uploaded — skipping live screening E2E (schema verified above)")
        sys.exit(0)

    # --- POST /screening/match ---
    r = requests.post(
        f"{BASE}/screening/match",
        json={
            "job_description": "Python FastAPI developer with SQL and Docker experience",
            "title": "E2E Persistence Test",
            "generate_ai_insights": False,
        },
        timeout=180,
    )
    print(f"POST /screening/match: {r.status_code}")
    if r.status_code != 200:
        print("Error:", r.text[:400])
        sys.exit(1)

    md = r.json()
    print(f"total_candidates: {md.get('total_candidates')}")
    rc = md["rankings"][0] if md.get("rankings") else {}
    print(f"candidate: {rc.get('candidate_name')} | score: {rc.get('match_score')}")
    print(f"recommendation: {rc.get('recommendation')}")
    print(f"screened_at: {rc.get('screened_at')}")
    print(f"keyword_score: {rc.get('keyword_score')}")
    print(f"matched_keywords: {rc.get('matched_keywords')}")

    # --- find job in DB ---
    all_jobs = requests.get(f"{BASE}/jobs", timeout=5).json()
    e2e_job = next((j for j in all_jobs if j.get("title") == "E2E Persistence Test"), None)
    if not e2e_job:
        print("FAIL: E2E job not found in /api/jobs")
        sys.exit(1)
    job_id = e2e_job["id"]
    print(f"job_id in DB: {job_id}")

    # --- GET /screening/rankings/{job_id} ---
    r3 = requests.get(f"{BASE}/screening/rankings/{job_id}", timeout=10)
    print(f"GET /screening/rankings/{job_id}: {r3.status_code}")
    rdata = r3.json()
    print(f"rankings total_candidates: {rdata.get('total_candidates')}")
    if rdata.get("rankings"):
        rc2 = rdata["rankings"][0]
        print(f"PERSISTED score: {rc2.get('match_score')} | recommendation: {rc2.get('recommendation')}")
        print(f"PERSISTED screened_at: {rc2.get('screened_at')}")
        print(f"PERSISTED keyword_score: {rc2.get('keyword_score')}")
        print(f"PERSISTED matched_keywords: {rc2.get('matched_keywords')}")
        print("PASS: GET /screening/rankings returns persisted data")

    # --- upsert test ---
    print("\n=== UPSERT TEST ===")
    requests.post(
        f"{BASE}/screening/match",
        json={
            "job_description": "Python FastAPI developer with SQL and Docker experience",
            "title": "E2E Persistence Test",
            "generate_ai_insights": False,
        },
        timeout=180,
    )
    rdata2 = requests.get(f"{BASE}/screening/rankings/{job_id}", timeout=10).json()
    before = rdata.get("total_candidates")
    after = rdata2.get("total_candidates")
    if before == after:
        print(f"PASS: upsert — row count unchanged after rescore ({before} -> {after})")
    else:
        print(f"FAIL: row count changed ({before} -> {after})")
        sys.exit(1)

finally:
    proc.terminate()
    proc.wait()
    print("Server stopped")
