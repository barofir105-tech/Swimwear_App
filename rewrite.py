import re

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Remove height from all st.data_editor calls
code = re.sub(r', height=\d+', '', code)

# 2. Swap the Add Order Block to top
match_orders_pg = re.search(r'elif st\.session_state\.current_view == "הזמנות":\n    st\.title\("📦 ניהול הזמנות"\).*?if orders_sheet is None:\n        st\.error\(.*?\) +else:\n(.*)(# ={42}\n#               מסך הלקוחות)', code, flags=re.DOTALL)

if match_orders_pg:
    orders_body = match_orders_pg.group(1)
    
    parts = orders_body.split('        st.markdown("---")\n        \n        st.subheader("➕ יצירת הזמנה חדשה")')
    if len(parts) == 2:
        table_part = parts[0]
        form_part = '        st.subheader("➕ יצירת הזמנה חדשה")' + parts[1]
        
        table_part = re.sub(r'cols = \["סטטוס תשלום", "סטטוס", "מספר הזמנה", "שם לקוחה".*?(?=\n\s*cols = \[c for c in cols)', 
                            'cols = ["שם לקוחה", "פריט", "תאריך הזמנה", "תאריך אספקה", "עליון", "תחתון", "התאמות", "מספר הזמנה", "סטטוס", "סטטוס תשלום"]\n            if "מספר הזמנה" in display_orders.columns:\n                display_orders = display_orders.sort_values(by="מספר הזמנה", ascending=False)', table_part, flags=re.DOTALL)
        
        table_part = re.sub(r'"שם לקוחה": st\.column_config\.TextColumn\("שם לקוחה", disabled=True, width="medium"\)', '"שם לקוחה": st.column_config.TextColumn("שם לקוחה", disabled=True)', table_part)
        table_part = re.sub(r'"פריט\": st\.column_config\.TextColumn\("פריט", width="medium"\)', '"פריט": st.column_config.TextColumn("פריט")', table_part)
        table_part = re.sub(r'"התאמות": st\.column_config\.TextColumn\("התאמות", width="small"\)', '"התאמות": st.column_config.TextColumn("התאמות")', table_part)
        table_part = re.sub(r'"סטטוס": st\.column_config\.SelectboxColumn\("סטטוס", options=\["🆕 התקבלה \(ממתינה לייצור\)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"\], width="medium"\)', '"סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה לייצור)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"])', table_part)
        table_part = re.sub(r'"עליון": st\.column_config\.TextColumn\("עליון", width="small"\)', '"עליון": st.column_config.TextColumn("עליון")', table_part)
        table_part = re.sub(r'"תחתון": st\.column_config\.TextColumn\("תחתון", width="small"\)', '"תחתון": st.column_config.TextColumn("תחתון")', table_part)
        table_part = re.sub(r'"תאריך אספקה": st\.column_config\.DateColumn\("תאריך אספקה", format="DD/MM/YYYY", width="small"\)', '"תאריך אספקה": st.column_config.DateColumn("תאריך אספקה", format="DD/MM/YYYY")', table_part)
        
        new_orders_body = form_part + "\n        st.markdown('---')\n" + table_part
        
        code = code.replace(orders_body, new_orders_body)

# Similarly update customer orders table
code = re.sub(r'cols = \["סטטוס תשלום", "סטטוס", "מספר הזמנה", "פריט", "תאריך אספקה", "עליון", "תחתון", "התאמות"\]', 'cols = ["פריט", "תאריך אספקה", "עליון", "תחתון", "התאמות", "מספר הזמנה", "סטטוס", "סטטוס תשלום"]\n                    if "מספר הזמנה" in display_cust_orders.columns:\n                        display_cust_orders = display_cust_orders.sort_values(by="מספר הזמנה", ascending=False)', code)

code = re.sub(r'"פריט": st\.column_config\.TextColumn\("פריט", width="medium"\)', '"פריט": st.column_config.TextColumn("פריט")', code)
code = re.sub(r'"התאמות": st\.column_config\.TextColumn\("התאמות", width="small"\)', '"התאמות": st.column_config.TextColumn("התאמות")', code)
code = re.sub(r'"סטטוס": st\.column_config\.SelectboxColumn\("סטטוס", options=\["🆕 התקבלה \(ממתינה לייצור\)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"\], width="medium"\)', '"סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה לייצור)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"])', code)
code = re.sub(r'"עליון": st\.column_config\.TextColumn\("עליון", width="small"\)', '"עליון": st.column_config.TextColumn("עליון")', code)
code = re.sub(r'"תחתון": st\.column_config\.TextColumn\("תחתון", width="small"\)', '"תחתון": st.column_config.TextColumn("תחתון")', code)
code = re.sub(r'"תאריך אספקה": st\.column_config\.DateColumn\("תאריך אספקה", format="DD/MM/YYYY", width="small"\)', '"תאריך אספקה": st.column_config.DateColumn("תאריך אספקה", format="DD/MM/YYYY")', code)


with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("success")
