"""
WC-F-QC-02: 100% Mono Dtex Verification Form
40 positions fixed, colors from WO (1-4 colors).
Pos 1-20 left, 21-40 right, side by side per color.
Auto-calculates AVG per color and Total AVG.
"""
import streamlit as st
from datetime import datetime, date

def render_qc02(wo, line, existing_rec=None, is_edit=False):
    colors      = wo.get("colors", [])
    color_count = wo.get("color_count", 1)

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
            WC-F-QC-02 &nbsp;|&nbsp; 100% Mono Dtex Verification Form &nbsp;|&nbsp; Rev.00 &nbsp;|&nbsp; Date: 02-Jan-2025
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Header
    h1,h2,h3,h4 = st.columns([1,1,2,1])
    with h1: line_v = st.text_input("LINE", value=existing_rec.get("line","") if existing_rec else line.replace("L-",""), key="qc02_line")
    with h2:
        shift_opts = ["DS","NS"]
        sd = existing_rec.get("shift","DS") if existing_rec else "DS"
        shift_v = st.selectbox("SHIFT", shift_opts, index=shift_opts.index(sd) if sd in shift_opts else 0, key="qc02_shift")
    with h3:
        try: date_obj = date.fromisoformat(existing_rec.get("date", str(date.today())) if existing_rec else str(date.today()))
        except: date_obj = date.today()
        date_v = st.date_input("DATE", value=date_obj, key="qc02_date")
    with h4: time_v = st.text_input("TIME", value=existing_rec.get("time", datetime.now().strftime("%H:%M")) if existing_rec else datetime.now().strftime("%H:%M"), key="qc02_time")

    h5,h6,h7 = st.columns([2,1,2])
    with h5: st.text_input("WO",        value=wo["wo_number"],        disabled=True, key="qc02_wo")
    with h6: st.text_input("ITEM",      value=wo["item_code"],         disabled=True, key="qc02_item")
    with h7: st.text_input("ITEM NAME", value=wo.get("item_name",""), disabled=True, key="qc02_iname")

    opr_v = st.text_input("OPERATOR", value=existing_rec.get("operator","") if existing_rec else st.session_state.get("current_user",""), placeholder="Name Surname", key="qc02_opr")
    st.divider()

    saved_positions = gv("positions", {})
    all_vals = {}  # {color: {pos: val}}

    # One tab per color
    if color_count > 1:
        tabs = st.tabs([f"🎨 {c}" for c in colors])
    else:
        tabs = [st.container()]

    for ci, color in enumerate(colors):
        saved_color = saved_positions.get(color, {}) if saved_positions else {}
        color_vals  = {}

        with tabs[ci]:
            st.markdown(f"#### {color} — DTEX Measurements")
            st.caption("Positions 1–20 (left) | 21–40 (right)")

            hcols = st.columns([1, 2, 0.3, 1, 2])
            with hcols[0]: st.markdown("**Pos**")
            with hcols[1]: st.markdown("**DTEX**")
            with hcols[3]: st.markdown("**Pos**")
            with hcols[4]: st.markdown("**DTEX**")

            for i in range(1, 21):
                pos_l = i
                pos_r = i + 20
                c1,c2,c3,c4,c5 = st.columns([1,2,0.3,1,2])
                with c1: st.markdown(f"<div style='padding-top:8px;font-weight:600;color:#475569;'>{pos_l}</div>", unsafe_allow_html=True)
                with c2:
                    sv = saved_color.get(str(pos_l))
                    color_vals[pos_l] = st.number_input(
                        f"l_{ci}_{pos_l}", value=float(sv) if sv else None,
                        format="%.1f", label_visibility="collapsed",
                        key=f"qc02_{ci}_l_{pos_l}"
                    )
                with c3: st.markdown("<div style='padding-top:8px;text-align:center;color:#cbd5e1;'>│</div>", unsafe_allow_html=True)
                with c4: st.markdown(f"<div style='padding-top:8px;font-weight:600;color:#475569;'>{pos_r}</div>", unsafe_allow_html=True)
                with c5:
                    sv = saved_color.get(str(pos_r))
                    color_vals[pos_r] = st.number_input(
                        f"r_{ci}_{pos_r}", value=float(sv) if sv else None,
                        format="%.1f", label_visibility="collapsed",
                        key=f"qc02_{ci}_r_{pos_r}"
                    )

            filled = [v for v in color_vals.values() if v is not None and v > 0]
            avg    = sum(filled)/len(filled) if filled else 0
            st.metric(f"{color} AVG (dtex)", f"{avg:.1f}" if avg else "-")

        all_vals[color] = {str(k): v for k,v in color_vals.items() if v}

    # Total avg
    all_avgs = []
    for color in colors:
        vals = [v for v in all_vals.get(color,{}).values() if v]
        if vals: all_avgs.append(sum(vals)/len(vals))
    total_avg = sum(all_avgs)/len(all_avgs) if all_avgs else 0

    st.divider()
    st.metric("TOTAL AVERAGE (dtex)", f"{total_avg:.1f}" if total_avg else "-")

    # Comments
    st.divider()
    st.markdown("#### 💬 Comments")
    comments_v = st.text_area("Notes...", value=existing_rec.get("comments","") if existing_rec else "", height=80, key="qc02_comments")

    # Verified
    st.divider()
    st.markdown('<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px 14px;margin-bottom:10px;"><b>TOLERANCE VALUE CHECK</b><br><span style="font-size:.82rem;color:#64748b;">All tests conducted per standard procedure.</span></div>', unsafe_allow_html=True)
    verified_v = st.text_input("✅ Verified by", value=existing_rec.get("verified_by","") if existing_rec else "", key="qc02_verified")

    per_color_avgs = {}
    for color in colors:
        vals = [v for v in all_vals.get(color,{}).values() if v]
        per_color_avgs[color] = round(sum(vals)/len(vals), 2) if vals else 0

    return {
        "line_v": line_v, "shift_v": shift_v, "date_v": str(date_v),
        "time_v": time_v, "opr_v": opr_v, "verified_v": verified_v,
        "comments_v": comments_v,
        "data": {
            "positions":      all_vals,
            "per_color_avgs": per_color_avgs,
            "total_avg":      round(total_avg, 2),
        }
    }
