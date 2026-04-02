import sys

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: Title
text = text.replace('### 📋 טבלת עריכת תנועות ידניות', '### 📋 טבלת תנועות')

# Fix 3: Button text
text = text.replace('➕ חוללי תנועה', '➕ הוסיפי תנועה')

# Fix 4: Bug in delete_mode logic
text = text.replace('delete_mode_txn", False) == False:', 'delete_mode_txn", False) == True:')
text = text.replace('delete_mode_so", False) == False:', 'delete_mode_so", False) == True:')

# Fix 2: Reordering TXN columns
old_txn_cols = """                txn_display = txn_df[["id", "בחרי"]].copy() if "בחרי" in txn_df.columns else txn_df[["id"]].copy()
                txn_display["שם התנועה"] = txn_df["name"]
                txn_display["תאריך"] = txn_df["date_ts"].dt.date
                txn_display["סוג"] = txn_df["Type"].map({"Expense": "הוצאה", "Income": "הכנסה"})
                txn_display["סכום"] = txn_df["amount"]"""

new_txn_cols = """                txn_display = txn_df[["id"]].copy()
                txn_display["סכום"] = txn_df["amount"]
                txn_display["סוג"] = txn_df["Type"].map({"Expense": "הוצאה", "Income": "הכנסה"})
                txn_display["תאריך"] = txn_df["date_ts"].dt.date
                txn_display["שם התנועה"] = txn_df["name"]
                if "בחרי" in txn_df.columns: txn_display["בחרי"] = txn_df["בחרי"]"""
text = text.replace(old_txn_cols, new_txn_cols)

# Fix 2: Reordering SO columns
old_so_cols = """                so_disp = so_df[["id", "בחרי"] if "בחרי" in so_df.columns else ["id"]].copy()
                so_disp["שם ההוצאה"] = so_df["name"]
                
                def render_freq(row):
                    freq = row.get("frequency", "Monthly")
                    if freq == "Monthly": return "חודשית"
                    if freq == "Yearly": return "שנתית"
                    val = row.get("custom_interval", 1)
                    unit = row.get("custom_unit", "Months")
                    map_u = {"Days":"ימים", "Weeks":"שבועות", "Months":"חודשים", "Years":"שנים"}
                    return f"כל {val} {map_u.get(unit, unit)}"
                
                so_disp["תדירות"] = so_df.apply(render_freq, axis=1)
                so_disp["סכום"] = so_df["amount"]
                so_disp["התחלה"] = pd.to_datetime(so_df["start_date"], errors="coerce").dt.date
                so_disp["סיום"] = pd.to_datetime(so_df["end_date"], errors="coerce").dt.date"""

new_so_cols = """                so_disp = so_df[["id"]].copy()
                
                def render_freq(row):
                    freq = row.get("frequency", "Monthly")
                    if freq == "Monthly": return "חודשית"
                    if freq == "Yearly": return "שנתית"
                    val = row.get("custom_interval", 1)
                    unit = row.get("custom_unit", "Months")
                    map_u = {"Days":"ימים", "Weeks":"שבועות", "Months":"חודשים", "Years":"שנים"}
                    return f"כל {val} {map_u.get(unit, unit)}"
                
                so_disp["סיום"] = pd.to_datetime(so_df["end_date"], errors="coerce").dt.date
                so_disp["התחלה"] = pd.to_datetime(so_df["start_date"], errors="coerce").dt.date
                so_disp["סכום"] = so_df["amount"]
                so_disp["תדירות"] = so_df.apply(render_freq, axis=1)
                so_disp["שם ההוצאה"] = so_df["name"]
                if "בחרי" in so_df.columns: so_disp["בחרי"] = so_df["בחרי"]"""
text = text.replace(old_so_cols, new_so_cols)

with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied!")
