# storage.py
# Scores are separate columns (not JSON) so we can run aggregate queries like
# "SELECT AVG(causality) FROM weekly_entries WHERE date > '2026-06-01'"
# without parsing text.

import os
import psycopg2
import psycopg2.extras  # Gives us DictCursor so rows behave like dicts
from dotenv import load_dotenv

# Load your local .env variables if running locally
load_dotenv(override=True)

def get_connection():
    db_url = os.environ["DATABASE_URL"]
    # Handle occasional Streamlit/Postgres variation in url scheme
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    # We pass cursor_factory=psycopg2.extras.DictCursor so that 
    # row["column_name"] syntax works exactly like your original sqlite3.Row did!
    return psycopg2.connect(db_url, cursor_factory=psycopg2.extras.DictCursor)

def init_db():
    """
    Since you already ran the SQL setup directly in the Supabase editor, 
    this function acts as a safety connection-check so your app won't crash.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM daily_entries LIMIT 1;")
    except Exception:
        print("Warning: Could not connect or find tables. Ensure SQL script was run on Supabase.")
    finally:
        cursor.close()
        conn.close()

def save_weekly(entry: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Changed placeholders from ? to %s
    # Replaced cursor.lastrowid with RETURNING id
    cursor.execute("""
        INSERT INTO weekly_entries (
            date, news, analysis, score, assessment
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        entry["date"],
        entry["news"],
        entry["analysis"],
        entry.get("score"),
        entry.get("assessment")
    ))
    new_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return new_id

def save_daily(entry: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO daily_entries (date, headlines, notes)
        VALUES (%s, %s, %s)
        RETURNING id;
    """, (entry["date"], entry["headlines"], entry["notes"]))
    
    new_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return new_id

def get_weekly_history(n: int) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM weekly_entries
        ORDER BY date DESC
        LIMIT %s
    """, (n,))
    
    # DictCursor allows us to call dict(row) to convert rows into clean Python dictionaries
    rows = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows

def get_avg_scores(n: int = 8) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Note: In PostgreSQL, a subquery inside a FROM clause MUST have an alias name.
    # We added 'as subquery' at the end of the nested SELECT to prevent a syntax error.
    cursor.execute("""
        SELECT
            AVG(score) as score
        FROM (
            SELECT * FROM weekly_entries
            ORDER BY date DESC
            LIMIT %s
        ) as subquery
    """, (n,))
    
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    # If the subquery yields a value, convert it to a standard dict. 
    # Because AVG() returns a Decimal type in Postgres, we cast it to a float or handle empty sets.
    if row and row["score"] is not None:
        return {"score": float(row["score"])}
    return {"score": None}