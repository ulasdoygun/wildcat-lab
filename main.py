import streamlit as st
import json
import os
from datetime import datetime, date

st.set_page_config(page_title="WC Lab Dashboard", layout="wide", page_icon="🧪")

DB_FILE      = "/root/lab/wo_database.json"
RECORDS_FILE = "/root/lab/qc05_records.json"
LINES        = ["L-03", "L-05", "L-06", "L-07"]

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

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return {"work_orders": {}}

def save_db(db):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_wo(db, line):
    return db["work_orders"].get(line)

def load_records():
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE) as f:
            return json.load(f)
    return []

def save_records(recs):
    os.makedirs(os.path.dirname(RECORDS_FILE), exist_ok=True)
    with open(RECORDS_FILE, "w") as f:
        json.dump(recs, f, indent=2)

def add_record(rec):
    recs = load_records()
    rec["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    recs.append(rec)
    save_records(recs)
    return rec["id"]

def update_record(record_id, rec):
    recs = load_records()
    for i, r in enumerate(recs):
        if r.get("id") == record_id:
            rec["id"] = record_id
            rec["edited_at"] = datetime.now().isoformat()
            recs[i] = rec
            break
    save_records(recs)

def delete_record(record_id):
    recs = load_records()
    recs = [r for r in recs if r.get("id") != record_id]
    save_records(recs)

def get_records_for_line_date(line, wo_number, date_str):
    recs = load_records()
    result = {"DS": [], "NS": []}
    for r in recs:
        if r.get("line") == line.replace("L-","") and r.get("wo") == wo_number and r.get("date") == date_str:
            shift = r.get("shift", "DS")
            if shift in result:
                result[shift].append(r)
    for shift in result:
        result[shift].sort(key=lambda x: x.get("time",""))
    return result

st.markdown("""
<style>
.wc-header {
    background: linear-gradient(90deg,#1a3a5c,#2563a8);
    color:white; padding:16px 24px; border-radius:10px;
    display:flex; justify-content:space-between; align-items:center;
    margin-bottom:20px;
}
.wc-header h1 { margin:0; font-size:1.45rem; }
.wc-header span { font-size:.88rem; opacity:.85; }
.line-card {
    background:white; border-radius:10px; padding:16px 18px;
    border-left:6px solid #2563a8; box-shadow:0 2px 8px rgba(0,0,0,.07);
    margin-bottom:6px;
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
.edit-banner {
    background:#fff7ed; border:1px solid #fed7aa; border-radius:8px;
    padding:10px 16px; margin-bottom:12px; color:#9a3412; font-weight:600;
}
.filter-box {
    background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
    padding:14px 18px; margin-bottom:16px;
}
div[data-testid="stNumberInput"] input {
    font-size:1.05rem !important; height:42px !important; text-align:center !important;
}
</style>
""", unsafe_allow_html=True)

for k, v in [("page","dashboard"),("sel_line",None),("wo_action",None),("edit_record_id",None),("form_shift","DS"),("confirm_delete",None)]:
    if k not in st.session_state:
        st.session_state[k] = v

now_str = datetime.now().strftime("%d %b %Y  |  %H:%M")
st.markdown(f'<div class="wc-header"><h1>🧪 WILDCAT ENTERPRISE — Lab Dashboard</h1><span>{now_str}</span></div>', unsafe_allow_html=True)

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
                </div>
                """, unsafe_allow_html=True)

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
                        if line in db["work_orders"]:
                            del db["work_orders"][line]; save_db(db); st.rerun()
            else:
                st.markdown(f'<div class="line-card empty"><div class="line-title" style="color:#64748b;">⚪ {line}</div><div style="color:#94a3b8;font-style:italic;font-size:.9rem;">No active work order</div></div>', unsafe_allow_html=True)
                if st.button("➕ New Work Order", key=f"new_{line}", use_container_width=True):
                    st.session_state.sel_line=line; st.session_state.wo_action="new"; st.session_state.page="wo_entry"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RECORDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "records":
    line = st.session_state.sel_line
    wo   = get_wo(db, line)
    if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    st.markdown(f"### 📋 Records — **{line}**")
    if wo:
        st.markdown(f'<div style="background:#dbeafe;border-radius:8px;padding:8px 14px;margin:6px 0;font-size:.9rem;"><b>WO:</b> {wo["wo_number"]} | <b>ITEM:</b> {wo["item_code"]} | {wo.get("item_name","")}</div>', unsafe_allow_html=True)
    st.divider()

    all_recs  = load_records()
    line_recs = [r for r in all_recs if r.get("line") == line.replace("L-","")]

    # ── Filters ──────────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        st.markdown("**🔍 Filter**")
        fc1, fc2, fc3, fc4, fc5 = st.columns([2,1.5,1.5,1.5,1.5])
        with fc1:
            wo_filter = st.text_input("WO Number", placeholder="e.g. 2607019", key="f_wo")
        with fc2:
            form_options = ["All"] + sorted(set(r.get("form","") for r in line_recs if r.get("form")))
            form_filter = st.selectbox("Form", form_options, key="f_form")
        with fc3:
            shift_filter = st.selectbox("Shift", ["All","DS","NS"], key="f_shift")
        with fc4:
            date_from = st.date_input("From", value=None, key="f_from")
        with fc5:
            date_to = st.date_input("To", value=None, key="f_to")
        st.markdown('</div>', unsafe_allow_html=True)

    # Apply filters
    filtered = line_recs
    if wo_filter:
        filtered = [r for r in filtered if wo_filter.lower() in r.get("wo","").lower()]
    if form_filter != "All":
        filtered = [r for r in filtered if r.get("form","") == form_filter]
    if shift_filter != "All":
        filtered = [r for r in filtered if r.get("shift","") == shift_filter]
    if date_from:
        filtered = [r for r in filtered if r.get("date","") >= str(date_from)]
    if date_to:
        filtered = [r for r in filtered if r.get("date","") <= str(date_to)]

    st.markdown(f"**{len(filtered)} record(s) found**")
    st.divider()

    if not filtered:
        st.info("No records match the filter.")
    else:
        # Confirm delete dialog
        if st.session_state.confirm_delete:
            rid = st.session_state.confirm_delete
            st.error(f"⚠️ Are you sure you want to delete this record? This cannot be undone.")
            cd1, cd2 = st.columns(2)
            with cd1:
                if st.button("🗑️ Yes, Delete", use_container_width=True, type="primary"):
                    delete_record(rid)
                    st.session_state.confirm_delete = None
                    st.success("Record deleted.")
                    st.rerun()
            with cd2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_delete = None
                    st.rerun()
            st.divider()

        dates = sorted(set(r.get("date","") for r in filtered), reverse=True)
        for d in dates:
            day_recs = [r for r in filtered if r.get("date")==d]
            with st.expander(f"📅 {d}  —  {len(day_recs)} record(s)", expanded=(d==str(date.today()))):
                for r in sorted(day_recs, key=lambda x: x.get("time","")):
                    edited   = " ✏️" if r.get("edited_at") else ""
                    form_code = r.get("form","?")
                    form_name = FORM_NAMES.get(form_code, form_code)
                    rid = r.get("id","")

                    c1,c2,c3,c4,c5,c6 = st.columns([0.8,0.8,1.2,1.5,3,2])
                    with c1: st.markdown(f"**{r.get('shift','?')}**")
                    with c2: st.markdown(f"🕐 {r.get('time','?')}")
                    with c3: st.markdown(f"WO: {r.get('wo','?')}")
                    with c4: st.markdown(f"📋 `{form_code}`")
                    with c5: st.markdown(f"{r.get('operator','?')}{edited}")
                    with c6:
                        e1, e2 = st.columns(2)
                        with e1:
                            if rid and st.button("✏️ Edit", key=f"edit_{rid}", use_container_width=True):
                                st.session_state.edit_record_id=rid
                                st.session_state.sel_line=line
                                st.session_state.page="form_wcfqc05"
                                st.rerun()
                        with e2:
                            if rid and st.button("🗑️ Del", key=f"del_{rid}", use_container_width=True):
                                st.session_state.confirm_delete = rid
                                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# WO ENTRY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "wo_entry":
    line=st.session_state.sel_line; action=st.session_state.wo_action; existing=get_wo(db,line)
    if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    st.markdown(f"### {'🔄 Change' if action=='change' else '➕ New'} Work Order — **{line}**")
    st.divider()

    # Dynamic color count outside form
    prev_n = existing["color_count"] if existing else 3
    n_colors = st.selectbox("Number of Colors *", [1,2,3,4], index=prev_n-1, key="wo_ncolors")

    with st.form("wo_form"):
        c1,c2 = st.columns(2)
        with c1:
            wo_num  = st.text_input("Work Order No *", value=existing["wo_number"] if existing else "")
            item_cd = st.text_input("Item Code *",     value=existing["item_code"]  if existing else "")
        with c2:
            item_nm = st.text_input("Item Name / Description", value=existing.get("item_name","") if existing else "")

        color_defaults = {
            1: ["WHITE","","",""],
            2: ["FIELD GREEN","OLIVE GREEN","",""],
            3: ["FIELD GREEN","APPLE GREEN","OLIVE GREEN",""],
            4: ["FIELD GREEN","APPLE GREEN","OLIVE GREEN","LIME GREEN"]
        }
        prev_colors = existing.get("colors",[]) if existing else []
        defaults    = color_defaults[n_colors]

        st.markdown(f"**Color Names** ({n_colors} color{'s' if n_colors>1 else ''})")
        ccols = st.columns(4)
        colors_in = []
        for idx in range(4):
            default = prev_colors[idx] if idx < len(prev_colors) else defaults[idx]
            with ccols[idx]:
                val = st.text_input(
                    f"Color {idx+1}" if idx < n_colors else f"Color {idx+1} (unused)",
                    value=default if idx < n_colors else "",
                    key=f"ci_{idx}",
                    disabled=(idx >= n_colors)
                )
                colors_in.append(val if idx < n_colors else "")

        if st.form_submit_button("💾 Save Work Order", use_container_width=True, type="primary"):
            if not wo_num or not item_cd:
                st.error("WO Number and Item Code are required!")
            else:
                final_colors = [c.upper() for c in colors_in[:n_colors] if c]
                db["work_orders"][line] = {
                    "wo_number":   wo_num,
                    "item_code":   item_cd,
                    "item_name":   item_nm,
                    "color_count": n_colors,
                    "colors":      final_colors,
                    "created_at":  datetime.now().isoformat()
                }
                save_db(db)
                st.success(f"✅ Saved for {line}!")
                st.session_state.page="dashboard"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FORM SELECTION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "forms":
    line=st.session_state.sel_line; wo=get_wo(db,line)
    if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    st.markdown(f"### 📂 Select Form — **{line}**")
    if wo:
        st.markdown(f'<div style="background:#dbeafe;border-radius:8px;padding:10px 16px;margin:8px 0;font-size:.9rem;"><b>{line}</b> | <b>WO:</b> {wo["wo_number"]} | <b>ITEM:</b> {wo["item_code"]} | {wo.get("item_name","")} | <b>{wo["color_count"]} Color</b> — {" / ".join(wo.get("colors",[]))}</div>', unsafe_allow_html=True)
    shift_sel = st.radio("Shift", ["DS","NS"], horizontal=True)
    st.session_state.form_shift = shift_sel
    st.divider()
    for form in FORMS:
        c1,c2,c3 = st.columns([1.4,5,1.4])
        with c1: st.markdown(f"**{form['code']}**")
        with c2: st.markdown(form['name'])
        with c3:
            impl = form['code'] in IMPLEMENTED
            if st.button("▶ Open", key=f"f_{form['code']}", use_container_width=True,
                         type="primary" if impl else "secondary", disabled=not impl):
                st.session_state.edit_record_id=None
                st.session_state.page=f"form_{form['code'].replace('-','').lower()}"
                st.rerun()
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
            if r.get("id") == edit_id:
                existing_rec = r; break
    is_edit = existing_rec is not None

    back_page = "records" if is_edit else "forms"
    if st.button(f"← Back to {'Records' if is_edit else 'Forms'}"):
        st.session_state.page=back_page; st.rerun()

    if not wo and not existing_rec: st.error("No active WO!"); st.stop()
    if not wo and existing_rec:
        wo = {"wo_number":existing_rec.get("wo",""),"item_code":existing_rec.get("item",""),
              "item_name":existing_rec.get("item_name",""),"color_count":len(existing_rec.get("colors",[])),
              "colors":existing_rec.get("colors",[])}

    colors      = wo.get("colors",[])
    color_count = wo["color_count"]

    def gv(path, default=None):
        if not existing_rec: return default
        keys = path.split("."); v = existing_rec
        for k in keys:
            if isinstance(v, dict): v = v.get(k, default)
            else: return default
        return v if v is not None else default

    if is_edit:
        st.markdown(f'<div class="edit-banner">✏️ EDITING — {existing_rec.get("date","")} | {existing_rec.get("shift","")} | {existing_rec.get("time","")} | {existing_rec.get("operator","")}</div>', unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;border:2px solid #334155;border-radius:6px;overflow:hidden;margin-bottom:14px;"><div style="background:#1a3a5c;color:white;padding:10px;font-size:1.05rem;font-weight:bold;">🏭 WILDCAT ENTERPRISE TEXTILES INDUSTRIES</div><div style="background:#2563a8;color:white;padding:5px;font-size:.88rem;">WC-F-QC-05 Mono Yarn Full Inspection Form &nbsp;|&nbsp; Rev.00 &nbsp;|&nbsp; Date: 02-Jan-2025</div></div>', unsafe_allow_html=True)

    h1,h2,h3,h4 = st.columns([1,1,2,1])
    with h1: line_v = st.text_input("LINE", value=gv("line", line.replace("L-","")))
    with h2:
        shift_opts = ["DS","NS"]; sd = gv("shift", st.session_state.form_shift)
        shift_v = st.selectbox("SHIFT", shift_opts, index=shift_opts.index(sd) if sd in shift_opts else 0)
    with h3:
        try: date_obj = date.fromisoformat(gv("date", str(date.today())))
        except: date_obj = date.today()
        date_v = st.date_input("DATE", value=date_obj)
    with h4: time_v = st.text_input("TIME", value=gv("time", datetime.now().strftime("%H:%M")))

    h5,h6,h7 = st.columns([2,1,2])
    with h5: st.text_input("WO",        value=wo["wo_number"],        disabled=True)
    with h6: st.text_input("ITEM",      value=wo["item_code"],         disabled=True)
    with h7: st.text_input("ITEM NAME", value=wo.get("item_name",""), disabled=True)
    opr_v = st.text_input("OPERATOR", value=gv("operator",""), placeholder="Name Surname")
    st.divider()

    st.markdown("#### 📍 Positions")
    saved_pos = gv("positions", [str((i+1)*3) for i in range(5)])
    n_pos = st.number_input("Number of positions", min_value=1, max_value=10,
                             value=len(saved_pos) if saved_pos else 5, step=1)
    n_pos = int(n_pos); pcols = st.columns(n_pos); positions = []
    for i in range(n_pos):
        dp = saved_pos[i] if i < len(saved_pos) else str((i+1)*3)
        with pcols[i]: positions.append(st.text_input(f"Pos {i+1}", value=dp, key=f"p_{i}"))
    st.divider()

    st.markdown("#### 🧪 Test Results")
    all_data = {}

    for pi in range(n_pos):
        pos = positions[pi]; plabel = pos or f"Pos {pi+1}"
        saved_d = gv(f"test_data.{plabel}", {})

        def sv(test, color, sd=saved_d):
            v = sd.get(test,{})
            return v.get(color, None) if isinstance(v,dict) else None

        with st.expander(f"📌 Position: {plabel}", expanded=(pi==0)):
            pd_ = {}

            st.markdown("<div class='section-lbl'>DTEX</div>", unsafe_allow_html=True)
            dtex_v = {}; dc = st.columns(color_count)
            for ci,color in enumerate(colors):
                with dc[ci]: dtex_v[color] = st.number_input(color, value=sv("dtex",color), format="%.1f", key=f"dtex_{pi}_{ci}")
            pd_["dtex"] = dtex_v

            st.markdown("<div class='section-lbl'>TOTAL DTEX (manual)</div>", unsafe_allow_html=True)
            pd_["total_dtex"] = st.number_input("Total Dtex", value=saved_d.get("total_dtex",None), format="%.1f", key=f"total_dtex_{pi}")

            left,right = st.columns(2)
            with left:
                st.markdown("<div class='section-lbl'>BOILING SHRINKAGE (AVE)</div>", unsafe_allow_html=True)
                bs_v = {}
                for ci,color in enumerate(colors): bs_v[color] = st.number_input(color, value=sv("boiling_shrinkage",color), format="%.1f", key=f"bs_{pi}_{ci}")
                pd_["boiling_shrinkage"] = bs_v

                st.markdown("<div class='section-lbl'>THICKNESS</div>", unsafe_allow_html=True)
                th_v = {}
                for ci,color in enumerate(colors): th_v[color] = st.number_input(color, value=sv("thickness",color), format="%.0f", key=f"th_{pi}_{ci}")
                pd_["thickness"] = th_v

                st.markdown("<div class='section-lbl'>TENSILE (AVE)</div>", unsafe_allow_html=True)
                te_v = {}
                for ci,color in enumerate(colors): te_v[color] = st.number_input(color, value=sv("tensile",color), format="%.1f", key=f"te_{pi}_{ci}")
                pd_["tensile"] = te_v

            with right:
                st.markdown("<div class='section-lbl'>YARN WRAP PER METER</div>", unsafe_allow_html=True)
                pd_["yarn_wrap"] = st.number_input("Value", value=saved_d.get("yarn_wrap",None), format="%.0f", key=f"yw_{pi}")

                st.markdown("<div class='section-lbl'>AIR SHRINKAGE</div>", unsafe_allow_html=True)
                as_v = {}
                for ci,color in enumerate(colors): as_v[color] = st.number_input(color, value=sv("air_shrinkage",color), format="%.1f", key=f"as_{pi}_{ci}")
                pd_["air_shrinkage"] = as_v

                st.markdown("<div class='section-lbl'>WIDTH</div>", unsafe_allow_html=True)
                wi_v = {}
                for ci,color in enumerate(colors): wi_v[color] = st.number_input(color, value=sv("width",color), format="%.2f", key=f"wi_{pi}_{ci}")
                pd_["width"] = wi_v

                st.markdown("<div class='section-lbl'>ELONGATION (AVE)</div>", unsafe_allow_html=True)
                el_v = {}
                for ci,color in enumerate(colors): el_v[color] = st.number_input(color, value=sv("elongation",color), format="%.1f", key=f"el_{pi}_{ci}")
                pd_["elongation"] = el_v

            all_data[plabel] = pd_

    st.divider()
    st.markdown("#### 🔬 SCI / SCE")
    saved_sci = gv("sci",{}); spool_no = st.text_input("Spool #", value=gv("spool_no",""), placeholder="e.g. 01143")
    sci_data = {}; sc = st.columns(color_count)
    for ci,color in enumerate(colors):
        with sc[ci]:
            st.markdown(f"**{color}**")
            sci_data[color] = st.text_input("SCI/SCE", value=saved_sci.get(color,""), placeholder="0.51/0.31", key=f"sci_{ci}")

    st.divider()
    st.markdown('<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 16px;margin-bottom:10px;"><b>TOLERANCE VALUE CHECK</b><br><span style="font-size:.82rem;color:#64748b;">All the tests are conducted in accordance with standard procedure. The results have been verified for accuracy, compliance, and are with the specified tolerance limits.</span></div>', unsafe_allow_html=True)
    verified_v = st.text_input("✅ Verified by", value=gv("verified_by",""), placeholder="Name Surname")

    st.divider()
    if st.button("💾 UPDATE RECORD" if is_edit else "💾 SAVE RECORD", use_container_width=True, type="primary"):
        if not opr_v: st.error("Please enter Operator name!"); st.stop()
        if not verified_v: st.error("Please enter Verified by!"); st.stop()
        record = {
            "form":"WC-F-QC-05", "saved_at":datetime.now().isoformat(),
            "line":line_v, "shift":shift_v, "date":str(date_v), "time":time_v,
            "wo":wo["wo_number"], "item":wo["item_code"], "item_name":wo.get("item_name",""),
            "operator":opr_v, "verified_by":verified_v,
            "colors":colors, "positions":positions,
            "test_data":all_data, "sci":sci_data, "spool_no":spool_no,
        }
        if is_edit:
            update_record(edit_id, record); st.success("✅ Record updated!")
        else:
            add_record(record); st.success("✅ Record saved!"); st.balloons()
