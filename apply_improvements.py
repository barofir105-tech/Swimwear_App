"""
apply_all_improvements.py
Applies improvements #4, #7, #8, #9 using targeted string replacement.
"""
import subprocess, sys

# ── helpers ──────────────────────────────────────────────────────────────
def patch(path, old, new, label):
    text = open(path, encoding="utf-8").read()
    if old in text:
        open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
        print(f"  OK  {label}")
        return True
    else:
        print(f"  SKIP {label} (anchor not found)")
        return False

def compile_check(path):
    r = subprocess.run([sys.executable, "-m", "py_compile", path], capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} compile {path}" + ("" if ok else f": {r.stderr.strip()[:80]}"))
    return ok

# ─────────────────────────────────────────────────────────────────────────
# IMPROVEMENT #8 — Stats bar above orders table (views/orders.py)
# ─────────────────────────────────────────────────────────────────────────
print("\n[#8] Orders stats bar")

OLD8 = "        if not orders_df.empty:\n            display_orders = orders_df.copy()\n\n            st.markdown(\"### 🔍 חיפוש וסינון הזמנות\")"

stats_block = (
    '        if not orders_df.empty:\n'
    '            display_orders = orders_df.copy()\n'
    '\n'
    '            # stats bar\n'
    '            _total  = len(orders_df)\n'
    '            _active = len(orders_df[orders_df["Status"] != "\u2705 \u05e0\u05de\u05e1\u05e8\u05d4 \u05dc\u05dc\u05e7\u05d5\u05d7\u05d4"])\n'
    '            _pickup = len(orders_df[orders_df["Status"] == "\U0001f4e6 \u05de\u05d5\u05db\u05e0\u05d4 \u05dc\u05d0\u05d9\u05e1\u05d5\u05e3/\u05de\u05e9\u05dc\u05d5\u05d7"])\n'
    '            _unpaid = len(orders_df[orders_df["Payment Status"] == "\U0001f534"])\n'
    '            _done   = _total - _active\n'
    '            _s1, _s2, _s3, _s4, _s5 = st.columns(5)\n'
    '            with _s1: st.metric("\U0001f4e6 \u05e1\u05d4\\\"\u05db \u05d4\u05d6\u05de\u05e0\u05d5\u05ea", _total)\n'
    '            with _s2: st.metric("\u26a1 \u05d4\u05d6\u05de\u05e0\u05d5\u05ea \u05e4\u05e2\u05d9\u05dc\u05d5\u05ea", _active)\n'
    '            with _s3: st.metric("\U0001f69a \u05de\u05d5\u05db\u05e0\u05d5\u05ea \u05dc\u05d0\u05d9\u05e1\u05d5\u05e3", _pickup)\n'
    '            with _s4: st.metric("\U0001f534 \u05d8\u05e8\u05dd \u05e9\u05d5\u05dc\u05de\u05d5", _unpaid)\n'
    '            with _s5: st.metric("\u2705 \u05d4\u05d5\u05e9\u05dc\u05de\u05d5", _done)\n'
    '            st.markdown("---")\n'
    '\n'
    '            st.markdown("### \U0001f50d \u05d7\u05d9\u05e4\u05d5\u05e9 \u05d5\u05e1\u05d9\u05e0\u05d5\u05df \u05d4\u05d6\u05de\u05e0\u05d5\u05ea")\n'
)

NEW8 = stats_block

patch("views/orders.py", OLD8, NEW8, "orders stats bar")
compile_check("views/orders.py")

# ─────────────────────────────────────────────────────────────────────────
# IMPROVEMENT #4 — Radio months → Selectbox (views/financial.py)
# ─────────────────────────────────────────────────────────────────────────
print("\n[#4] Financial: radio months → selectbox")

OLD4 = """            c_y, c_m = st.columns([1, 4])
            with c_y:
                selected_year = st.selectbox("שנה", options=year_options, index=cur_year_idx)
            with c_m:
                selected_month_heb = st.radio("חודש", options=hebrew_months, horizontal=True, label_visibility="collapsed", index=cur_month_idx)
                selected_month = hebrew_to_english[selected_month_heb]"""

NEW4 = """            c_y, c_m = st.columns([1, 3])
            with c_y:
                selected_year = st.selectbox("שנה", options=year_options, index=cur_year_idx)
            with c_m:
                selected_month_heb = st.selectbox("חודש", options=hebrew_months, index=cur_month_idx)
                selected_month = hebrew_to_english[selected_month_heb]"""

patch("views/financial.py", OLD4, NEW4, "months selectbox")
compile_check("views/financial.py")

# ─────────────────────────────────────────────────────────────────────────
# IMPROVEMENT #9 — Colored type indicator in finance transactions table
# ─────────────────────────────────────────────────────────────────────────
print("\n[#9] Financial: colored type indicator column")

OLD9 = """                txn_display = txn_df[["id"]].copy()
                txn_display["סכום"] = txn_df["amount"]
                txn_display["סוג"] = txn_df["Type"].map({"Expense": "הוצאה", "Income": "הכנסה"})
                txn_display["תאריך"] = txn_df["date_ts"].dt.date
                txn_display["שם התנועה"] = txn_df["name"]
                if "בחרי" in txn_df.columns: txn_display["בחרי"] = txn_df["בחרי"]

                conf = {
                    "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "שם התנועה": st.column_config.TextColumn("שם התנועה"),
                    "תאריך": st.column_config.DateColumn("תאריך", format="DD/MM/YYYY"),
                    "סוג": st.column_config.SelectboxColumn("סוג", options=["הוצאה", "הכנסה"]),
                    "סכום": st.column_config.NumberColumn("סכום", format="₪%d")
                }"""

NEW9 = """                txn_display = txn_df[["id"]].copy()
                txn_display["סכום"] = txn_df["amount"]
                txn_display["סוג"] = txn_df["Type"].map({"Expense": "הוצאה", "Income": "הכנסה"})
                txn_display["●"] = txn_df["Type"].map({"Expense": "🔴", "Income": "🟢"})
                txn_display["תאריך"] = txn_df["date_ts"].dt.date
                txn_display["שם התנועה"] = txn_df["name"]
                if "בחרי" in txn_df.columns: txn_display["בחרי"] = txn_df["בחרי"]

                conf = {
                    "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "●": st.column_config.TextColumn("", disabled=True, width="small"),
                    "שם התנועה": st.column_config.TextColumn("שם התנועה"),
                    "תאריך": st.column_config.DateColumn("תאריך", format="DD/MM/YYYY"),
                    "סוג": st.column_config.SelectboxColumn("סוג", options=["הוצאה", "הכנסה"]),
                    "סכום": st.column_config.NumberColumn("סכום", format="₪%d")
                }"""

patch("views/financial.py", OLD9, NEW9, "colored type indicator")
compile_check("views/financial.py")

# ─────────────────────────────────────────────────────────────────────────
# IMPROVEMENT #7 — st.success → st.toast across all views
# ─────────────────────────────────────────────────────────────────────────
print("\n[#7] Toast messages")

import re

# Messages to convert to toast (brief confirmations, not errors/info)
TOAST_PATTERNS = [
    "st.success(\"נשמר בהצלחה!\"); st.rerun()",
    "st.success(\"ההזמנות נמחקו!\"); st.rerun()",
    "st.success(\"הגזרות נמחקו בהצלחה!\"); st.rerun()",
    "st.success(\"הגזרות עודכנו!\"); st.rerun()",
    "st.success(\"המלאי עודכן בהצלחה!\"); st.rerun()",
    "st.success(\"ההזמנות עודכנו בהצלחה!\"); st.rerun()",
    "st.success(\"ההערות נשמרו!\")",
    "st.success(\"המידע התעדכן במערכת!\")\n                            st.rerun()",
    "st.success(\"התנועה נוספה!\")\n                        st.rerun()",
    "st.success(\"הוראת הקבע נוספה!\")\n                        st.rerun()",
]

view_files = [
    "views/orders.py",
    "views/inventory.py",
    "views/customers.py",
    "views/financial.py",
    "views/patterns.py",
]

for vf in view_files:
    text = open(vf, encoding="utf-8").read()
    original = text
    # Replace patterns like: st.success("..."); st.rerun()
    # with: st.toast("...", icon="✅"); st.rerun()
    # Simple: convert st.success(X) to st.toast(X, icon="✅") keeping st.rerun() intact
    text = re.sub(
        r'st\.success\(("(?:[^"\\]|\\.)*")\); st\.rerun\(\)',
        r'st.toast(\1, icon="✅"); st.rerun()',
        text
    )
    # Also single-line success without immediate rerun
    text = re.sub(
        r'st\.success\(("(?:[^"\\]|\\.)*")\)',
        r'st.toast(\1, icon="✅")',
        text
    )
    # success with f-strings
    text = re.sub(
        r'st\.success\((f"(?:[^"\\]|\\.)*")\); st\.rerun\(\)',
        r'st.toast(\1, icon="✅"); st.rerun()',
        text
    )
    text = re.sub(
        r'st\.success\((f"(?:[^"\\]|\\.)*")\)',
        r'st.toast(\1, icon="✅")',
        text
    )
    if text != original:
        open(vf, "w", encoding="utf-8").write(text)
        print(f"  OK  toast in {vf}")
    else:
        print(f"  -- no success() found in {vf}")

for vf in view_files:
    compile_check(vf)

print("\nAll improvements applied.")
