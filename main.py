import streamlit as st
import json, os, mimetypes
from datetime import datetime, date
from pathlib import Path

st.set_page_config(page_title="WC Lab Dashboard", layout="wide", page_icon="🧪")

# ── Init DB ───────────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, "/root/lab")
try:
    from database import (
        init_db, get_work_order, get_all_work_orders, save_work_order, delete_work_order,
        add_record, update_record, delete_record, get_record, get_records, get_records_for_today,
        save_media, get_media, delete_media, get_media_path,
        set_presence, clear_presence, get_presence, get_all_presence,
        migrate_from_json
    )
    init_db()
except ImportError:
    st.error("Database module not found. Please ensure database.py is in /root/lab/")
    st.stop()

LINES = ["L-03", "L-05", "L-06", "L-07"]

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
FORM_NAMES  = {f["code"]: f["name"] for f in FORMS}
IMPLEMENTED = {"WC-F-QC-05", "WC-F-QC-01", "WC-F-QC-02"}

UNITS = {
    "dtex":"dtex","total_dtex":"dtex","boiling_shrinkage":"%","thickness":"µm",
    "tensile":"N","yarn_wrap":"wraps/m","air_shrinkage":"%","width":"mm","elongation":"%",
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.wc-header {
    background:linear-gradient(90deg,#1a3a5c,#2563a8);
    color:white; padding:16px 24px; border-radius:10px;
    display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;
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
div[data-testid="stNumberInput"] button[aria-label="Clear value"] { display:none !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("page","dashboard"),("sel_line",None),("wo_action",None),
             ("edit_record_id",None),("form_shift","DS"),("confirm_delete",None),
             ("current_user",""),("last_saved_id",None),("active_form",None)]:
    if k not in st.session_state: st.session_state[k] = v

# ── Header + top bar ──────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%d %b %Y  |  %H:%M")
st.markdown(f'<div class="wc-header"><h1>🧪 WILDCAT ENTERPRISE — Lab Dashboard</h1><span>{now_str}</span></div>', unsafe_allow_html=True)

tb1, tb2 = st.columns([4, 1])
with tb1:
    tc1, tc2 = st.columns([2,2])
    with tc1:
        user_input = st.text_input("👤", value=st.session_state.current_user,
                                    placeholder="Your name", key="user_input", label_visibility="collapsed")
        if user_input != st.session_state.current_user:
            st.session_state.current_user = user_input
    with tc2:
        st.markdown(f"<div style='padding-top:8px;color:#475569;font-size:.88rem;'>👤 <b>{st.session_state.current_user or 'Enter name →'}</b></div>", unsafe_allow_html=True)
with tb2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page="dashboard"; st.rerun()

page = st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
# HELPER: save/update record from form result
# ══════════════════════════════════════════════════════════════════════════════
def handle_save(form_code, result, wo, line, edit_id, is_edit, photo_uploads=None):
    if not result["opr_v"]:    st.error("Please enter Operator name!"); return False
    if not result["verified_v"]: st.error("Please enter Verified by!"); return False
    colors = wo.get("colors",[])
    if is_edit:
        update_record(edit_id,
            operator=result["opr_v"], verified_by=result["verified_v"],
            colors=colors, data=result["data"], comments=result["comments_v"],
            shift=result["shift_v"], date=result["date_v"],
            time_val=result["time_v"], line=result["line_v"].replace("L-",""))
        if photo_uploads:
            for uf in photo_uploads: save_media(edit_id,"photo",uf,wo["wo_number"])
        clear_presence(edit_id, st.session_state.current_user)
        st.success("✅ Record updated!")
        return True
    else:
        new_id = add_record(
            form_code=form_code,
            line=result["line_v"].replace("L-",""),
            wo=wo, shift=result["shift_v"],
            date=result["date_v"], time_val=result["time_v"],
            operator=result["opr_v"], verified_by=result["verified_v"],
            colors=colors, data=result["data"], comments=result["comments_v"])
        st.session_state.last_saved_id=new_id
        st.session_state.edit_record_id=new_id
        if photo_uploads:
            for uf in photo_uploads: save_media(new_id,"photo",uf,wo["wo_number"])
        st.success("✅ Record saved!"); st.balloons()
        return True

# ══════════════════════════════════════════════════════════════════════════════
# MEDIA SECTION (shared)
# ══════════════════════════════════════════════════════════════════════════════
def render_media_section(record_id, wo):
    if not record_id: return
    st.divider()
    st.markdown("#### 📁 Media & Documents")
    st.caption("File saved as: **TYPE_WORKORDER_datetime.ext**")
    ATTACH_TYPES = {"📷 Photo":"photo","🔬 Spectro":"spectro","📋 Protocol":"protocol",
                    "📄 TXT Photo":"txt_photo","📊 Lab Report":"lab_report","📁 Other":"other"}
    a1,a2 = st.columns([2,4])
    with a1: mt_label=st.selectbox("Attachment Type",list(ATTACH_TYPES.keys()),key="mt_sel"); mt_sel=ATTACH_TYPES[mt_label]
    with a2: doc_upload=st.file_uploader("Select file",type=["jpg","jpeg","png","pdf","txt","xlsx","docx","webp"],key="doc_upload")
    if doc_upload:
        preview=f"{mt_sel}_{wo['wo_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{Path(doc_upload.name).suffix}"
        st.caption(f"Will be saved as: `{preview}`")
        if st.button("📎 Attach File",use_container_width=True,type="primary"):
            fname=save_media(record_id,mt_sel,doc_upload,wo["wo_number"])
            st.success(f"✅ {fname}"); st.rerun()
    existing_files=get_media(record_id)
    if existing_files:
        st.markdown(f"**{len(existing_files)} file(s) attached:**")
        for fm in existing_files:
            fname=fm["filename"]; fpath=get_media_path(record_id,fname)
            if not os.path.exists(fpath): continue
            fsize=os.path.getsize(fpath)
            with open(fpath,"rb") as f: fdata=f.read()
            mime=mimetypes.guess_type(fpath)[0] or "application/octet-stream"
            fc1,fc2,fc3=st.columns([5,1.5,1.5])
            with fc1: st.markdown(f"📄 `{fname}` &nbsp;<span style='color:#94a3b8;font-size:.8rem;'>{fsize//1024} KB</span>",unsafe_allow_html=True)
            with fc2: st.download_button("⬇️ Download",data=fdata,file_name=fname,mime=mime,key=f"dl_{fname}",use_container_width=True)
            with fc3:
                if st.button("🗑️ Delete",key=f"delmedia_{fname}",use_container_width=True):
                    if st.session_state.get(f"confirm_media_{fname}"):
                        delete_media(record_id,fname)
                        del st.session_state[f"confirm_media_{fname}"]; st.rerun()
                    else:
                        st.session_state[f"confirm_media_{fname}"]=True; st.rerun()
            if st.session_state.get(f"confirm_media_{fname}"):
                st.warning(f"Delete `{fname}`? Click Delete again to confirm.")

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    st.markdown("### 📋 Active Work Orders")
    today = str(date.today())
    cols  = st.columns(2)
    for i, line in enumerate(LINES):
        wo = get_work_order(line)
        with cols[i % 2]:
            if wo:
                colors_str  = " / ".join(wo.get("colors",[]))
                day_records = get_records_for_today(line, wo["wo_number"], today)
                shift_html  = ""
                for shift in ["DS","NS"]:
                    recs = day_records[shift]
                    shift_html += f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;flex-wrap:wrap;"><span style="font-weight:700;font-size:.85rem;color:#475569;min-width:28px;">{shift}:</span>'
                    if recs:
                        for r in recs:
                            t  = r.get("time","??:??")
                            fc = r.get("form_code","?")
                            shift_html += f'<span style="background:#e0f2fe;color:#0369a1;border-radius:20px;padding:3px 12px;font-size:.78rem;font-weight:600;border:1px solid #bae6fd;">🕐 {t} <span style="opacity:.7">{fc}</span></span> '
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
                        delete_work_order(line); st.rerun()
            else:
                st.markdown(f'<div class="line-card empty"><div class="line-title" style="color:#64748b;">⚪ {line}</div><div style="color:#94a3b8;font-style:italic;font-size:.9rem;">No active work order</div></div>', unsafe_allow_html=True)
                if st.button("➕ New Work Order", key=f"new_{line}", use_container_width=True):
                    st.session_state.sel_line=line; st.session_state.wo_action="new"; st.session_state.page="wo_entry"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RECORDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "records":
    line = st.session_state.sel_line
    wo   = get_work_order(line)
    if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    st.markdown(f"### 📋 Records — **{line}**")
    if wo:
        st.markdown(f'<div style="background:#dbeafe;border-radius:8px;padding:8px 14px;margin:6px 0;font-size:.9rem;"><b>WO:</b> {wo["wo_number"]} | <b>ITEM:</b> {wo["item_code"]} | {wo.get("item_name","")}</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**🔍 Filter**")
    fc1,fc2,fc3,fc4,fc5 = st.columns([2,1.5,1.5,1.5,1.5])
    with fc1: wo_filter    = st.text_input("WO Number", placeholder="e.g. 2607019", key="f_wo")
    with fc2: form_filter  = st.selectbox("Form", ["All"]+[f["code"] for f in FORMS], key="f_form")
    with fc3: shift_filter = st.selectbox("Shift", ["All","DS","NS"], key="f_shift")
    with fc4: date_from    = st.date_input("From", value=None, key="f_from")
    with fc5: date_to      = st.date_input("To",   value=None, key="f_to")

    filtered = get_records(
        line=line,
        wo_number=wo_filter if wo_filter else None,
        form_code=form_filter if form_filter != "All" else None,
        shift=shift_filter if shift_filter != "All" else None,
        date_from=str(date_from) if date_from else None,
        date_to=str(date_to) if date_to else None,
    )

    st.markdown(f"**{len(filtered)} record(s) found**")
    st.divider()

    all_presence = get_all_presence()

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
                    form_code = r.get("form_code","?")
                    rid       = r.get("id","")
                    media_cnt = len(get_media(rid)) if rid else 0
                    media_str = f" 📎{media_cnt}" if media_cnt else ""
                    presence  = all_presence.get(rid)
                    pres_html = f'<span class="presence-badge">👁️ {presence["username"]}</span>' if presence and presence.get("username") != st.session_state.current_user else ""

                    c1,c2,c3,c4,c5,c6 = st.columns([0.8,0.8,1.2,1.5,3.5,2])
                    with c1: st.markdown(f"**{r.get('shift','?')}**")
                    with c2: st.markdown(f"🕐 {r.get('time','?')}")
                    with c3: st.markdown(f"WO: {r.get('wo_number','?')}")
                    with c4: st.markdown(f"📋 `{form_code}`")
                    with c5: st.markdown(f"{r.get('operator','?')}{edited}{media_str} {pres_html}", unsafe_allow_html=True)
                    with c6:
                        e1,e2 = st.columns(2)
                        with e1:
                            if rid and st.button("✏️ Edit", key=f"edit_{rid}", use_container_width=True):
                                st.session_state.edit_record_id=rid
                                st.session_state.active_form=form_code
                                st.session_state.sel_line=line
                                page_map = {"WC-F-QC-05":"form_wcfqc05","WC-F-QC-01":"form_wcfqc01","WC-F-QC-02":"form_wcfqc02"}
                                st.session_state.page=page_map.get(form_code,"form_wcfqc05"); st.rerun()
                        with e2:
                            if rid and st.button("🗑️ Del", key=f"del_{rid}", use_container_width=True):
                                st.session_state.confirm_delete=rid; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# WO ENTRY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "wo_entry":
    line=st.session_state.sel_line; action=st.session_state.wo_action; existing=get_work_order(line)
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
                save_work_order(line, {"wo_number":wo_num,"item_code":item_cd,"item_name":item_nm,
                    "color_count":n_colors,"colors":[c.upper() for c in colors_in[:n_colors] if c],
                    "created_at":datetime.now().isoformat()})
                st.success(f"✅ Saved for {line}!"); st.session_state.page="dashboard"; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# FORM SELECTION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "forms":
    line=st.session_state.sel_line; wo=get_work_order(line)
    if st.button("← Dashboard"): st.session_state.page="dashboard"; st.rerun()
    st.markdown(f"### 📂 Select Form — **{line}**")
    if wo:
        st.markdown(f'<div style="background:#dbeafe;border-radius:8px;padding:10px 16px;margin:8px 0;font-size:.9rem;"><b>{line}</b> | <b>WO:</b> {wo["wo_number"]} | <b>ITEM:</b> {wo["item_code"]} | {wo.get("item_name","")} | <b>{wo["color_count"]} Color</b> — {" / ".join(wo.get("colors",[]))}</div>', unsafe_allow_html=True)
    shift_sel=st.radio("Shift",["DS","NS"],horizontal=True)
    st.session_state.form_shift=shift_sel
    st.divider()
    page_map = {"WC-F-QC-05":"form_wcfqc05","WC-F-QC-01":"form_wcfqc01","WC-F-QC-02":"form_wcfqc02"}
    for form in FORMS:
        c1,c2,c3=st.columns([1.4,5,1.4])
        with c1: st.markdown(f"**{form['code']}**")
        with c2: st.markdown(form['name'])
        with c3:
            impl=form['code'] in IMPLEMENTED
            if st.button("▶ Open",key=f"f_{form['code']}",use_container_width=True,
                         type="primary" if impl else "secondary",disabled=not impl):
                st.session_state.edit_record_id=None
                st.session_state.active_form=form['code']
                st.session_state.page=page_map.get(form['code'],"form_wcfqc05"); st.rerun()
        st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# WC-F-QC-01
# ══════════════════════════════════════════════════════════════════════════════
elif page == "form_wcfqc01":
    line=st.session_state.sel_line; wo=get_work_order(line)
    edit_id=st.session_state.edit_record_id
    existing_rec=get_record(edit_id) if edit_id else None
    is_edit=existing_rec is not None
    if is_edit and edit_id: set_presence(edit_id, st.session_state.current_user)
    back_page="records" if is_edit else "forms"
    if st.button(f"← Back to {'Records' if is_edit else 'Forms'}"):
        if edit_id: clear_presence(edit_id, st.session_state.current_user)
        st.session_state.page=back_page; st.rerun()
    if not wo and existing_rec:
        wo={"wo_number":existing_rec.get("wo_number",""),"item_code":existing_rec.get("item_code",""),
            "item_name":existing_rec.get("item_name",""),"color_count":1,"colors":[]}
    if not wo: st.error("No active WO!"); st.stop()
    if is_edit:
        st.markdown(f'<div class="edit-banner">✏️ EDITING — {existing_rec.get("date","")} | {existing_rec.get("shift","")} | {existing_rec.get("time","")} | {existing_rec.get("operator","")}</div>', unsafe_allow_html=True)
    from form_qc01 import render_qc01
    result=render_qc01(wo, line, existing_rec, is_edit)
    photo_uploads=st.file_uploader("📷 Photos",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,key="qc01_photos")
    st.divider()
    if st.button("💾 UPDATE RECORD" if is_edit else "💾 SAVE RECORD",use_container_width=True,type="primary"):
        handle_save("WC-F-QC-01",result,wo,line,edit_id,is_edit,photo_uploads)
    render_media_section(edit_id or st.session_state.last_saved_id, wo)

# ══════════════════════════════════════════════════════════════════════════════
# WC-F-QC-02
# ══════════════════════════════════════════════════════════════════════════════
elif page == "form_wcfqc02":
    line=st.session_state.sel_line; wo=get_work_order(line)
    edit_id=st.session_state.edit_record_id
    existing_rec=get_record(edit_id) if edit_id else None
    is_edit=existing_rec is not None
    if is_edit and edit_id: set_presence(edit_id, st.session_state.current_user)
    back_page="records" if is_edit else "forms"
    if st.button(f"← Back to {'Records' if is_edit else 'Forms'}"):
        if edit_id: clear_presence(edit_id, st.session_state.current_user)
        st.session_state.page=back_page; st.rerun()
    if not wo and existing_rec:
        wo={"wo_number":existing_rec.get("wo_number",""),"item_code":existing_rec.get("item_code",""),
            "item_name":existing_rec.get("item_name",""),"color_count":len(existing_rec.get("colors",[])),
            "colors":existing_rec.get("colors",[])}
    if not wo: st.error("No active WO!"); st.stop()
    if is_edit:
        st.markdown(f'<div class="edit-banner">✏️ EDITING — {existing_rec.get("date","")} | {existing_rec.get("shift","")} | {existing_rec.get("time","")} | {existing_rec.get("operator","")}</div>', unsafe_allow_html=True)
    from form_qc02 import render_qc02
    result=render_qc02(wo, line, existing_rec, is_edit)
    photo_uploads=st.file_uploader("📷 Photos",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,key="qc02_photos")
    st.divider()
    if st.button("💾 UPDATE RECORD" if is_edit else "💾 SAVE RECORD",use_container_width=True,type="primary"):
        handle_save("WC-F-QC-02",result,wo,line,edit_id,is_edit,photo_uploads)
    render_media_section(edit_id or st.session_state.last_saved_id, wo)

# ══════════════════════════════════════════════════════════════════════════════
# WC-F-QC-05
# ══════════════════════════════════════════════════════════════════════════════
elif page == "form_wcfqc05":
    line=st.session_state.sel_line; wo=get_work_order(line)
    edit_id=st.session_state.edit_record_id
    existing_rec=get_record(edit_id) if edit_id else None
    is_edit=existing_rec is not None
    if is_edit and edit_id: set_presence(edit_id, st.session_state.current_user)
    back_page="records" if is_edit else "forms"
    if st.button(f"← Back to {'Records' if is_edit else 'Forms'}"):
        if edit_id: clear_presence(edit_id, st.session_state.current_user)
        st.session_state.page=back_page; st.rerun()
    if not wo and existing_rec:
        wo={"wo_number":existing_rec.get("wo_number",""),"item_code":existing_rec.get("item_code",""),
            "item_name":existing_rec.get("item_name",""),"color_count":len(existing_rec.get("colors",[])),
            "colors":existing_rec.get("colors",[])}
    if not wo: st.error("No active WO!"); st.stop()
    colors=wo.get("colors",[]); color_count=wo["color_count"]

    def gv(path, default=None):
        if not existing_rec: return default
        keys=path.split(".")
        v=existing_rec.get("data",{})
        for k in keys:
            if isinstance(v,dict): v=v.get(k,default)
            else: return default
        return v if v is not None else default

    if is_edit:
        presence=get_presence(edit_id)
        if presence and presence.get("username")!=st.session_state.current_user:
            st.markdown(f'<div style="background:#fef9c3;border:1px solid #fde68a;border-radius:8px;padding:8px 14px;margin-bottom:10px;">👁️ <b>{presence["username"]}</b> is also viewing this record</div>', unsafe_allow_html=True)
        edited_str=f" | Last edited: {existing_rec['edited_at'][:16].replace('T',' ')}" if existing_rec.get('edited_at') else ""
        st.markdown(f'<div class="edit-banner">✏️ EDITING — {existing_rec.get("date","")} | {existing_rec.get("shift","")} | {existing_rec.get("time","")} | {existing_rec.get("operator","")}{edited_str}</div>', unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;border:2px solid #334155;border-radius:6px;overflow:hidden;margin-bottom:14px;"><div style="background:#1a3a5c;color:white;padding:10px;font-size:1.05rem;font-weight:bold;">🏭 WILDCAT ENTERPRISE TEXTILES INDUSTRIES</div><div style="background:#2563a8;color:white;padding:5px;font-size:.88rem;">WC-F-QC-05 Mono Yarn Full Inspection Form &nbsp;|&nbsp; Rev.00 &nbsp;|&nbsp; Date: 02-Jan-2025</div></div>', unsafe_allow_html=True)

    h1,h2,h3,h4=st.columns([1,1,2,1])
    with h1: line_v=st.text_input("LINE",value=existing_rec.get("line","") if existing_rec else line.replace("L-",""))
    with h2:
        shift_opts=["DS","NS"]; sd=existing_rec.get("shift",st.session_state.form_shift) if existing_rec else st.session_state.form_shift
        shift_v=st.selectbox("SHIFT",shift_opts,index=shift_opts.index(sd) if sd in shift_opts else 0)
    with h3:
        try: date_obj=date.fromisoformat(existing_rec.get("date",str(date.today())) if existing_rec else str(date.today()))
        except: date_obj=date.today()
        date_v=st.date_input("DATE",value=date_obj)
    with h4: time_v=st.text_input("TIME",value=existing_rec.get("time",datetime.now().strftime("%H:%M")) if existing_rec else datetime.now().strftime("%H:%M"))
    h5,h6,h7=st.columns([2,1,2])
    with h5: st.text_input("WO",value=wo["wo_number"],disabled=True)
    with h6: st.text_input("ITEM",value=wo["item_code"],disabled=True)
    with h7: st.text_input("ITEM NAME",value=wo.get("item_name",""),disabled=True)
    opr_v=st.text_input("OPERATOR",value=existing_rec.get("operator","") if existing_rec else st.session_state.current_user,placeholder="Name Surname")
    if is_edit:
        st.markdown('<div style="background:#fef9c3;border-radius:8px;padding:6px 12px;margin:6px 0;font-size:.82rem;color:#854d0e;">💡 Fill in all fields below, then click <b>💾 UPDATE RECORD</b> at the bottom.</div>', unsafe_allow_html=True)
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
                for key,label in [("boiling_shrinkage","BOILING SHRINKAGE (AVE)"),("thickness","THICKNESS"),("tensile","TENSILE")]:
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
            sci_data[color]=st.text_input("SCI/SCE",value=saved_sci.get(color,"") if saved_sci else "",placeholder="0.51/0.31",key=f"sci_{ci}")

    st.divider()
    st.markdown('<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 16px;margin-bottom:10px;"><b>TOLERANCE VALUE CHECK</b><br><span style="font-size:.82rem;color:#64748b;">All tests conducted per standard procedure.</span></div>', unsafe_allow_html=True)
    verified_v=st.text_input("✅ Verified by",value=existing_rec.get("verified_by","") if existing_rec else "",placeholder="Name Surname")
    st.divider()
    st.markdown("#### 💬 Comments")
    comments_v=st.text_area("Notes...",value=existing_rec.get("comments","") if existing_rec else "",height=100)
    st.markdown("#### 📷 Photos")
    photo_uploads=st.file_uploader("Upload photos",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,key="photo_upload")

    st.divider()
    if st.button("💾 UPDATE RECORD" if is_edit else "💾 SAVE RECORD",use_container_width=True,type="primary"):
        if not opr_v: st.error("Please enter Operator name!"); st.stop()
        if not verified_v: st.error("Please enter Verified by!"); st.stop()
        form_data={"test_data":all_data,"positions":positions,"sci":sci_data,"spool_no":spool_no}
        if is_edit:
            update_record(edit_id,operator=opr_v,verified_by=verified_v,colors=colors,
                         data=form_data,comments=comments_v,shift=shift_v,date=str(date_v),
                         time_val=time_v,line=line_v.replace("L-",""))
            if photo_uploads:
                for uf in photo_uploads: save_media(edit_id,"photo",uf,wo["wo_number"])
            clear_presence(edit_id,st.session_state.current_user)
            st.success("✅ Record updated!")
        else:
            new_id=add_record("WC-F-QC-05",line_v.replace("L-",""),wo,shift_v,str(date_v),
                              time_v,opr_v,verified_v,colors,form_data,comments_v)
            st.session_state.last_saved_id=new_id; st.session_state.edit_record_id=new_id
            if photo_uploads:
                for uf in photo_uploads: save_media(new_id,"photo",uf,wo["wo_number"])
            st.success("✅ Record saved!"); st.balloons()

    render_media_section(edit_id or st.session_state.last_saved_id, wo)

    if is_edit and existing_rec:
        st.divider()
        st.markdown("#### 📄 Export PDF")
        if st.button("📄 Generate PDF",use_container_width=True):
            try:
                from pdf_export import generate_pdf
                # Build record dict for PDF
                rec_for_pdf = dict(existing_rec)
                rec_for_pdf.update(existing_rec.get("data",{}))
                pdf_bytes=generate_pdf(rec_for_pdf)
                fname=f"{existing_rec.get('wo_number','WO')}_{existing_rec.get('date','date')}_{existing_rec.get('shift','')}_QC05.pdf"
                st.download_button("⬇ Download PDF",data=pdf_bytes,file_name=fname,
                                   mime="application/pdf",key="pdf_dl",use_container_width=True)
            except Exception as e:
                st.error(f"PDF error: {e}")
