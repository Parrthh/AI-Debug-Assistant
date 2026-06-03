import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Database will be created here in this folder: "data/"
DB_PATH = Path("data/memory.db")

def get_connection():
    # Creating and returning a connection to the SQLite database
    # Creating the "data/" folder if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def initialize_db():
    # Creating the database tables if they do not exist
    # We call them once at the start of every pipeline run
    conn = get_connection()
    cursor = conn.cursor()

    # Table for Bugs - Level 1 memory
    # Stored bugs that we have seen before and their accepted fixes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bugs (
            bug_id TEXT PRIMARY KEY,
            bug_type TEXT,
            error_message TEXT,
            original_code TEXT,
            accepted_fix TEXT,
            reuse_count INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # Preferences table - Level 2 memory
    # Stored structured preferences extracted from engineer feedback
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            preference_id TEXT PRIMARY KEY,
            pref_category TEXT,
            rule TEXT,
            frequency INTEGER DEFAULT 1,
            acceptance_rate REAL DEFAULT 0.0,
            last_seen TEXT,
            created_at TEXT
        )
    """)

    # Session table - Benchmark Tracking
    # Record every pipeline run for measuring improvement over time
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            bug_id TEXT,
            fix_source TEXT,
            accepted_flag INTEGER,
            interventions INTEGER DEFAULT 0,
            result_ok INTEGER,
            resolve_time REAL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# LEVEL 1 - BUG RECOGNITION

def find_matching_bug(bug_context):
    """ 
    Searches the bugs table for maching bug using two signals:
    1. Bug type match
    2. Error message similarity

    Returns a confidence level and the matching bug row if found
    Confidence: 'high','medium', or None
    """

    conn = get_connection()
    cursor = conn.cursor()

    bug_type = bug_context["bug_type"]
    error_message = bug_context["error_message"]

    # Looking for bugs with the same bug type
    cursor.execute("""
        SELECT bug_id, bug_type, error_message, accepted_fix, reuse_count 
        FROM bugs
        WHERE bug_type = ?
    """, (bug_type,))

    matches = cursor.fetchall()
    conn.close()

    if not matches:
        # No match found - Claude Call needed
        return None, None

    # Check error message similary for each match
    for match in matches:
        stored_error = match[2]

        # High Confidence - both bug type and error message are similar
        if is_similar(error_message, stored_error):
            return "high", match
        
    # Medium confidence - only bug type matches
    return "medium", matches[0]


def is_similar(error1, error2):
    """
    Simple similarity check between two error messages
    Return True if they share enough keywords
    """
    words1 = set(error1.lower().split())
    words2 = set(error2.lower().split())

    # Remove common words
    noise = {"at","in","the","a","an","is","was","for","of","to"}
    words1 -= noise
    words2 -= noise

    if not words1 or not words2:
        return False

    # Calculating overlap ratio
    overlap = len(words1 & words2) / max(len(words1), len(words2))
    return overlap >= 0.5

def store_bug(bug_context, accepted_fix):
    # Stores a new bug and its accepted fix in the bugs table
    # Called after an engineer accepts a fix
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO bugs
        (bug_id, bug_type, error_message, original_code, accepted_fix, reuse_count, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    """, (
        str(uuid.uuid4()),
        bug_context["bug_type"],
        bug_context["error_message"],
        bug_context["code"],
        accepted_fix,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

def increment_reuse_count(bug_id):
    # Incrementing the reuse counter when a stored fix is reused
    # This is a key benchmark metric

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bugs SET reuse_count = reuse_count + 1 WHERE bug_id = ?
    """, (bug_id,))

    conn.commit()
    conn.close()

# LEVEL - 2: PREFERENCE MEMORY

def get_top_preferences(n=5):
    # Retrieves the top N preferences using the scoring formula:
    # score = (frequency x 0.5) + (recency_score x 0.3) + (acceptance_rate x 0.2)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT preference_id, pref_category, rule, frequency, acceptance_rate, last_seen
        FROM preferences
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    # Calculating score for each preference
    scored = []
    now = datetime.now()

    for row in rows:
        preference_id, category, rule, frequency, acceptance_rate, last_seen = row

        # Normalize frequency to 0-1 range
        max_frequency = max(r[3] for r in rows)
        frequency_score = frequency / max_frequency if max_frequency > 0 else 0

        # Calculating recency score
        last_seen_dt = datetime.fromisoformat(last_seen)
        days_ago = (now - last_seen_dt).days
        
        if days_ago <= 7:
            recency_score = 1.0
        elif days_ago <= 30:
            recency_score = 0.7
        else:
            recency_score = 0.4

        # Final score using our weighted formula
        score = (frequency_score * 0.5) + (recency_score * 0.3) + (acceptance_rate * 0.2)
        scored.append((score,rule))

    # Sort by score descending and return top N rules
    scored.sort(reverse=True)
    return [rule for _, rule in scored[:n]]

def store_preference(category, rule, accepted):
    """
    Stores or updates a preference extractedf from engineers feedback.
    If the same rule already exists, increments frequency and updates acceptance rate and last seen timestamp.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if this preference already exists
    cursor.execute("""
        SELECT preference_id, frequency, acceptance_rate FROM preferences
        WHERE rule = ?
    """, (rule,))

    existing = cursor.fetchone()

    if existing:
        # Update existing preference
        preference_id, frequency, acceptance_rate = existing
        new_frequency = frequency + 1

        # Recalculating acceptance rate as a running average
        new_acceptance_rate = ((acceptance_rate * frequency) + (1 if accepted else 0)) / new_frequency
        cursor.execute("""
            UPDATE preferences
            SET frequency = ?, acceptance_rate = ?, last_seen = ?
            WHERE preference_id = ?
        """, (new_frequency, new_acceptance_rate, datetime.now().isoformat(),preference_id))

    else:
        # Insert new preference
        cursor.execute("""
            INSERT INTO preferences
            (preference_id, pref_category, rule, frequency, acceptance_rate, last_seen, created_at)
            VALUES (?, ?, ?, 1, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            category,
            rule,
            (1.0 if accepted else 0.0),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

# BENCHMARK TRACKING

def store_session(bug_id, fix_source, accepted, interventions, test_passed, resolution_time):
    """
    Records a pipeline session for benchmark tracking
    fix_score: 'stored' (L1 hit) or 'claude' (L2 or full call)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions
        (session_id, bug_id, fix_source, accepted_flag, interventions, result_ok, resolve_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        bug_id,
        fix_source,
        1 if accepted else 0,
        interventions,
        1 if test_passed else 0,
        resolution_time,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


