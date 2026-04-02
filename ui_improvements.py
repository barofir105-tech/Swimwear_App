import sys

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# ==============================================================
# CHANGE 1: Navbar keys + Active State CSS
# ==============================================================

old_nav = (
    'with col2:\n'
    '    if st.button("\U0001f9f5 \u05de\u05dc\u05d0\u05d9", use_container_width=True): st.session_state.current_view = "\u05de\u05dc\u05d0\u05d9"; st.rerun()\n'
    'with col3:\n'
    '    if st.button("\u2702\ufe0f \u05d2\u05d6\u05e8\u05d5\u05ea", use_container_width=True): st.session_state.current_view = "\u05d2\u05d6\u05e8\u05d5\u05ea"; st.rerun()\n'
    'with col4:\n'
    '    if st.button("\U0001f4b0 \u05e4\u05d9\u05e0\u05e0\u05e1\u05d9", use_container_width=True): st.session_state.current_view = "\u05e4\u05d9\u05e0\u05e0\u05e1\u05d9"; st.rerun()\n'
    'with col5:\n'
    '    if st.button("\U0001f465 \u05dc\u05e7\u05d5\u05d7\u05d5\u05ea", use_container_width=True): st.session_state.current_view = "\u05dc\u05e7\u05d5\u05d7\u05d5\u05ea"; st.rerun()\n'
    'with col6:\n'
    '    if st.button("\U0001f4e6 \u05d4\u05d6\u05de\u05e0\u05d5\u05ea", use_container_width=True): st.session_state.current_view = "\u05d4\u05d6\u05de\u05e0\u05d5\u05ea"; st.rerun()\n'
    'with col7:\n'
    '    if st.button("\U0001f504 \u05e8\u05e2\u05e0\u05d5\u05df \u05e0\u05ea\u05d5\u05e0\u05d9\u05dd", use_container_width=True): st.session_state.data_loaded = False; st.rerun()'
)

if old_nav in text:
    new_nav = (
        '# --- Active nav state CSS injection ---\n'
        '_view_nav_map = {\n'
        '    "\u05de\u05dc\u05d0\u05d9": "nav_inv", "\u05d2\u05d6\u05e8\u05d5\u05ea": "nav_pat", "\u05e4\u05d9\u05e0\u05e0\u05e1\u05d9": "nav_fin",\n'
        '    "\u05dc\u05e7\u05d5\u05d7\u05d5\u05ea": "nav_cust", "\u05db\u05e8\u05d8\u05d9\u05e1_\u05dc\u05e7\u05d5\u05d7\u05d4": "nav_cust", "\u05d4\u05d6\u05de\u05e0\u05d5\u05ea": "nav_ord"\n'
        '}\n'
        '_ank = _view_nav_map.get(st.session_state.get("current_view", "\u05d4\u05d6\u05de\u05e0\u05d5\u05ea"), "nav_ord")\n'
        'st.markdown(\n'
        '    f\'\'\'<style>.st-key-{_ank} button {{\n'
        '    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;\n'
        '    color: white !important;\n'
        '    border-color: #6366f1 !important;\n'
        '    box-shadow: 0 3px 12px rgba(99,102,241,0.45) !important;\n'
        '    font-weight: 700 !important;\n'
        '    transform: translateY(-1px);\n'
        '}}</style>\'\'\',\n'
        '    unsafe_allow_html=True\n'
        ')\n'
        '\n'
        'with col2:\n'
        '    if st.button("\U0001f9f5 \u05de\u05dc\u05d0\u05d9", use_container_width=True, key="nav_inv"): st.session_state.current_view = "\u05de\u05dc\u05d0\u05d9"; st.rerun()\n'
        'with col3:\n'
        '    if st.button("\u2702\ufe0f \u05d2\u05d6\u05e8\u05d5\u05ea", use_container_width=True, key="nav_pat"): st.session_state.current_view = "\u05d2\u05d6\u05e8\u05d5\u05ea"; st.rerun()\n'
        'with col4:\n'
        '    if st.button("\U0001f4b0 \u05e4\u05d9\u05e0\u05e0\u05e1\u05d9", use_container_width=True, key="nav_fin"): st.session_state.current_view = "\u05e4\u05d9\u05e0\u05e0\u05e1\u05d9"; st.rerun()\n'
        'with col5:\n'
        '    if st.button("\U0001f465 \u05dc\u05e7\u05d5\u05d7\u05d5\u05ea", use_container_width=True, key="nav_cust"): st.session_state.current_view = "\u05dc\u05e7\u05d5\u05d7\u05d5\u05ea"; st.rerun()\n'
        'with col6:\n'
        '    if st.button("\U0001f4e6 \u05d4\u05d6\u05de\u05e0\u05d5\u05ea", use_container_width=True, key="nav_ord"): st.session_state.current_view = "\u05d4\u05d6\u05de\u05e0\u05d5\u05ea"; st.rerun()\n'
        'with col7:\n'
        '    if st.button("\U0001f504 \u05e8\u05e2\u05e0\u05d5\u05df \u05e0\u05ea\u05d5\u05e0\u05d9\u05dd", use_container_width=True, key="nav_refresh"): st.session_state.data_loaded = False; st.rerun()'
    )
    text = text.replace(old_nav, new_nav)
    print("OK Change 1 (Navbar) applied")
else:
    print("SKIP Change 1 - anchor not found, checking snippet...")
    # debug
    snippet = 'if st.button("\U0001f9f5 \u05de\u05dc\u05d0\u05d9"'
    if snippet in text:
        print("  - snippet found, but full block differs")
    else:
        print("  - snippet NOT found")

# ==============================================================
# CHANGE 2: Order form – Styled section headers
# ==============================================================

changes2 = [
    (
        '            # --- \u05e9\u05d3\u05d5\u05ea \u05de\u05d9\u05d3\u05d4/\u05d2\u05d6\u05e8\u05d4 \u05d3\u05d9\u05e0\u05de\u05d9\u05d9\u05dd \u05dc\u05e4\u05d9 \u05e1\u05d5\u05d2 ---\n'
        '            top_size, bottom_size, custom_size, pattern_name = "", "", "", ""',

        '            st.markdown(\n'
        '                \'<div style="background:linear-gradient(135deg,#f8f9ff,#eef0ff);border-right:4px solid #6366f1;\'\n'
        '                \'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">\'\n'
        '                \'<span style="font-weight:700;color:#4338ca;font-size:15px;">\U0001f4d0 \u05d2\u05d6\u05e8\u05d4 \u05d5\u05de\u05d9\u05d3\u05d5\u05ea</span></div>\',\n'
        '                unsafe_allow_html=True)\n'
        '            # --- \u05e9\u05d3\u05d5\u05ea \u05de\u05d9\u05d3\u05d4/\u05d2\u05d6\u05e8\u05d4 \u05d3\u05d9\u05e0\u05de\u05d9\u05d9\u05dd \u05dc\u05e4\u05d9 \u05e1\u05d5\u05d2 ---\n'
        '            top_size, bottom_size, custom_size, pattern_name = "", "", "", ""'
    ),
    (
        '            st.markdown("### \U0001f9f5 \u05d1\u05d7\u05d9\u05e8\u05ea \u05d1\u05d3 \u05e8\u05d0\u05e9\u05d9")',

        '            st.markdown(\n'
        '                \'<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-right:4px solid #22c55e;\'\n'
        '                \'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">\'\n'
        '                \'<span style="font-weight:700;color:#15803d;font-size:15px;">\U0001f9f5 \u05d1\u05d7\u05d9\u05e8\u05ea \u05d1\u05d3\u05d9\u05dd</span></div>\',\n'
        '                unsafe_allow_html=True)\n'
        '            st.markdown("### \U0001f9f5 \u05d1\u05d7\u05d9\u05e8\u05ea \u05d1\u05d3 \u05e8\u05d0\u05e9\u05d9")'
    ),
    (
        '            col_d1, col_d2 = st.columns(2)\n'
        '            with col_d1: form_order_date = st.date_input("\u05ea\u05d0\u05e8\u05d9\u05da \u05d4\u05d6\u05de\u05e0\u05d4", value=datetime.today())\n'
        '            with col_d2: form_delivery_date = st.date_input("\u05ea\u05d0\u05e8\u05d9\u05da \u05d0\u05e1\u05e4\u05e7\u05d4 \u05de\u05d9\u05d5\u05e2\u05d3", value=None)',

        '            st.markdown(\n'
        '                \'<div style="background:linear-gradient(135deg,#fffbeb,#fef9c3);border-right:4px solid #f59e0b;\'\n'
        '                \'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">\'\n'
        '                \'<span style="font-weight:700;color:#b45309;font-size:15px;">\U0001f4c5 \u05ea\u05d0\u05e8\u05d9\u05db\u05d9\u05dd \u05d5\u05d4\u05e2\u05e8\u05d5\u05ea</span></div>\',\n'
        '                unsafe_allow_html=True)\n'
        '            col_d1, col_d2 = st.columns(2)\n'
        '            with col_d1: form_order_date = st.date_input("\u05ea\u05d0\u05e8\u05d9\u05da \u05d4\u05d6\u05de\u05e0\u05d4", value=datetime.today())\n'
        '            with col_d2: form_delivery_date = st.date_input("\u05ea\u05d0\u05e8\u05d9\u05da \u05d0\u05e1\u05e4\u05e7\u05d4 \u05de\u05d9\u05d5\u05e2\u05d3", value=None)'
    ),
    (
        '            st.markdown("**\u05e1\u05d8\u05d8\u05d5\u05e1 \u05d5\u05ea\u05e9\u05dc\u05d5\u05dd:**")',

        '            st.markdown(\n'
        '                \'<div style="background:linear-gradient(135deg,#fff0f3,#ffe4e6);border-right:4px solid #f43f5e;\'\n'
        '                \'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">\'\n'
        '                \'<span style="font-weight:700;color:#be123c;font-size:15px;">\U0001f4b3 \u05e1\u05d8\u05d8\u05d5\u05e1 \u05d5\u05ea\u05e9\u05dc\u05d5\u05dd</span></div>\',\n'
        '                unsafe_allow_html=True)\n'
        '            st.markdown("**\u05e1\u05d8\u05d8\u05d5\u05e1 \u05d5\u05ea\u05e9\u05dc\u05d5\u05dd:**")'
    ),
]

for i, (old, new) in enumerate(changes2):
    if old in text:
        text = text.replace(old, new)
        print(f"OK Change 2{chr(97+i)} applied")
    else:
        print(f"SKIP Change 2{chr(97+i)} - anchor not found")

# ==============================================================
# CHANGE 3: Patterns – editable columns + save button
# ==============================================================

old_cfg = (
    '        patterns_cfg = {\n'
    '            "\u05e9\u05dd \u05d4\u05d2\u05d6\u05e8\u05d4": st.column_config.TextColumn("\u05e9\u05dd \u05d4\u05d2\u05d6\u05e8\u05d4", disabled=True),\n'
    '            "\u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d4": st.column_config.TextColumn("\u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d4", disabled=True),\n'
    '        }'
)
new_cfg = (
    '        patterns_cfg = {\n'
    '            "\u05e9\u05dd \u05d4\u05d2\u05d6\u05e8\u05d4": st.column_config.TextColumn("\u05e9\u05dd \u05d4\u05d2\u05d6\u05e8\u05d4 (\u05e0\u05d9\u05ea\u05df \u05dc\u05e2\u05e8\u05d9\u05db\u05d4)"),\n'
    '            "\u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d4": st.column_config.SelectboxColumn("\u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d4", options=["\u05d1\u05d2\u05d3 \u05d9\u05dd \u05e9\u05dc\u05dd", "\u05d1\u05d9\u05e7\u05d9\u05e0\u05d9"], required=True),\n'
    '        }'
)

if old_cfg in text:
    text = text.replace(old_cfg, new_cfg)
    print("OK Change 3a (Patterns column_config) applied")
else:
    print("SKIP Change 3a - anchor not found")

old_save_block = (
        '        with col_btn_save:\n'
        '            if st.session_state.delete_mode_patterns:\n'
        '                patterns_to_delete = edited_patterns[edited_patterns["\u05d1\u05d7\u05e8\u05d9"] == True]\n'
        '                if not patterns_to_delete.empty:\n'
        '                    if st.button("\u05de\u05d7\u05e7\u05d9 \u05de\u05e1\u05d5\u05de\u05e0\u05d5\u05ea \U0001f5d1\ufe0f", type="primary", use_container_width=True):\n'
        '                        with st.spinner("\u05de\u05d5\u05d7\u05e7\u05ea \u05d2\u05d6\u05e8\u05d5\u05ea..."):\n'
        '                            names_to_delete = patterns_to_delete["\u05e9\u05dd \u05d4\u05d2\u05d6\u05e8\u05d4"].astype(str).tolist()\n'
        '                            st.session_state.patterns_df = st.session_state.patterns_df[\n'
        '                                ~st.session_state.patterns_df["Pattern Name"].astype(str).isin(names_to_delete)\n'
        '                            ]\n'
        '\n'
        '                            patterns_sheet.clear()\n'
        '                            save_patterns = st.session_state.patterns_df[["Pattern Name", "Category"]]\n'
        '                            if save_patterns.empty:\n'
        '                                patterns_sheet.update([["Pattern Name", "Category"]])\n'
        '                            else:\n'
        '                                patterns_sheet.update(\n'
        '                                    [save_patterns.columns.values.tolist()] + save_patterns.values.tolist()\n'
        '                                )\n'
        '\n'
        '                            st.session_state.delete_mode_patterns = False\n'
        '                            st.success("\u05d4\u05d2\u05d6\u05e8\u05d5\u05ea \u05e0\u05de\u05d7\u05e7\u05d5 \u05d1\u05d4\u05e6\u05dc\u05d7\u05d4!")\n'
        '                            st.rerun()'
)

new_save_block = old_save_block + (
    '\n'
    '            else:\n'
    '                if st.button("\U0001f4be \u05e9\u05de\u05e8\u05d9 \u05e9\u05d9\u05e0\u05d5\u05d9\u05d9\u05dd", type="primary", use_container_width=True):\n'
    '                    with st.spinner("\u05e9\u05d5\u05de\u05e8\u05ea \u05d1\u05e2\u05e0\u05df..."):\n'
    '                        upd_pat = edited_patterns.copy()\n'
    '                        if "\u05d1\u05d7\u05e8\u05d9" in upd_pat.columns:\n'
    '                            upd_pat = upd_pat.drop(columns=["\u05d1\u05d7\u05e8\u05d9"])\n'
    '                        upd_pat = upd_pat.rename(columns={"\u05e9\u05dd \u05d4\u05d2\u05d6\u05e8\u05d4 (\u05e0\u05d9\u05ea\u05df \u05dc\u05e2\u05e8\u05d9\u05db\u05d4)": "Pattern Name", "\u05e9\u05dd \u05d4\u05d2\u05d6\u05e8\u05d4": "Pattern Name", "\u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d4": "Category"})\n'
    '                        upd_pat = upd_pat[["Pattern Name", "Category"]]\n'
    '                        upd_pat = upd_pat[upd_pat["Pattern Name"].astype(str).str.strip() != ""]\n'
    '                        st.session_state.patterns_df = upd_pat.reset_index(drop=True)\n'
    '                        patterns_sheet.clear()\n'
    '                        if upd_pat.empty:\n'
    '                            patterns_sheet.update([["Pattern Name", "Category"]])\n'
    '                        else:\n'
    '                            patterns_sheet.update([upd_pat.columns.values.tolist()] + upd_pat.values.tolist())\n'
    '                        st.success("\u05d4\u05d2\u05d6\u05e8\u05d5\u05ea \u05e2\u05d5\u05d3\u05db\u05e0\u05d5!")\n'
    '                        st.rerun()'
)

if old_save_block in text:
    text = text.replace(old_save_block, new_save_block)
    print("OK Change 3b (Patterns save button) applied")
else:
    print("SKIP Change 3b - anchor not found")

with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("\nAll done. Run: python -m py_compile swimwear_app.py")
