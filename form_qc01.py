"""
WC-F-QC-01: 100% FIB Slit Verification Form
64 positions: Die 2 (pos 1-32) left, Die 1 (pos 33-64) right
Auto-calculates AVG for each die and Total Average.
"""
import streamlit as st
from datetime import datetime, date

def render_qc01(wo, line, existing_rec=None, is_edit=False):
    def gv(key, default=None):
        if not existing_rec: return default
        d = existing_rec.get("data", {})
        return d.get(key, default)

    st.markdown("""
    <div style="text-align:center;border:2px solid #334155;border-radius:6px;overflow:hidden;margin-bottom:14px;">
        <div style="background:#1a3a5c;color:white;padding:10px;font-size:1.05rem;font-weight:bold;">
            🏭 WILDCAT ENTERPRISE TEXTILES INDUSTRIES
        </div>
        <div style="background:#2563a8;color:white;padding:5px;font-size:.88rem;">
            WC-F-QC-01 &nbsp;|&nbsp; 100% FIB Slit Verification Form &nbsp;|&nbsp; Rev.00 &nbsp;|&nbsp; Date: 02-Jan-2025
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Header
    h1,h2,h3,h4 = st.columns([1,1,2,1])
    with h1: line_v  = st.text_input("LINE",  value=existing_rec.get("line","") if existing_rec else line.replace("L-",""), key="qc01_line")
    with h2:
        shift_opts = ["DS","NS"]
        sd = existing_rec.get("shift","DS") if existing_rec else "DS"
        shift_v = st.selectbox("SHIFT", shift_opts, index=shift_opts.index(sd) if sd in shift_opts else 0, key="qc01_shift")
    with h3:
        try: date_obj = date.fromisoformat(existing_rec.get("date", str(date.today())) if existing_rec else str(date.today()))
        except: date_obj = date.today()
        date_v = st.date_input("DATE", value=date_obj, key="qc01_date")
    with h4: time_v = st.text_input("TIME", value=existing_rec.get("time", datetime.now().strftime("%H:%M")) if existing_rec else datetime.now().strftime("%H:%M"), key="qc01_time")

    h5,h6,h7 = st.columns([2,1,2])
    with h5: st.text_input("WO",        value=wo["wo_number"],        disabled=True, key="qc01_wo")
    with h6: st.text_input("ITEM",      value=wo["item_code"],         disabled=True, key="qc01_item")
    with h7: st.text_input("ITEM NAME", value=wo.get("item_name",""), disabled=True, key="qc01_iname")

    opr_v = st.text_input("OPERATOR", value=existing_rec.get("operator","") if existing_rec else st.session_state.get("current_user",""), placeholder="Name Surname", key="qc01_opr")
    st.divider()

    # Load saved values
    saved = gv("positions", {})  # {"die2": {1: val, ...}, "die1": {33: val, ...}}
    die2_saved = saved.get("die2", {}) if saved else {}
    die1_saved = saved.get("die1", {}) if saved else {}

    st.markdown("#### 📊 DTEX Measurements")
    st.caption("DIE 2: Positions 1–32 (left) &nbsp;|&nbsp; DIE 1: Positions 33–64 (right)")

    die2_vals = {}
    die1_vals = {}

    # 32 rows, 2 dies side by side
    col_headers = st.columns([1, 2, 0.5, 1, 2])
    with col_headers[0]: st.markdown("**Pos (Die 2)**")
    with col_headers[1]: st.markdown("**DTEX**")
    with col_headers[2]: st.markdown("")
    with col_headers[3]: st.markdown("**Pos (Die 1)**")
    with col_headers[4]: st.markdown("**DTEX**")

    for i in range(1, 33):
        pos_die2 = i
        pos_die1 = i + 32
        c1,c2,c3,c4,c5 = st.columns([1,2,0.3,1,2])
        with c1: st.markdown(f"<div style='padding-top:8px;font-weight:600;color:#475569;'>{pos_die2}</div>", unsafe_allow_html=True)
        with c2:
            saved_val = die2_saved.get(str(pos_die2))
            die2_vals[pos_die2] = st.number_input(
                f"d2_{pos_die2}", value=float(saved_val) if saved_val else None,
                format="%.1f", label_visibility="collapsed", key=f"qc01_d2_{pos_die2}"
            )
        with c3: st.markdown("<div style='padding-top:8px;text-align:center;color:#cbd5e1;'>│</div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div style='padding-top:8px;font-weight:600;color:#475569;'>{pos_die1}</div>", unsafe_allow_html=True)
        with c5:
            saved_val = die1_saved.get(str(pos_die1))
            die1_vals[pos_die1] = st.number_input(
                f"d1_{pos_die1}", value=float(saved_val) if saved_val else None,
                format="%.1f", label_visibility="collapsed", key=f"qc01_d1_{pos_die1}"
            )

    # Auto AVG
    die2_filled = [v for v in die2_vals.values() if v is not None and v > 0]
    die1_filled = [v for v in die1_vals.values() if v is not None and v > 0]
    die2_avg = sum(die2_filled)/len(die2_filled) if die2_filled else 0
    die1_avg = sum(die1_filled)/len(die1_filled) if die1_filled else 0
    total_avg = (die2_avg + die1_avg) / 2 if die2_avg and die1_avg else (die2_avg or die1_avg)

    st.divider()
    a1,a2,a3 = st.columns(3)
    with a1: st.metric("DIE 2 AVG (dtex)", f"{die2_avg:.1f}" if die2_avg else "-")
    with a2: st.metric("DIE 1 AVG (dtex)", f"{die1_avg:.1f}" if die1_avg else "-")
    with a3: st.metric("TOTAL AVG (dtex)", f"{total_avg:.1f}" if total_avg else "-")

    # Comments
    st.divider()
    st.markdown("#### 💬 Comments")
    comments_v = st.text_area("Notes...", value=existing_rec.get("comments","") if existing_rec else "", height=80, key="qc01_comments")

    # Verified by
    st.divider()
    st.markdown('<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px 14px;margin-bottom:10px;"><b>TOLERANCE VALUE CHECK</b><br><span style="font-size:.82rem;color:#64748b;">All tests conducted per standard procedure.</span></div>', unsafe_allow_html=True)
    verified_v = st.text_input("✅ Verified by", value=existing_rec.get("verified_by","") if existing_rec else "", key="qc01_verified")

    return {
        "line_v": line_v, "shift_v": shift_v, "date_v": str(date_v),
        "time_v": time_v, "opr_v": opr_v, "verified_v": verified_v,
        "comments_v": comments_v,
        "data": {
            "positions": {
                "die2": {str(k): v for k,v in die2_vals.items() if v},
                "die1": {str(k): v for k,v in die1_vals.items() if v},
            },
            "averages": {
                "die2_avg": round(die2_avg, 2),
                "die1_avg": round(die1_avg, 2),
                "total_avg": round(total_avg, 2),
            }
        }
    }
