import streamlit as st
import json, os, base64, mimetypes
from datetime import datetime, date
from pathlib import Path

st.set_page_config(page_title="WC Lab Dashboard", layout="wide", page_icon="🧪")

DB_FILE      = "/root/lab/wo_database.json"
RECORDS_FILE = "/root/lab/qc05_records.json"
MEDIA_DIR    = "/root/lab/media"
LINES        = ["L-03", "L-05", "L-06", "L-07"]
os.makedirs(MEDIA_DIR, exist_ok=True)

FORMS = [
    {"code": "WC-F-QC-01", "name": "100% FIB Slit Verification Form"},
    {"code": "WC-F-QC-02", "name": "100% Mono Dtex Verification Form"},
    {"code": "WC-F-QC-05", "name": "Mono Yarn Full Inspection Form"},
    {"code": "WC-F-QC-07", "name": "Slit Yarn Full Inspection Form"},
    {"code": "WC-F-QC-08", "name": "Twisted Mono Yarn Inspection Form"},
    {"code": "WC-F-QC-10", "name": "Raw Material Inspection Form"},
    {"code": "WC-F-QC-19", "name": "QC Intermediate and Final Product Verification"},
    {"code": "WC-F-QC-20", "name": "Texturized Yarn Bulk Shrinkage Full Inspection"},
    {"code": "WC-F-QC-21", "name": "QC Texturized 2 Color Yarn Full Inspection"},
    {"code": "WC-F-QC-22", "name": "QC Texturized 1 Color Yarn Full Inspection"},
]
FORM_NAMES = {f["code"]: f["name"] for f in FORMS}
IMPLEMENTED = {"WC-F-QC-05"}

UNITS = {
    "dtex": "dtex", "total_dtex": "dtex",
    "boiling_shrinkage": "%", "thickness": "µm",
    "tensile": "N", "yarn_wrap": "wraps/m",
    "air_shrinkage": "%", "width": "mm", "elongation": "%",
}

# ── DB helpers ────────────────────────────────────────────────────────────────
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f: return json.load(f)
    return {"work_orders": {}}

def save_db(db):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=2)

def get_wo(db, line): return db["work_orders"].get(line)

def load_records():
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE) as f: return json.load(f)
    return []

def save_records(recs):
    os.makedirs(os.path.dirname(RECORDS_FILE), exist_ok=True)
    with open(RECORDS_FILE, "w") as f: json.dump(recs, f, indent=2)

def add_record(rec):
    recs = load_records()
    rec["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    recs.append(rec); save_records(recs)
    return rec["id"]

def update_record(record_id, rec):
    recs = load_records()
    for i, r in enumerate(recs):
        if r.get("id") == record_id:
            rec["id"] = record_id
            rec["edited_at"] = datetime.now().isoformat()
            recs[i] = rec; break
    save_records(recs)

def delete_record(record_id):
    recs = [r for r in load_records() if r.get("id") != record_id]
    save_records(recs)

def get_records_for_line_date(line, wo_number, date_str):
    result = {"DS": [], "NS": []}
    for r in load_records():
        if r.get("line")==line.replace("L-","") and r.get("wo")==wo_number and r.get("date")==date_str:
            s = r.get("shift","DS")
            if s in result: result[s].append(r)
    for s in result: result[s].sort(key=lambda x: x.get("time",""))
    return result

# ── Media helpers ─────────────────────────────────────────────────────────────
def save_media_file(record_id, file_type, uploaded_file, wo_number):
    ext   = Path(uploaded_file.name).suffix
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Format: TYPE_WORKORDER_datetime.ext  e.g. protocol_2607019_20260420_143022.jpg
    fname = f"{file_type}_{wo_number}_{ts}{ext}"
    fpath = os.path.join(MEDIA_DIR, record_id)
    os.makedirs(fpath, exist_ok=True)
    with open(os.path.join(fpath, fname), "wb") as f: f.write(uploaded_file.getbuffer())
    return fname

def get_media_files(record_id):
    fpath = os.path.join(MEDIA_DIR, record_id)
    if not os.path.exists(fpath): return []
    return sorted(os.listdir(fpath))

def get_media_path(record_id, fname):
    return os.path.join(MEDIA_DIR, record_id, fname)

# ── Presence helpers ──────────────────────────────────────────────────────────
PRESENCE_FILE   = "/root/lab/presence.json"
PRESENCE_EXPIRE = 120  # seconds

def load_presence():
    if os.path.exists(PRESENCE_FILE):
        with open(PRESENCE_FILE) as f: return json.load(f)
    return {}

def save_presence_data(p):
    with open(PRESENCE_FILE, "w") as f: json.dump(p, f)

def set_presence(record_id, user):
    if not record_id or not user: return
    p = load_presence()
    p[record_id] = {"user": user, "since": datetime.now().isoformat()}
    save_presence_data(p)

def clear_presence(record_id, user):
    if not record_id: return
    p = load_presence()
    if p.get(record_id, {}).get("user") == user:
        del p[record_id]; save_presence_data(p)

def get_presence(record_id):
    if not record_id: return None
    p = load_presence()
    entry = p.get(record_id)
    if not entry: return None
    try:
        since = datetime.fromisoformat(entry["since"])
        if (datetime.now() - since).seconds < PRESENCE_EXPIRE:
            return entry
    except: pass
    return None

def get_all_presence():
    p = load_presence(); result = {}; now = datetime.now()
    for rid, entry in p.items():
        try:
            since = datetime.fromisoformat(entry["since"])
            if (now - since).seconds < PRESENCE_EXPIRE:
                result[rid] = entry
        except: pass
    return result

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.wc-header {
    background:linear-gradient(90deg,#1a3a5c,#2563a8);
    color:white; padding:16px 24px; border-radius:10px;
    display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;
}
.wc-header h1 { margin:0; font-size:1.45rem; }
.wc-header span { font-size:.88rem; opacity:.85; }
.line-card {
    background:white; border-radius:10px; padding:16px 18px;
    border-left:6px solid #2563a8; box-shadow:0 2px 8px rgba(0,0,0,.07); margin-bottom:6px;
}
.line-card.empty { border-left-color:#cbd5e1; background:#f8fafc; }
.line-title { font-size:1.15rem; font-weight:700; color:#1a3a5c; margin-bottom:6px; }
.badge { display:inline-block; border-radius:5px; padding:2px 9px; font-size:.8rem; font-weight:600; margin-right:5px; }
.badge-wo   { background:#dbeafe; color:#1d4ed8; }
.badge-item { background:#f0fdf4; color:#15803d; }
.badge-col  { background:#fef9c3; color:#854d0e; }
.no-rec { color:#94a3b8; font-size:.82rem; font-style:italic; }
.section-lbl {
    background:#f1f5f9; font-weight:700; font-size:.8rem;
    color:#1e293b; padding:4px 8px; border-bottom:1px solid #e2e8f0;
    margin-top:8px; border-radius:4px 4px 0 0;
}
.unit-tag {
    display:inline-block; background:#e0f2fe; color:#0369a1;
    border-radius:4px; padding:1px 7px; font-size:.75rem; font-weight:600; margin-left:4px;
}
.edit-banner {
    background:#fff7ed; border:1px solid #fed7aa; border-radius:8px;
    padding:10px 16px; margin-bottom:12px; color:#9a3412; font-weight:600;
}
.presence-badge {
    display:inline-block; background:#fef9c3; color:#854d0e;
    border-radius:20px; padding:2px 10px; font-size:.78rem; font-weight:600;
    border:1px solid #fde68a; margin-left:6px;
}
.float-nav {
    position:fixed; left:16px; top:50%; transform:translateY(-50%);
    z-index:9999; display:flex; flex-direction:column; gap:6px;
    background:rgba(255,255,255,.95); border:1px solid #e2e8f0;
    border-radius:12px; padding:10px 8px; box-shadow:0 4px 16px rgba(0,0,0,.12);
}
.float-nav a {
    display:block; background:#2563a8; color:white !important;
    border-radius:8px; padding:6px 10px; font-size:.78rem; font-weight:700;
    text-align:center; text-decoration:none !important; min-width:48px;
}
.float-nav a:hover { background:#1a3a5c; }
.float-nav .nav-title { font-size:.68rem; color:#94a3b8; text-align:center; font-weight:600; margin-bottom:2px; }
div[data-testid="stNumberInput"] input {
    font-size:1.05rem !important; height:42px !important; text-align:center !important;
    background-color:#f0f9ff; border-color:#bae6fd;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("page","dashboard"),("sel_line",None),("wo_action",None),
             ("edit_record_id",None),("form_shift","DS"),("confirm_delete",None),
             ("current_user","")]:
    if k not in st.session_state: st.session_state[k] = v

now_str = datetime.now().strftime("%d %b %Y  |  %H:%M")
st.markdown(f'<div class="wc-header"><h1>🧪 WILDCAT ENTERPRISE — Lab Dashboard</h1><span>{now_str}</span></div>', unsafe_allow_html=True)

# ── User name (sidebar, persistent) ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 👤 User")
    user_input = st.text_input("Your name", value=st.session_state.current_user,
                                placeholder="Enter your name", key="user_input")
    if user_input != st.session_state.current_user:
        st.session_state.current_user = user_input
    if st.session_state.current_user:
        st.success(f"Hello, **{st.session_state.current_user}**!")
    else:
        st.warning("Please enter your name")
    st.divider()
    st.markdown("**Navigation**")
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page="dashboard"; st.rerun()

db   = load_db()
page = st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    st.markdown("### 📋 Active Work Orders")
    today = str(date.today())
    cols  = st.columns(2)
    for i, line in enumerate(LINES):
        wo = get_wo(db, line)
        with cols[i % 2]:
            if wo:
                colors_str  = " / ".join(wo.get("colors",[]))
                day_records = get_records_for_line_date(line, wo["wo_number"], today)
                shift_html  = ""
                for shift in ["DS","NS"]:
                    recs = day_records[shift]
                    shift_html += f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;flex-wrap:wrap;"><span style="font-weight:700;font-size:.85rem;color:#475569;min-width:28px;">{shift}:</span>'
                    if recs:
                        for r in recs:
                            t = r.get("time","??:??")
                            shift_html += f'<span style="background:#e0f2fe;color:#0369a1;border-radius:20px;padding:3px 12px;font-size:.82rem;font-weight:600;border:1px solid #bae6fd;">🕐 {t}</span> '
                    else:
                        shift_html += '<span class="no-rec">No record yet</span>'
                    shift_html += "</div>"
                st.markdown(f"""
                <div class="line-card">
                    <div class="line-title">🟢 {line}</div>
                    <span class="badge badge-wo">WO: {wo['wo_number']}</span>
                    <span class="badge badge-item">ITEM: {wo['item_code']}</span>
                    <span class="badge badge-col">{wo['color_count']} Color</span>
                    <div style="color:#475569;font-size:.85rem;margin-top:5px;">{wo.get('item_name','')}</div>
                    <div style="color:#94a3b8;font-size:.78rem;margin-bottom:8px;">{colors_str}</div>
                    {shift_html}
                </div>""", unsafe_allow_html=True)
                b1,b2,b3,b4 = st.columns(4)
                with b1:
                    if st.button("📂 Forms", key=f"frm_{line}", use_container_width=True, type="primary"):
                        st.session_state.sel_line=line; st.session_state.page="forms"; st.rerun()
                with b2:
                    if st.button("📋 Records", key=f"rec_{line}", use_container_width=True):
                        st.session_state.sel_line=line; st.session_state.page="records"; st.rerun()
                with b3:
                    if st.button("🔄 Change WO", key=f"chg_{line}", use_container_width=True):
                        st.session_state.sel_line=line; st.session_state.wo_action="change"; st.session_state.page="wo_entry"; st.rerun()
                with b4:
                    if st.button("❌ Close WO", key=f"cls_{line}", use_container_width=True):
                        if line in db["work_orders"]: del db["work_orders"][line]; save_db(db); st.rerun()
            else:
                st.markdown(f'<div class="line-card empty"><div class="line-title" style="color:#64748b;">⚪ {line}</div><div style="color:#94a3b8;font-style:italic;font-size:.9rem;">No active work order</div></div>', unsafe_allow_html=True)
                if st.button("➕ New Work Order", key=f"new_{line}", use_container_width=True):
                    st.session_state.sel_line=line; st.session_state.wo_action="new"; st.session_state.page="wo_entry"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RECORDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "records":
    line = st.session_state.sel_line; wo = get_wo(db, line)
    if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    st.markdown(f"### 📋 Records — **{line}**")
    if wo:
        st.markdown(f'<div style="background:#dbeafe;border-radius:8px;padding:8px 14px;margin:6px 0;font-size:.9rem;"><b>WO:</b> {wo["wo_number"]} | <b>ITEM:</b> {wo["item_code"]} | {wo.get("item_name","")}</div>', unsafe_allow_html=True)
    st.divider()

    all_recs  = load_records()
    line_recs = [r for r in all_recs if r.get("line") == line.replace("L-","")]
    all_presence = get_all_presence()

    st.markdown("**🔍 Filter**")
    fc1,fc2,fc3,fc4,fc5 = st.columns([2,1.5,1.5,1.5,1.5])
    with fc1: wo_filter = st.text_input("WO Number", placeholder="e.g. 2607019", key="f_wo")
    with fc2:
        form_opts = ["All"] + sorted(set(r.get("form","") for r in line_recs if r.get("form")))
        form_filter = st.selectbox("Form", form_opts, key="f_form")
    with fc3: shift_filter = st.selectbox("Shift", ["All","DS","NS"], key="f_shift")
    with fc4: date_from = st.date_input("From", value=None, key="f_from")
    with fc5: date_to   = st.date_input("To",   value=None, key="f_to")

    filtered = line_recs
    if wo_filter: filtered = [r for r in filtered if wo_filter.lower() in r.get("wo","").lower()]
    if form_filter != "All": filtered = [r for r in filtered if r.get("form","") == form_filter]
    if shift_filter != "All": filtered = [r for r in filtered if r.get("shift","") == shift_filter]
    if date_from: filtered = [r for r in filtered if r.get("date","") >= str(date_from)]
    if date_to:   filtered = [r for r in filtered if r.get("date","") <= str(date_to)]

    st.markdown(f"**{len(filtered)} record(s) found**")
    st.divider()

    if st.session_state.confirm_delete:
        rid = st.session_state.confirm_delete
        st.error("⚠️ Are you sure you want to delete this record?")
        cd1,cd2 = st.columns(2)
        with cd1:
            if st.button("🗑️ Yes, Delete", use_container_width=True, type="primary"):
                delete_record(rid); st.session_state.confirm_delete=None; st.rerun()
        with cd2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_delete=None; st.rerun()
        st.divider()

    if not filtered:
        st.info("No records match the filter.")
    else:
        dates = sorted(set(r.get("date","") for r in filtered), reverse=True)
        for d in dates:
            day_recs = [r for r in filtered if r.get("date")==d]
            with st.expander(f"📅 {d}  —  {len(day_recs)} record(s)", expanded=(d==str(date.today()))):
                for r in sorted(day_recs, key=lambda x: x.get("time","")):
                    edited    = " ✏️" if r.get("edited_at") else ""
                    form_code = r.get("form","?")
                    rid       = r.get("id","")
                    media_cnt = len(get_media_files(rid)) if rid else 0
                    media_str = f" 📎{media_cnt}" if media_cnt else ""

                    # Presence
                    presence  = all_presence.get(rid)
                    pres_html = ""
                    if presence and presence.get("user") != st.session_state.current_user:
                        pres_html = f'<span class="presence-badge">👁️ {presence["user"]}</span>'

                    c1,c2,c3,c4,c5,c6 = st.columns([0.8,0.8,1.2,1.5,3.5,2])
                    with c1: st.markdown(f"**{r.get('shift','?')}**")
                    with c2: st.markdown(f"🕐 {r.get('time','?')}")
                    with c3: st.markdown(f"WO: {r.get('wo','?')}")
                    with c4: st.markdown(f"📋 `{form_code}`")
                    with c5: st.markdown(f"{r.get('operator','?')}{edited}{media_str} {pres_html}", unsafe_allow_html=True)
                    with c6:
                        e1,e2 = st.columns(2)
                        with e1:
                            if rid and st.button("✏️ Edit", key=f"edit_{rid}", use_container_width=True):
                                st.session_state.edit_record_id=rid
                                st.session_state.sel_line=line
                                st.session_state.page="form_wcfqc05"; st.rerun()
                        with e2:
                            if rid and st.button("🗑️ Del", key=f"del_{rid}", use_container_width=True):
                                st.session_state.confirm_delete=rid; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# WO ENTRY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "wo_entry":
    line=st.session_state.sel_line; action=st.session_state.wo_action; existing=get_wo(db,line)
    if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    st.markdown(f"### {'🔄 Change' if action=='change' else '➕ New'} Work Order — **{line}**")
    st.divider()
    color_defaults={1:["WHITE","","",""],2:["FIELD GREEN","OLIVE GREEN","",""],
                    3:["FIELD GREEN","APPLE GREEN","OLIVE GREEN",""],
                    4:["FIELD GREEN","APPLE GREEN","OLIVE GREEN","LIME GREEN"]}
    prev_n   = existing["color_count"] if existing else 3
    n_colors = st.selectbox("Number of Colors *",[1,2,3,4],index=prev_n-1,key="wo_ncolors")
    with st.form("wo_form"):
        c1,c2=st.columns(2)
        with c1:
            wo_num =st.text_input("Work Order No *",value=existing["wo_number"] if existing else "")
            item_cd=st.text_input("Item Code *",    value=existing["item_code"]  if existing else "")
        with c2:
            item_nm=st.text_input("Item Name / Description",value=existing.get("item_name","") if existing else "")
        prev_colors=existing.get("colors",[]) if existing else []
        defaults=color_defaults[n_colors]
        st.markdown(f"**Color Names** ({n_colors} color{'s' if n_colors>1 else ''})")
        ccols=st.columns(4); colors_in=[]
        for idx in range(4):
            default=prev_colors[idx] if idx<len(prev_colors) else defaults[idx]
            with ccols[idx]:
                val=st.text_input(f"Color {idx+1}" if idx<n_colors else f"Color {idx+1} (unused)",
                                  value=default if idx<n_colors else "",key=f"ci_{idx}",disabled=(idx>=n_colors))
                colors_in.append(val if idx<n_colors else "")
        if st.form_submit_button("💾 Save Work Order",use_container_width=True,type="primary"):
            if not wo_num or not item_cd: st.error("WO Number and Item Code are required!")
            else:
                db["work_orders"][line]={"wo_number":wo_num,"item_code":item_cd,"item_name":item_nm,
                    "color_count":n_colors,"colors":[c.upper() for c in colors_in[:n_colors] if c],
                    "created_at":datetime.now().isoformat()}
                save_db(db); st.success(f"✅ Saved for {line}!"); st.session_state.page="dashboard"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FORM SELECTION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "forms":
    line=st.session_state.sel_line; wo=get_wo(db,line)
    if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    st.markdown(f"### 📂 Select Form — **{line}**")
    if wo:
        st.markdown(f'<div style="background:#dbeafe;border-radius:8px;padding:10px 16px;margin:8px 0;font-size:.9rem;"><b>{line}</b> | <b>WO:</b> {wo["wo_number"]} | <b>ITEM:</b> {wo["item_code"]} | {wo.get("item_name","")} | <b>{wo["color_count"]} Color</b> — {" / ".join(wo.get("colors",[]))}</div>', unsafe_allow_html=True)
    shift_sel=st.radio("Shift",["DS","NS"],horizontal=True)
    st.session_state.form_shift=shift_sel
    st.divider()
    for form in FORMS:
        c1,c2,c3=st.columns([1.4,5,1.4])
        with c1: st.markdown(f"**{form['code']}**")
        with c2: st.markdown(form['name'])
        with c3:
            impl=form['code'] in IMPLEMENTED
            if st.button("▶ Open",key=f"f_{form['code']}",use_container_width=True,
                         type="primary" if impl else "secondary",disabled=not impl):
                st.session_state.edit_record_id=None
                st.session_state.page=f"form_{form['code'].replace('-','').lower()}"; st.rerun()
        st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# WC-F-QC-05 FORM
# ══════════════════════════════════════════════════════════════════════════════
elif page == "form_wcfqc05":
    line    = st.session_state.sel_line
    wo      = get_wo(db, line)
    edit_id = st.session_state.edit_record_id
    existing_rec = None
    if edit_id:
        for r in load_records():
            if r.get("id") == edit_id: existing_rec=r; break
    is_edit = existing_rec is not None

    # Set presence
    if edit_id and st.session_state.current_user:
        set_presence(edit_id, st.session_state.current_user)

    back_page = "records" if is_edit else "forms"
    if st.button(f"← Back to {'Records' if is_edit else 'Forms'}"):
        if edit_id: clear_presence(edit_id, st.session_state.current_user)
        st.session_state.page=back_page; st.rerun()

    if not wo and not existing_rec: st.error("No active WO!"); st.stop()
    if not wo and existing_rec:
        wo={"wo_number":existing_rec.get("wo",""),"item_code":existing_rec.get("item",""),
            "item_name":existing_rec.get("item_name",""),"color_count":len(existing_rec.get("colors",[])),
            "colors":existing_rec.get("colors",[])}

    colors=wo.get("colors",[]); color_count=wo["color_count"]

    def gv(path, default=None):
        if not existing_rec: return default
        keys=path.split("."); v=existing_rec
        for k in keys:
            if isinstance(v,dict): v=v.get(k,default)
            else: return default
        return v if v is not None else default

    if is_edit:
        edited_str = f" | Last edited: {existing_rec['edited_at'][:16].replace('T',' ')}" if existing_rec.get('edited_at') else ""
        # Show who else is viewing
        presence = get_presence(edit_id)
        if presence and presence.get("user") != st.session_state.current_user:
            st.markdown(f'<div style="background:#fef9c3;border:1px solid #fde68a;border-radius:8px;padding:8px 14px;margin-bottom:10px;">👁️ <b>{presence["user"]}</b> is also viewing this record</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="edit-banner">✏️ EDITING — {existing_rec.get("date","")} | {existing_rec.get("shift","")} | {existing_rec.get("time","")} | {existing_rec.get("operator","")}{edited_str}</div>', unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;border:2px solid #334155;border-radius:6px;overflow:hidden;margin-bottom:14px;"><div style="background:#1a3a5c;color:white;padding:10px;font-size:1.05rem;font-weight:bold;">🏭 WILDCAT ENTERPRISE TEXTILES INDUSTRIES</div><div style="background:#2563a8;color:white;padding:5px;font-size:.88rem;">WC-F-QC-05 Mono Yarn Full Inspection Form &nbsp;|&nbsp; Rev.00 &nbsp;|&nbsp; Date: 02-Jan-2025</div></div>', unsafe_allow_html=True)

    h1,h2,h3,h4=st.columns([1,1,2,1])
    with h1: line_v=st.text_input("LINE",value=gv("line",line.replace("L-","")))
    with h2:
        shift_opts=["DS","NS"]; sd=gv("shift",st.session_state.form_shift)
        shift_v=st.selectbox("SHIFT",shift_opts,index=shift_opts.index(sd) if sd in shift_opts else 0)
    with h3:
        try: date_obj=date.fromisoformat(gv("date",str(date.today())))
        except: date_obj=date.today()
        date_v=st.date_input("DATE",value=date_obj)
    with h4: time_v=st.text_input("TIME",value=gv("time",datetime.now().strftime("%H:%M")))
    h5,h6,h7=st.columns([2,1,2])
    with h5: st.text_input("WO",value=wo["wo_number"],disabled=True)
    with h6: st.text_input("ITEM",value=wo["item_code"],disabled=True)
    with h7: st.text_input("ITEM NAME",value=wo.get("item_name",""),disabled=True)
    opr_v=st.text_input("OPERATOR",value=gv("operator",st.session_state.current_user),placeholder="Name Surname")
    st.divider()

    st.markdown("#### 📍 Positions")
    saved_pos=gv("positions",[str((i+1)*3) for i in range(5)])
    n_pos=st.number_input("Number of positions",min_value=1,max_value=10,value=len(saved_pos) if saved_pos else 5,step=1)
    n_pos=int(n_pos); pcols=st.columns(n_pos); positions=[]
    for i in range(n_pos):
        dp=saved_pos[i] if i<len(saved_pos) else str((i+1)*3)
        with pcols[i]: positions.append(st.text_input(f"Pos {i+1}",value=dp,key=f"p_{i}"))
    st.divider()

    nav_links="".join([f'<a href="#{p.strip()}">{p.strip()}</a>' for p in positions if p.strip()])
    st.markdown(f'<div class="float-nav"><div class="nav-title">POS</div>{nav_links}</div>', unsafe_allow_html=True)

    st.markdown("#### 🧪 Test Results")
    all_data={}

    for pi in range(n_pos):
        pos=positions[pi]; plabel=pos or f"Pos {pi+1}"
        saved_d=gv(f"test_data.{plabel}",{})

        def sv(test, color, sd=saved_d):
            v=sd.get(test,{})
            return v.get(color,None) if isinstance(v,dict) else None

        st.markdown(f'<div id="{plabel.strip()}"></div>', unsafe_allow_html=True)
        with st.expander(f"📌 Position: {plabel}",expanded=(pi==0)):
            pd_={}
            u=UNITS["dtex"]
            st.markdown(f'<div class="section-lbl">DTEX <span class="unit-tag">{u}</span></div>', unsafe_allow_html=True)
            dtex_v={}; dc=st.columns(color_count)
            for ci,color in enumerate(colors):
                with dc[ci]: dtex_v[color]=st.number_input(color,value=sv("dtex",color),format="%.1f",key=f"dtex_{pi}_{ci}")
            pd_["dtex"]=dtex_v
            st.markdown(f'<div class="section-lbl">TOTAL DTEX <span class="unit-tag">{UNITS["total_dtex"]}</span></div>', unsafe_allow_html=True)
            pd_["total_dtex"]=st.number_input("Total Dtex (manual)",value=saved_d.get("total_dtex",None),format="%.1f",key=f"tdtex_{pi}")

            left,right=st.columns(2)
            with left:
                for key,label in [("boiling_shrinkage","BOILING SHRINKAGE (AVE)"),("thickness","THICKNESS"),("tensile","TENSILE (AVE)")]:
                    u=UNITS[key]
                    st.markdown(f'<div class="section-lbl">{label} <span class="unit-tag">{u}</span></div>', unsafe_allow_html=True)
                    tmp={}
                    for ci,color in enumerate(colors):
                        tmp[color]=st.number_input(color,value=sv(key,color),format="%.0f" if key=="thickness" else "%.1f",key=f"{key}_{pi}_{ci}")
                    pd_[key]=tmp
            with right:
                u=UNITS["yarn_wrap"]
                st.markdown(f'<div class="section-lbl">YARN WRAP PER METER <span class="unit-tag">{u}</span></div>', unsafe_allow_html=True)
                pd_["yarn_wrap"]=st.number_input("Value",value=saved_d.get("yarn_wrap",None),format="%.0f",key=f"yw_{pi}")
                for key,label in [("air_shrinkage","AIR SHRINKAGE"),("width","WIDTH"),("elongation","ELONGATION (AVE)")]:
                    u=UNITS[key]
                    st.markdown(f'<div class="section-lbl">{label} <span class="unit-tag">{u}</span></div>', unsafe_allow_html=True)
                    tmp={}
                    for ci,color in enumerate(colors):
                        tmp[color]=st.number_input(color,value=sv(key,color),format="%.2f" if key=="width" else "%.1f",key=f"{key}_{pi}_{ci}")
                    pd_[key]=tmp
            all_data[plabel]=pd_

    st.divider()
    st.markdown("#### 🔬 SCI / SCE")
    saved_sci=gv("sci",{}); spool_no=st.text_input("Spool #",value=gv("spool_no",""),placeholder="e.g. 01143")
    sci_data={}; sc=st.columns(color_count)
    for ci,color in enumerate(colors):
        with sc[ci]:
            st.markdown(f"**{color}**")
            sci_data[color]=st.text_input("SCI/SCE",value=saved_sci.get(color,""),placeholder="0.51/0.31",key=f"sci_{ci}")

    st.divider()
    st.markdown('<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 16px;margin-bottom:10px;"><b>TOLERANCE VALUE CHECK</b><br><span style="font-size:.82rem;color:#64748b;">All tests conducted per standard procedure. Results verified for accuracy and compliance.</span></div>', unsafe_allow_html=True)
    verified_v=st.text_input("✅ Verified by",value=gv("verified_by",""),placeholder="Name Surname")

    st.divider()
    st.markdown("#### 💬 Comments")
    comments_v=st.text_area("Notes, observations, issues...",value=gv("comments",""),height=100,
                             placeholder="e.g. Color inconsistency observed on position 6...")

    st.markdown("#### 📷 Photos")
    st.caption("Upload photos related to this inspection")
    photo_uploads=st.file_uploader("Upload photos",type=["jpg","jpeg","png","webp"],
                                    accept_multiple_files=True,key="photo_upload")

    st.divider()
    if st.button("💾 UPDATE RECORD" if is_edit else "💾 SAVE RECORD",use_container_width=True,type="primary"):
        if not opr_v: st.error("Please enter Operator name!"); st.stop()
        if not verified_v: st.error("Please enter Verified by!"); st.stop()
        record={"form":"WC-F-QC-05","saved_at":datetime.now().isoformat(),
                "line":line_v,"shift":shift_v,"date":str(date_v),"time":time_v,
                "wo":wo["wo_number"],"item":wo["item_code"],"item_name":wo.get("item_name",""),
                "operator":opr_v,"verified_by":verified_v,
                "colors":colors,"positions":positions,
                "test_data":all_data,"sci":sci_data,"spool_no":spool_no,
                "comments":comments_v}
        if is_edit:
            update_record(edit_id,record)
            if photo_uploads:
                for uf in photo_uploads: save_media_file(edit_id,"photo",uf,wo["wo_number"])
            clear_presence(edit_id, st.session_state.current_user)
            st.success("✅ Record updated!")
        else:
            new_id=add_record(record)
            if photo_uploads:
                for uf in photo_uploads: save_media_file(new_id,"photo",uf,wo["wo_number"])
            st.success("✅ Record saved!"); st.balloons()

    # ── Media section ─────────────────────────────────────────────────────────
    record_id = edit_id if is_edit else None
    if record_id:
        st.divider()
        st.markdown("#### 📁 Media & Documents")
        st.caption("Select attachment type, then upload. File saved as: **TYPE_WORKORDER_datetime.ext**")

        ATTACH_TYPES = {
            "📷 Photo":        "photo",
            "🔬 Spectro":      "spectro",
            "📋 Protocol":     "protocol",
            "📄 TXT Photo":    "txt_photo",
            "📊 Lab Report":   "lab_report",
            "📁 Other":        "other",
        }
        a1, a2 = st.columns([2, 4])
        with a1:
            mt_label = st.selectbox("Attachment Type", list(ATTACH_TYPES.keys()), key="mt_sel")
            mt_sel   = ATTACH_TYPES[mt_label]
        with a2:
            doc_upload = st.file_uploader("Select file",
                                           type=["jpg","jpeg","png","pdf","txt","xlsx","docx","webp"],
                                           key="doc_upload")
        if doc_upload:
            preview_name = f"{mt_sel}_{wo['wo_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{Path(doc_upload.name).suffix}"
            st.caption(f"Will be saved as: `{preview_name}`")
            if st.button("📎 Attach File", use_container_width=True, type="primary"):
                fname=save_media_file(record_id,mt_sel,doc_upload,wo["wo_number"])
                st.success(f"✅ Saved as: {fname}"); st.rerun()

        existing_files=get_media_files(record_id)
        if existing_files:
            st.markdown(f"**{len(existing_files)} file(s) attached:**")
            for fname in existing_files:
                fpath=get_media_path(record_id,fname)
                fsize=os.path.getsize(fpath)
                with open(fpath,"rb") as f: fdata=f.read()
                mime=mimetypes.guess_type(fpath)[0] or "application/octet-stream"
                fc1,fc2,fc3=st.columns([5,1.5,1.5])
                with fc1: st.markdown(f"📄 `{fname}` &nbsp;<span style='color:#94a3b8;font-size:.8rem;'>{fsize//1024} KB</span>",unsafe_allow_html=True)
                with fc2: st.download_button("⬇",data=fdata,file_name=fname,mime=mime,key=f"dl_{fname}",use_container_width=True)
                with fc3:
                    if st.button("🗑",key=f"delmedia_{fname}",use_container_width=True):
                        os.remove(fpath); st.rerun()

    # ── PDF Export ────────────────────────────────────────────────────────────
    if is_edit and existing_rec:
        st.divider()
        st.markdown("#### 📄 Export PDF")
        if st.button("📄 Generate PDF",use_container_width=True):
            try:
                import sys; sys.path.insert(0,"/root/lab")
                from pdf_export import generate_pdf
                pdf_bytes=generate_pdf(existing_rec)
                fname=f"{existing_rec.get('wo','WO')}_{existing_rec.get('date','date')}_{existing_rec.get('shift','')}_QC05.pdf"
                st.download_button("⬇ Download PDF",data=pdf_bytes,file_name=fname,
                                   mime="application/pdf",key="pdf_dl",use_container_width=True)
            except Exception as e:
                st.error(f"PDF error: {e}")
