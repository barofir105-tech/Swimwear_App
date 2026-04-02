import os
import re

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Order ID Generation
text = text.replace(
    'order_id = "ORD-" + datetime.now().strftime("%Y%m%d%H%M")',
    '''def get_next_order_id(df):
                        if df.empty: return "0001"
                        valid_ids = pd.to_numeric(df["Order ID"], errors='coerce')
                        max_id = valid_ids.max()
                        if pd.isna(max_id): return "0001"
                        return f"{int(max_id) + 1:04d}"
                    order_id = get_next_order_id(st.session_state.orders_df)'''
)

# 2. Add Price column to active orders view (around line 620)
old_display_rename = """"Order ID": "מספר הזמנה", "Order Date": "תאריך הזמנה", "Delivery Date": "תאריך אספקה",
                "Customer Name": "שם לקוחה", "Item": "פריט", "Status": "סטטוס", "Payment Status": "סטטוס תשלום",
                "Top Size": "עליון", "Bottom Size": "תחתון", "Custom Size": "התאמות", "Fabric Usage": "צריכת בד (מ')" """

new_display_rename = """"Order ID": "מספר הזמנה", "Order Date": "תאריך הזמנה", "Delivery Date": "תאריך אספקה",
                "Customer Name": "שם לקוחה", "Item": "פריט", "Status": "סטטוס", "Payment Status": "סטטוס תשלום",
                "Top Size": "עליון", "Bottom Size": "תחתון", "Custom Size": "התאמות", "Fabric Usage": "צריכת בד (מ')", "Price": "מחיר" """
text = text.replace(old_display_rename, new_display_rename)

old_cols_active = 'cols = ["סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "תאריך הזמנה", "פריט", "שם לקוחה"]'
new_cols_active = 'cols = ["מחיר", "סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "תאריך הזמנה", "פריט", "שם לקוחה"]'
text = text.replace(old_cols_active, new_cols_active)

old_config_active = '"סטטוס תשלום": st.column_config.SelectboxColumn("תשלום", options=["🔴", "🟡", "🟢"], width="small"),'
new_config_active = '"סטטוס תשלום": st.column_config.SelectboxColumn("תשלום", options=["🔴", "🟡", "🟢"], width="small"),\n                "מחיר": st.column_config.NumberColumn("מחיר", format="₪%d", width="small"),'
text = text.replace(old_config_active, new_config_active)

old_save_rename = """"מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "שם לקוחה": "Customer Name", "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage" """

new_save_rename = """"מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "שם לקוחה": "Customer Name", "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage", "מחיר": "Price" """
text = text.replace(old_save_rename, new_save_rename)


# 2b. Add Price column to Customer's active orders view (around line 920)
# (Same logic but for the customer tab)
old_cust_rename = """"Order ID": "מספר הזמנה", "Order Date": "תאריך הזמנה", "Delivery Date": "תאריך אספקה",
            "Item": "פריט", "Top Size": "עליון", "Bottom Size": "תחתון", "Custom Size": "התאמות",
            "Fabric Usage": "צריכת בד (מ')", "Status": "סטטוס", "Payment Status": "סטטוס תשלום" """

new_cust_rename = """"Order ID": "מספר הזמנה", "Order Date": "תאריך הזמנה", "Delivery Date": "תאריך אספקה",
            "Item": "פריט", "Top Size": "עליון", "Bottom Size": "תחתון", "Custom Size": "התאמות",
            "Fabric Usage": "צריכת בד (מ')", "Status": "סטטוס", "Payment Status": "סטטוס תשלום", "Price": "מחיר" """
text = text.replace(old_cust_rename, new_cust_rename)

old_cols_cust = 'cols = ["סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "תאריך הזמנה", "פריט"]'
new_cols_cust = 'cols = ["מחיר", "סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "תאריך הזמנה", "פריט"]'
text = text.replace(old_cols_cust, new_cols_cust)

old_cust_save_rename = """"מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage" """

new_cust_save_rename = """"מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage", "מחיר": "Price" """
text = text.replace(old_cust_save_rename, new_cust_save_rename)


# 3. Finance Default Month & Pie Chart fix
old_finance_radio = """        year_options = list(range(2025, 2035))
        
        col_y, col_m = st.columns([1, 4])
        with col_y:
            selected_year = st.selectbox("שנה", options=year_options, index=1)
        with col_m:
            selected_month_heb = st.radio("חודש", options=hebrew_months, horizontal=True, label_visibility="collapsed")"""

new_finance_radio = """        year_options = list(range(2025, 2035))
        current_dt = datetime.now()
        cur_year_idx = year_options.index(current_dt.year) if current_dt.year in year_options else 1
        cur_month_idx = current_dt.month - 1
        
        col_y, col_m = st.columns([1, 4])
        with col_y:
            selected_year = st.selectbox("שנה", options=year_options, index=cur_year_idx)
        with col_m:
            selected_month_heb = st.radio("חודש", options=hebrew_months, horizontal=True, label_visibility="collapsed", index=cur_month_idx)"""
text = text.replace(old_finance_radio, new_finance_radio)

old_pie_cat = """                    if item.get("Type", "Expense") == "Income":
                        cat_name = dict(item).get("Item", "הכנסה ידנית")
                        if cat_name == "": cat_name = "כללי"
                        inc_rows.append({"Category": cat_name, "Value": float(item["amount"])})"""

new_pie_cat = """                    if item.get("Type", "Expense") == "Income":
                        cat_name = dict(item).get("Item", dict(item).get("name", "הכנסה ידנית"))
                        if str(cat_name).strip() == "": cat_name = "כללי"
                        inc_rows.append({"Category": cat_name, "Value": float(item["amount"])})"""
text = text.replace(old_pie_cat, new_pie_cat)


with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updates applied to swimwear_app.py")
