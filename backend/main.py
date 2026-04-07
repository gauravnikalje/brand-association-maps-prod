"""
AntiGravity BAM — FastAPI Backend
Railway-native: PostgreSQL via SQLAlchemy, in-memory pipeline, public API (no auth).
"""

import io
import os
import sys
import uuid
import time
import logging
import json
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from dotenv import load_dotenv

# ── Path bootstrap so src.* modules are importable ──────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.config_loader import load_config
from src.cleaner import clean_messages, lemmatize_messages
from src.bigrams import generate_bigrams
from src.taxonomy import load_taxonomies, map_taxonomy
from src.sentiment import map_sentiment
from src.association import compute_association, aggregate_and_score
from src.output_writer import write_output

# ── DB Setup ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
engine = None
if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
        logging.info("PostgreSQL connected via SQLAlchemy.")
    except Exception as e:
        logging.warning(f"DB connection failed: {e}. Running in stateless mode.")

def get_db():
    if engine is None:
        return None
    return engine.connect()

def db_insert_run(run_id: str, client_name: str, brand: str, status: str = "pending"):
    if engine is None:
        return
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_runs (id, status, created_at)
            VALUES (:id, :status, :created_at)
            ON CONFLICT DO NOTHING
        """), {"id": run_id, "status": status, "created_at": datetime.now(timezone.utc)})

def db_update_run(run_id: str, status: str, total_messages: int = None,
                  total_bigrams: int = None, tagged_pct: float = None,
                  duration: float = None, error: str = None):
    if engine is None:
        return
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE pipeline_runs
            SET status=:status,
                total_messages=:total_messages,
                total_bigrams=:total_bigrams,
                tagged_pct=:tagged_pct,
                run_duration_sec=:duration,
                error_message=:error,
                completed_at=:completed_at
            WHERE id=:id
        """), {
            "id": run_id, "status": status,
            "total_messages": total_messages, "total_bigrams": total_bigrams,
            "tagged_pct": tagged_pct, "duration": duration,
            "error": error, "completed_at": datetime.now(timezone.utc)
        })

def db_insert_results(run_id: str, df: pd.DataFrame, level: str, t1_col: str=None,
                      t2_col: str=None, t3_col: str=None, t4_col: str=None):
    if engine is None or df.empty:
        return
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "level": level,
            "attribute_t1": row.get(t1_col) if t1_col else None,
            "attribute_t2": row.get(t2_col) if t2_col else None,
            "attribute_t3": row.get(t3_col) if t3_col else None,
            "attribute_t4": row.get(t4_col) if t4_col else None,
            "word1": row.get("word1"),
            "word2": row.get("word2"),
            "mentions": int(row.get("n", 0) or 0),
            "positive": int(row.get("Positive", 0) or 0),
            "negative": int(row.get("Negative", 0) or 0),
            "total": int(row.get("Total", 0) or 0),
            "positive_pct": float(row.get("Positive_perc", 0) or 0),
            "negative_pct": float(row.get("Negative_perc", 0) or 0),
            "mentions_assoc": row.get("Mentions_association"),
            "sentiment_assoc": row.get("Sentiment_association"),
            "overall_assoc": row.get("Association"),
        })
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO results_data (id, run_id, level, attribute_t1, attribute_t2,
                attribute_t3, attribute_t4, word1, word2, mentions, positive, negative,
                total, positive_pct, negative_pct, mentions_assoc, sentiment_assoc, overall_assoc)
            VALUES (:id, :run_id, :level, :attribute_t1, :attribute_t2, :attribute_t3,
                :attribute_t4, :word1, :word2, :mentions, :positive, :negative, :total,
                :positive_pct, :negative_pct, :mentions_assoc, :sentiment_assoc, :overall_assoc)
        """), rows)

# ── In-memory pipeline runner ─────────────────────────────────────────────────
CONFIG_PATH = os.path.join(ROOT, "config", "jlr.json")
DATA_DIR    = os.path.join(ROOT, "Brand Association Maps")

def run_pipeline_inmemory(file_bytes: bytes, filename: str, run_id: str):
    """Full BAM pipeline executed in memory, results persisted to DB."""
    t_start = time.time()
    db_insert_run(run_id, "JLR", "Jaguar", status="running")

    try:
        config = load_config(CONFIG_PATH)

        # Read uploaded file
        source_df = pd.read_excel(io.BytesIO(file_bytes))
        total_messages = len(source_df)

        cleaned_df  = clean_messages(source_df, config)
        lemmatized  = lemmatize_messages(cleaned_df["Message"])
        bigram_counts = generate_bigrams(lemmatized, config)
        total_bigrams = len(bigram_counts)

        bigram_tax, mono_tax = load_taxonomies(config, DATA_DIR)
        tagged_df, untagged_df = map_taxonomy(bigram_counts, bigram_tax, mono_tax)
        tagged_pct = round(len(tagged_df) / total_bigrams * 100, 1) if total_bigrams else 0

        sentiment_mapped = map_sentiment(cleaned_df, tagged_df)
        word_level = compute_association(sentiment_mapped, mention_col="Total")

        t4 = aggregate_and_score(sentiment_mapped, ["Attribute - T1","Attribute - T2","Attribute - T3","Attribute - T4"])
        t3 = aggregate_and_score(sentiment_mapped, ["Attribute - T1","Attribute - T2","Attribute - T3"])
        t2 = aggregate_and_score(sentiment_mapped, ["Attribute - T1","Attribute - T2"])

        # Persist results to DB
        db_insert_results(run_id, word_level, "word", t1_col="Attribute - T1", t2_col="Attribute - T2")
        db_insert_results(run_id, t2, "t2", t1_col="Attribute - T1", t2_col="Attribute - T2")
        db_insert_results(run_id, t3, "t3", t1_col="Attribute - T1", t2_col="Attribute - T2", t3_col="Attribute - T3")
        db_insert_results(run_id, t4, "t4", t1_col="Attribute - T1", t2_col="Attribute - T2", t3_col="Attribute - T3", t4_col="Attribute - T4")

        duration = round(time.time() - t_start, 2)
        db_update_run(run_id, "completed", total_messages=total_messages,
                      total_bigrams=total_bigrams, tagged_pct=tagged_pct, duration=duration)

        # Return Excel bytes for immediate download
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
            for name, df in [("word_level", word_level), ("t2", t2), ("t3", t3), ("t4", t4), ("untagged", untagged_df)]:
                if df is not None and not df.empty:
                    df.to_excel(writer, sheet_name=name, index=False)
        excel_buf.seek(0)

        # Summary for API response
        assoc_dist = {}
        if not word_level.empty and "Association" in word_level.columns:
            assoc_dist = word_level["Association"].value_counts().to_dict()

        pos_pct = round(float(word_level["Positive_perc"].mean()), 1) if not word_level.empty and "Positive_perc" in word_level.columns else 0.0

        return {
            "run_id": run_id,
            "status": "completed",
            "summary": {
                "total_messages": total_messages,
                "total_bigrams": total_bigrams,
                "tagged_pct": tagged_pct,
                "positive_pct": pos_pct,
                "duration_sec": duration,
                "association_distribution": assoc_dist,
            },
            "word_level": word_level.head(100).fillna("").to_dict(orient="records"),
            "t2": t2.fillna("").to_dict(orient="records") if not t2.empty else [],
            "excel_bytes": excel_buf.read(),
        }

    except Exception as e:
        logging.exception("Pipeline failed")
        db_update_run(run_id, "failed", error=str(e))
        raise

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="AntiGravity BAM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for latest results per run_id (ephemeral, lives as long as the process)
_results_cache: dict = {}

@app.get("/")
def root():
    return {"message": "AntiGravity BAM Backend — Online.", "version": "1.0.0"}

@app.get("/health")
def health():
    db_ok = engine is not None
    return {"status": "ok", "database": "connected" if db_ok else "stateless"}

@app.post("/api/run-pipeline")
async def run_pipeline_endpoint(file: UploadFile = File(...)):
    """
    Accept an xlsx file upload, run the full BAM pipeline in-memory,
    persist results to DB, cache for dashboard, return summary JSON.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    run_id = str(uuid.uuid4())
    file_bytes = await file.read()

    try:
        result = run_pipeline_inmemory(file_bytes, file.filename, run_id)
        # Cache (without raw bytes, those go to download endpoint)
        excel_bytes = result.pop("excel_bytes")
        _results_cache[run_id] = {"result": result, "excel_bytes": excel_bytes}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{run_id}")
def download_excel(run_id: str):
    """Stream the generated Excel file back as a direct download."""
    cached = _results_cache.get(run_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Run not found or expired. Re-run the pipeline.")

    excel_bytes = cached["excel_bytes"]
    filename = f"BAM_output_{run_id[:8]}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/results/{run_id}")
def get_results(run_id: str):
    """Fetch cached in-memory results for a run."""
    cached = _results_cache.get(run_id)
    if cached:
        return cached["result"]

    # Fallback: try DB
    if engine is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    with engine.connect() as conn:
        run = conn.execute(text("SELECT * FROM pipeline_runs WHERE id=:id"), {"id": run_id}).fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found.")
        results = conn.execute(text("SELECT * FROM results_data WHERE run_id=:id"), {"id": run_id}).fetchall()

    return {
        "run_id": run_id,
        "status": run.status,
        "summary": {
            "total_messages": run.total_messages,
            "total_bigrams": run.total_bigrams,
            "tagged_pct": run.tagged_pct,
            "duration_sec": run.run_duration_sec,
        },
        "word_level": [dict(r._mapping) for r in results if r.level == "word"][:100],
        "t2": [dict(r._mapping) for r in results if r.level == "t2"],
    }

@app.get("/api/runs")
def list_runs(limit: int = 20):
    """List recent pipeline runs from DB."""
    if engine is None:
        return {"runs": [], "note": "No database connected."}
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, status, total_messages, total_bigrams, tagged_pct, run_duration_sec, created_at, completed_at "
            "FROM pipeline_runs ORDER BY created_at DESC LIMIT :limit"
        ), {"limit": limit}).fetchall()
    return {"runs": [dict(r._mapping) for r in rows]}

@app.post("/api/feedback")
def submit_feedback(
    run_id: str = Form(...),
    category: str = Form(...),
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
    attribute_ref: Optional[str] = Form(None),
):
    """Submit feedback on a pipeline run. Persisted to DB if available."""
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    if category not in ("accuracy", "completeness", "usefulness", "general"):
        raise HTTPException(status_code=400, detail="Invalid category.")

    if engine:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO feedback (id, run_id, category, rating, comment, attribute_ref, created_at)
                VALUES (:id, :run_id, :category, :rating, :comment, :attribute_ref, :created_at)
            """), {
                "id": str(uuid.uuid4()), "run_id": run_id, "category": category,
                "rating": rating, "comment": comment, "attribute_ref": attribute_ref,
                "created_at": datetime.now(timezone.utc)
            })

    return {"status": "success", "message": "Feedback recorded. Thank you!"}
