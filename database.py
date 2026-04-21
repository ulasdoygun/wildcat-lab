"""
Wildcat Lab - SQLite Database Layer
All forms use this module for data access.
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "/root/lab/wildcat_lab.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    c = conn.cursor()
    
    c.executescript("""
        CREATE TABLE IF NOT EXISTS work_orders (
            line        TEXT PRIMARY KEY,
            wo_number   TEXT NOT NULL,
            item_code   TEXT NOT NULL,
            item_name   TEXT DEFAULT '',
            color_count INTEGER DEFAULT 1,
            colors      TEXT DEFAULT '[]',
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS records (
            id          TEXT PRIMARY KEY,
            form_code   TEXT NOT NULL,
            line        TEXT,
            wo_number   TEXT,
            item_code   TEXT,
            item_name   TEXT,
            shift       TEXT,
            date        TEXT,
            time        TEXT,
            operator    TEXT,
            verified_by TEXT,
            colors      TEXT DEFAULT '[]',
            data        TEXT DEFAULT '{}',
            comments    TEXT DEFAULT '',
            saved_at    TEXT,
            edited_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS media (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id   TEXT NOT NULL,
            filename    TEXT NOT NULL,
            file_type   TEXT,
            wo_number   TEXT,
            created_at  TEXT,
            FOREIGN KEY (record_id) REFERENCES records(id)
        );

        CREATE TABLE IF NOT EXISTS presence (
            record_id   TEXT PRIMARY KEY,
            username    TEXT,
            since       TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_records_line ON records(line);
        CREATE INDEX IF NOT EXISTS idx_records_wo ON records(wo_number);
        CREATE INDEX IF NOT EXISTS idx_records_date ON records(date);
        CREATE INDEX IF NOT EXISTS idx_records_form ON records(form_code);
        CREATE INDEX IF NOT EXISTS idx_media_record ON media(record_id);
    """)
    conn.commit()
    conn.close()

# ── Work Orders ───────────────────────────────────────────────────────────────
def get_all_work_orders():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM work_orders").fetchall()
    conn.close()
    result = {}
    for r in rows:
        result[r["line"]] = {
            "wo_number":   r["wo_number"],
            "item_code":   r["item_code"],
            "item_name":   r["item_name"],
            "color_count": r["color_count"],
            "colors":      json.loads(r["colors"]),
            "created_at":  r["created_at"],
        }
    return result

def get_work_order(line):
    conn = get_conn()
    r = conn.execute("SELECT * FROM work_orders WHERE line=?", (line,)).fetchone()
    conn.close()
    if not r: return None
    return {
        "wo_number":   r["wo_number"],
        "item_code":   r["item_code"],
        "item_name":   r["item_name"],
        "color_count": r["color_count"],
        "colors":      json.loads(r["colors"]),
        "created_at":  r["created_at"],
    }

def save_work_order(line, wo):
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO work_orders
        (line, wo_number, item_code, item_name, color_count, colors, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (line, wo["wo_number"], wo["item_code"], wo.get("item_name",""),
          wo["color_count"], json.dumps(wo["colors"]), wo.get("created_at", datetime.now().isoformat())))
    conn.commit()
    conn.close()

def delete_work_order(line):
    conn = get_conn()
    conn.execute("DELETE FROM work_orders WHERE line=?", (line,))
    conn.commit()
    conn.close()

# ── Records ───────────────────────────────────────────────────────────────────
def add_record(form_code, line, wo, shift, date, time_val, operator, verified_by,
               colors, data, comments=""):
    record_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    conn = get_conn()
    conn.execute("""
        INSERT INTO records
        (id, form_code, line, wo_number, item_code, item_name, shift, date, time,
         operator, verified_by, colors, data, comments, saved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (record_id, form_code, line,
          wo.get("wo_number",""), wo.get("item_code",""), wo.get("item_name",""),
          shift, date, time_val, operator, verified_by,
          json.dumps(colors), json.dumps(data), comments,
          datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return record_id

def update_record(record_id, operator, verified_by, colors, data, comments="",
                  shift=None, date=None, time_val=None, line=None):
    conn = get_conn()
    conn.execute("""
        UPDATE records SET
            operator=?, verified_by=?, colors=?, data=?, comments=?,
            edited_at=?, shift=COALESCE(?,shift), date=COALESCE(?,date),
            time=COALESCE(?,time), line=COALESCE(?,line)
        WHERE id=?
    """, (operator, verified_by, json.dumps(colors), json.dumps(data), comments,
          datetime.now().isoformat(), shift, date, time_val, line, record_id))
    conn.commit()
    conn.close()

def delete_record(record_id):
    conn = get_conn()
    conn.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.execute("DELETE FROM media WHERE record_id=?", (record_id,))
    conn.commit()
    conn.close()

def get_record(record_id):
    conn = get_conn()
    r = conn.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
    conn.close()
    if not r: return None
    return _row_to_dict(r)

def get_records(line=None, form_code=None, wo_number=None, shift=None,
                date_from=None, date_to=None):
    sql    = "SELECT * FROM records WHERE 1=1"
    params = []
    if line:      sql += " AND line=?";       params.append(line.replace("L-",""))
    if form_code: sql += " AND form_code=?";  params.append(form_code)
    if wo_number: sql += " AND wo_number LIKE ?"; params.append(f"%{wo_number}%")
    if shift:     sql += " AND shift=?";      params.append(shift)
    if date_from: sql += " AND date>=?";      params.append(date_from)
    if date_to:   sql += " AND date<=?";      params.append(date_to)
    sql += " ORDER BY date DESC, time DESC"
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def get_records_for_today(line, wo_number, date_str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM records WHERE line=? AND wo_number=? AND date=? ORDER BY time",
        (line.replace("L-",""), wo_number, date_str)
    ).fetchall()
    conn.close()
    result = {"DS": [], "NS": []}
    for r in rows:
        d = _row_to_dict(r)
        s = d.get("shift","DS")
        if s in result: result[s].append(d)
    return result

def _row_to_dict(r):
    d = dict(r)
    d["colors"] = json.loads(d.get("colors","[]"))
    d["data"]   = json.loads(d.get("data","{}"))
    return d

# ── Media ─────────────────────────────────────────────────────────────────────
MEDIA_DIR = "/root/lab/media"

def save_media(record_id, file_type, uploaded_file, wo_number):
    from pathlib import Path
    os.makedirs(os.path.join(MEDIA_DIR, record_id), exist_ok=True)
    ext   = Path(uploaded_file.name).suffix
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{file_type}_{wo_number}_{ts}{ext}"
    fpath = os.path.join(MEDIA_DIR, record_id, fname)
    with open(fpath, "wb") as f: f.write(uploaded_file.getbuffer())
    conn = get_conn()
    conn.execute(
        "INSERT INTO media (record_id, filename, file_type, wo_number, created_at) VALUES (?,?,?,?,?)",
        (record_id, fname, file_type, wo_number, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return fname

def get_media(record_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM media WHERE record_id=? ORDER BY created_at", (record_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_media(record_id, filename):
    fpath = os.path.join(MEDIA_DIR, record_id, filename)
    if os.path.exists(fpath): os.remove(fpath)
    conn = get_conn()
    conn.execute("DELETE FROM media WHERE record_id=? AND filename=?", (record_id, filename))
    conn.commit()
    conn.close()

def get_media_path(record_id, filename):
    return os.path.join(MEDIA_DIR, record_id, filename)

# ── Presence ──────────────────────────────────────────────────────────────────
PRESENCE_EXPIRE = 120

def set_presence(record_id, user):
    if not record_id or not user: return
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO presence (record_id, username, since) VALUES (?,?,?)",
        (record_id, user, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def clear_presence(record_id, user):
    if not record_id: return
    conn = get_conn()
    conn.execute("DELETE FROM presence WHERE record_id=? AND username=?", (record_id, user))
    conn.commit()
    conn.close()

def get_presence(record_id):
    conn = get_conn()
    r = conn.execute("SELECT * FROM presence WHERE record_id=?", (record_id,)).fetchone()
    conn.close()
    if not r: return None
    try:
        since = datetime.fromisoformat(r["since"])
        if (datetime.now() - since).seconds < PRESENCE_EXPIRE:
            return dict(r)
    except: pass
    return None

def get_all_presence():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM presence").fetchall()
    conn.close()
    result = {}
    now = datetime.now()
    for r in rows:
        try:
            since = datetime.fromisoformat(r["since"])
            if (now - since).seconds < PRESENCE_EXPIRE:
                result[r["record_id"]] = dict(r)
        except: pass
    return result

# ── Migration from JSON ───────────────────────────────────────────────────────
def migrate_from_json():
    """One-time migration from old JSON files to SQLite."""
    import glob
    
    wo_file = "/root/lab/wo_database.json"
    rec_file = "/root/lab/qc05_records.json"
    
    migrated = 0
    
    # Migrate work orders
    if os.path.exists(wo_file):
        with open(wo_file) as f:
            data = json.load(f)
        for line, wo in data.get("work_orders", {}).items():
            try:
                save_work_order(line, wo)
                migrated += 1
            except: pass
        print(f"Migrated {migrated} work orders")
    
    # Migrate records
    if os.path.exists(rec_file):
        with open(rec_file) as f:
            records = json.load(f)
        rec_migrated = 0
        conn = get_conn()
        for r in records:
            try:
                rid = r.get("id") or datetime.now().strftime("%Y%m%d%H%M%S%f")
                conn.execute("""
                    INSERT OR IGNORE INTO records
                    (id, form_code, line, wo_number, item_code, item_name, shift, date, time,
                     operator, verified_by, colors, data, comments, saved_at, edited_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rid,
                    r.get("form","WC-F-QC-05"),
                    r.get("line",""),
                    r.get("wo",""),
                    r.get("item",""),
                    r.get("item_name",""),
                    r.get("shift","DS"),
                    r.get("date",""),
                    r.get("time",""),
                    r.get("operator",""),
                    r.get("verified_by",""),
                    json.dumps(r.get("colors",[])),
                    json.dumps({
                        "test_data": r.get("test_data",{}),
                        "positions": r.get("positions",[]),
                        "sci":       r.get("sci",{}),
                        "spool_no":  r.get("spool_no",""),
                    }),
                    r.get("comments",""),
                    r.get("saved_at",""),
                    r.get("edited_at",""),
                ))
                rec_migrated += 1
            except Exception as e:
                print(f"Record migration error: {e}")
        conn.commit()
        conn.close()
        print(f"Migrated {rec_migrated} records")
    
    return migrated

if __name__ == "__main__":
    init_db()
    migrate_from_json()
    print("Database initialized and migration complete.")
