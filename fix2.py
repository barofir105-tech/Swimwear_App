import sys

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.strip() == 'elif st.session_state.current_view == "הזמנות":':
        for j in range(i, len(lines)):
            if lines[j].strip() == 'if orders_sheet is None:':
                start_idx = j + 2 # the line with `else:` is j+1, `if not orders_df.empty:` is j+2
                break
        break

for i in range(start_idx, len(lines)):
    if 'מסך הלקוחות' in lines[i]:
        end_idx = i - 2 # the line with # =======
        break

if start_idx == -1 or end_idx == -1:
    print('Could not find boundaries')
    sys.exit(1)

form_start = -1
table_end = -1

for i in range(start_idx, end_idx):
    if 'st.subheader("➕ יצירת הזמנה חדשה")' in lines[i]:
        form_start = i - 2 # including the st.markdown('---') before it
        table_end = form_start
        break

if form_start == -1:
    print('Could not find form')
    sys.exit(1)

table_lines = lines[start_idx:table_end]
form_lines = lines[form_start:end_idx]

# Modify Table Lines content:
for i, line in enumerate(table_lines):
    if line.strip().startswith('cols = ["סטטוס תשלום"'):
        table_lines[i] = '            cols = ["שם לקוחה", "פריט", "תאריך הזמנה", "תאריך אספקה", "עליון", "תחתון", "התאמות", "מספר הזמנה", "סטטוס", "סטטוס תשלום"]\n'
    if line.strip().startswith('config = {'):
        config_end = -1
        for j in range(i, len(table_lines)):
            if table_lines[j].strip() == '}':
                config_end = j
                break
        
        config_text = """            config = {
                "שם לקוחה": st.column_config.TextColumn("שם לקוחה", disabled=True),
                "פריט": st.column_config.TextColumn("פריט"),
                "תאריך הזמנה": st.column_config.DateColumn("תאריך הזמנה", format="DD/MM/YYYY", width="small"),
                "תאריך אספקה": st.column_config.DateColumn("תאריך אספקה", format="DD/MM/YYYY"),
                "עליון": st.column_config.TextColumn("עליון"),
                "תחתון": st.column_config.TextColumn("תחתון"),
                "התאמות": st.column_config.TextColumn("התאמות"),
                "מספר הזמנה": st.column_config.TextColumn("מספר הזמנה", disabled=True, width="small"),
                "סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה לייצור)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"]),
                "סטטוס תשלום": st.column_config.SelectboxColumn("תשלום", options=["🔴", "🟡", "🟢"], width="small"),
            }\n"""
        table_lines[i:config_end+1] = [config_text]
        break 

# Find where to put sorting
for i, line in enumerate(table_lines):
    if line.strip().startswith('cols = ['):
        sort_logic = '            if "מספר הזמנה" in display_orders.columns:\n                display_orders = display_orders.sort_values(by="מספר הזמנה", ascending=False)\n'
        table_lines.insert(i, sort_logic)
        break

new_body = form_lines + ['        st.markdown("---")\n'] + table_lines

new_lines = lines[:start_idx] + new_body + lines[end_idx:]

with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('success')
