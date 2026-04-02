import os
import re

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add imports
imports_chunk = """import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import base64
from PIL import Image, ImageOps
import io
import json
import threading
import copy
import plotly.express as px"""

text = re.sub(
    r'import streamlit as st.*?import io', 
    imports_chunk, 
    text, 
    flags=re.DOTALL
)

# 2. Add fetch_finance_from_cloud and _background_save_finance
finance_helpers = """
def fetch_finance_from_cloud():
    try:
        sheet = spreadsheet.worksheet("Finance")
        col_a_values = sheet.col_values(1)
        raw_value = "".join(col_a_values)
        if not raw_value.strip():
            return {"settings": {"currency": "₪"}, "month_settings": {}, "monthly_expenses": {}, "standing_orders": []}, sheet
        data = json.loads(raw_value)
        data.setdefault("settings", {"currency": "₪"})
        data.setdefault("month_settings", {})
        data.setdefault("monthly_expenses", {})
        data.setdefault("standing_orders", [])
        return data, sheet
    except:
        return {"settings": {"currency": "₪"}, "month_settings": {}, "monthly_expenses": {}, "standing_orders": []}, None

def _background_save_finance(data_snapshot: dict) -> None:
    try:
        sheet = spreadsheet.worksheet("Finance")
        json_string = json.dumps(data_snapshot, ensure_ascii=False)
        chunk_size = 40000
        chunks = [json_string[i:i + chunk_size] for i in range(0, len(json_string), chunk_size)]
        values_to_update = [[chunk] for chunk in chunks]
        sheet.clear()
        sheet.update(range_name=f"A1:A{len(chunks)}", values=values_to_update)
    except Exception as e:
        print(f"Background save finance failed: {e}")

def save_finance_data(data: dict) -> None:
    data_snapshot = copy.deepcopy(data)
    thread = threading.Thread(target=_background_save_finance, args=(data_snapshot,))
    thread.start()

def is_standing_order_active(order: dict, target_year: int, target_month: int) -> bool:
    start_date = datetime.fromisoformat(order["start_date"]).date()
    end_date = datetime.fromisoformat(order["end_date"]).date()
    target_period = target_year * 12 + target_month
    start_period = start_date.year * 12 + start_date.month
    end_period = end_date.year * 12 + end_date.month
    if target_period < start_period or target_period > end_period:
        return False
    if order["frequency"] == "Monthly":
        return True
    return target_month == start_date.month

# ==========================================
#        ניהול מצב מקומי (Local State)
"""

text = re.sub(
    r'# ==========================================\n#        ניהול מצב מקומי \(Local State\)',
    finance_helpers,
    text
)

# 3. Add fetching finance in data_loaded
load_data_chunk = """        st.session_state.inventory_df, st.session_state.inventory_sheet = fetch_inventory_from_cloud()
        st.session_state.finance_data, st.session_state.finance_sheet = fetch_finance_from_cloud()
        st.session_state.data_loaded = True"""

text = re.sub(
    r'        st\.session_state\.inventory_df, st\.session_state\.inventory_sheet = fetch_inventory_from_cloud\(\)\n        st\.session_state\.data_loaded = True',
    load_data_chunk,
    text
)

# 4. Pull finance memory map
memory_map_chunk = """inventory_df = st.session_state.inventory_df
inventory_sheet = st.session_state.inventory_sheet
finance_data = st.session_state.finance_data
finance_sheet = st.session_state.finance_sheet"""

text = re.sub(
    r'inventory_df = st\.session_state\.inventory_df\ninventory_sheet = st\.session_state\.inventory_sheet',
    memory_map_chunk,
    text
)

# 5. Insert Finance UI
finance_ui = """elif st.session_state.current_view == "פיננסי":
    st.title("💰 ניהול פיננסי")
    
    if finance_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Finance' ב-Google Sheets. אנא צרי אותו כדי להתחיל לשמור נתונים פיננסיים.")
    else:
        st.markdown("---")
        
        user_settings = finance_data["settings"]
        currency = "₪"  # Currency fixed to ILS by default as requested
        
        english_months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        hebrew_months = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
        hebrew_to_english = dict(zip(hebrew_months, english_months))
        english_to_hebrew = dict(zip(english_months, hebrew_months))
        
        year_options = list(range(2025, 2035))
        
        col_y, col_m = st.columns([1, 4])
        with col_y:
            selected_year = st.selectbox("שנה", options=year_options, index=1)
        with col_m:
            selected_month_heb = st.radio("חודש", options=hebrew_months, horizontal=True, label_visibility="collapsed")
            selected_month = hebrew_to_english[selected_month_heb]
            
        st.markdown(f"<h3 style='text-align: center; margin-bottom: 1rem;'>דו״ח פיננסי - {selected_month_heb} {selected_year}</h3>", unsafe_allow_html=True)
        
        month_state_key = f"{selected_year}-{selected_month}"
        month_index = english_months.index(selected_month) + 1
        finance_data["monthly_expenses"].setdefault(month_state_key, [])
        expenses_for_month = finance_data["monthly_expenses"][month_state_key]
        
        # Pull automated income from Orders Tab
        # Scan orders_df for Payment Status == "🟢" and Order Date matching this month/year.
        automated_incomes = []
        if not orders_df.empty and "Payment Status" in orders_df.columns:
            paid_orders = orders_df[orders_df["Payment Status"] == "🟢"].copy()
            if not paid_orders.empty:
                paid_orders["Order Date_dt"] = pd.to_datetime(paid_orders["Order Date"], format="%d/%m/%Y", errors="coerce")
                paid_orders = paid_orders.dropna(subset=["Order Date_dt"])
                
                paid_this_month = paid_orders[
                    (paid_orders["Order Date_dt"].dt.year == selected_year) & 
                    (paid_orders["Order Date_dt"].dt.month == month_index)
                ]
                
                for _, ro in paid_this_month.iterrows():
                    price_val = pd.to_numeric(ro.get("Price", 0), errors='coerce')
                    if pd.notnull(price_val) and price_val > 0:
                        automated_incomes.append({
                            "name": f"הזמנה #{ro.get('Order ID', '?')} - {ro.get('Customer Name', '')}",
                            "amount": float(price_val),
                            "Type": "Income",
                            "is_automated": True
                        })
        
        combined_expenses_for_month = expenses_for_month + automated_incomes
        
        current_settings = finance_data["month_settings"].get(month_state_key)
        is_confirmed = current_settings is not None
        default_status = "Working Month" if not is_confirmed else current_settings["employment_status"]
        default_funds = 0.0 if not is_confirmed else float(current_settings["available_funds"])
        
        settings_container = st.container() if not is_confirmed else st.expander("⚙️ עריכת תקציב חודשי", expanded=False)
        with settings_container:
            funds_label = "הכנסה צפויה" if default_status == "Working Month" else "תקציב חודשי מוגדר"
            available_funds = st.number_input(
                f"{funds_label} ({currency})",
                min_value=0.0,
                step=1.0,
                value=float(default_funds),
                key=f"funds_input_{month_state_key}"
            )
            if st.button("אישור תקציב", key=f"confirm_{month_state_key}"):
                finance_data["month_settings"][month_state_key] = {
                    "employment_status": "Working Month",
                    "available_funds": float(available_funds),
                }
                save_finance_data(finance_data)
                st.rerun()
                
        current_settings = finance_data["month_settings"].get(month_state_key)
        if current_settings:
            effective_status = current_settings["employment_status"]
            base_funds = float(current_settings["available_funds"])
            st.markdown(f"**תקציב התחלתי / משוער:** {currency}{base_funds:,.2f}")
        else:
            effective_status = "Working Month"
            base_funds = float(available_funds)
            st.markdown("**תקציב בסיס מוגדר:** טרם אושר")
            
        active_standing_orders = [o for o in finance_data["standing_orders"] if is_standing_order_active(o, selected_year, month_index)]
        standing_orders_total = sum(float(o["amount"]) for o in active_standing_orders)
        
        expenses_tab, standing_orders_tab = st.tabs(["💸 תנועות והוצאות", "🔄 הוראות קבע"])
        
        with expenses_tab:
            left_col, right_col = st.columns([1, 1], gap="large")
            with left_col:
                st.subheader("הוספת תנועה ידנית")
                transaction_name = st.text_input("שם התנועה", key=f"expense_name_{month_state_key}")
                transaction_type = st.selectbox("סוג התנועה", options=["Expense", "Income"], format_func=lambda x: "הוצאה" if x=="Expense" else "הכנסה", key=f"transaction_type_{month_state_key}")
                transaction_amount = st.number_input(f"סכום ({currency})", min_value=0.0, step=1.0, value=0.0, key=f"expense_amount_{month_state_key}")
                if st.button("הוספי תנועה", key=f"add_expense_{month_state_key}", use_container_width=True):
                    if transaction_name.strip() and transaction_amount > 0:
                        expenses_for_month.append({
                            "name": transaction_name.strip(),
                            "amount": float(transaction_amount),
                            "Type": transaction_type
                        })
                        save_finance_data(finance_data)
                        st.rerun()
                    else:
                        st.warning("נא להזין שם תקין וסכום גדול מ-0.")
                        
                st.subheader("רשימת תנועות לחודש זה")
                if combined_expenses_for_month:
                    for idx, expense in enumerate(combined_expenses_for_month):
                        is_auto = expense.get('is_automated', False)
                        item_type = expense.get("Type", "Expense")
                        row_1, row_2, row_3, row_4 = st.columns([4, 3, 2, 1])
                        row_1.markdown(f"<div style='text-align: right;'>{expense['name']} {('✨' if is_auto else '')}</div>", unsafe_allow_html=True)
                        amount_html = f"<span style='color: #22c55e;'>+{expense['amount']:.1f}</span>" if item_type == "Income" else f"<span style='color: #ef4444;'>{expense['amount']:.1f}</span>"
                        row_2.markdown(f"<div style='text-align: center;'>{amount_html}</div>", unsafe_allow_html=True)
                        type_str = "הכנסה אוטו'" if is_auto else ("הכנסה" if item_type == "Income" else "הוצאה")
                        row_3.markdown(f"<div style='text-align: center;'>{type_str}</div>", unsafe_allow_html=True)
                        if not is_auto:
                            if row_4.button("❌", key=f"del_exp_{month_state_key}_{idx}"):
                                if expense in expenses_for_month:
                                    expenses_for_month.remove(expense)
                                    save_finance_data(finance_data)
                                    st.rerun()
                        else:
                            row_4.write("")
                else:
                    st.info("אין תנועות (הוצאות/הכנסות) בחודש זה.")
                    
                if active_standing_orders:
                    st.subheader("הוראות קבע בחודש זה")
                    for active_idx, order in enumerate(active_standing_orders):
                        s_row1, s_row2, s_row3 = st.columns([5, 3, 2])
                        s_row1.markdown(f"<div style='text-align: right;'>{order['name']}</div>", unsafe_allow_html=True)
                        s_row2.markdown(f"<div style='text-align: center; color:#ef4444;'>{float(order['amount']):.1f} {currency}</div>", unsafe_allow_html=True)
                        s_row3.markdown(f"<div style='text-align: center;'>הוצאה</div>", unsafe_allow_html=True)
            
            with right_col:
                extra_income = sum(float(item["amount"]) for item in combined_expenses_for_month if item.get("Type", "Expense") == "Income")
                manual_expenses_total = sum(float(item["amount"]) for item in combined_expenses_for_month if item.get("Type", "Expense") == "Expense")
                effective_available_funds = base_funds
                total_expenses = manual_expenses_total + standing_orders_total
                remaining_funds = effective_available_funds + extra_income - total_expenses
                
                st.subheader("סקירת יתרה חודשית")
                # Removed 'base_funds' from total context visually since business mostly relies on income, but kept it for those who log 'seed budget'
                st.markdown(f"**תקציב בסיסי שהוגדר:** {currency}{effective_available_funds:,.2f}")
                st.markdown(f"**הכנסות נוספות (הזמנות/ידני):** <span style='color:#22c55e;'>+{currency}{extra_income:,.2f}</span>", unsafe_allow_html=True)
                st.markdown(f"**כלל ההוצאות החודש:** <span style='color:#ef4444;'>-{currency}{total_expenses:,.2f}</span>", unsafe_allow_html=True)
                st.markdown(f"**יתרה נותרת לחודש זה:** {currency}{remaining_funds:,.2f}")
                
                
                hebrew_category_map = {
                    "Expenses": "הוצאות",
                    "Remaining Budget": "יתרה/הכנסה פנויה",
                    "Deficit (Over Budget)": "חריגה מהתקציב (מינוס)"
                }
                
                total_pool = effective_available_funds + extra_income
                if total_expenses > total_pool:
                    deficit = total_expenses - total_pool
                    budget_chart_rows = [
                        {"Category": "Expenses", "Value": total_expenses},
                        {"Category": "Deficit (Over Budget)", "Value": deficit},
                    ]
                    budget_colors = {"Expenses": "#ff8c00", "Deficit (Over Budget)": "#ffb347"}
                else:
                    budget_chart_rows = [
                        {"Category": "Expenses", "Value": total_expenses},
                        {"Category": "Remaining Budget", "Value": remaining_funds},
                    ]
                    budget_colors = {"Expenses": "#ef4444", "Remaining Budget": "#22c55e"}
                    
                budget_df_chart = pd.DataFrame(budget_chart_rows)
                budget_df_chart["Hebrew_Category"] = budget_df_chart["Category"].map(hebrew_category_map)
                
                # Check if we have anything to show
                if total_pool > 0 or total_expenses > 0:
                    budget_pie_chart = px.pie(
                        budget_df_chart,
                        names="Category",
                        values="Value",
                        color="Category",
                        color_discrete_map=budget_colors,
                        hole=0.35,
                    )
                    budget_pie_chart.update_traces(
                        customdata=budget_df_chart["Hebrew_Category"],
                        textposition="inside",
                        textinfo="percent+label",
                        hovertemplate="%{customdata}<br>סכום: %{value:.1f} " + currency + "<extra></extra>",
                    )
                    budget_pie_chart.update_layout(
                        margin=dict(t=20, b=20, l=20, r=20),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(budget_pie_chart, use_container_width=True)

        with standing_orders_tab:
            st.subheader("ניהול הוראות קבע (הוצאות קבועות)")
            col_so1, col_so2, col_so3 = st.columns(3)
            with col_so1: order_name = st.text_input("שם ההוראה", key="standing_name")
            with col_so2: order_amount = st.number_input(f"סכום ההוצאה ({currency})", min_value=0.0, step=1.0, value=0.0, key="standing_amount")
            with col_so3: order_frequency = st.selectbox("תדירות חיוב", options=["Monthly", "Yearly"], format_func=lambda x: "חודשי" if x=="Monthly" else "שנתי", key="standing_frequency")
            
            c_d1, c_d2 = st.columns(2)
            with c_d1: order_start_date = st.date_input("תאריך התחלה", value=date.today(), key="standing_start")
            with c_d2: order_end_date = st.date_input("תאריך סיום מוערך", value=date(2035, 12, 31), key="standing_end")
            
            if st.button("הוספי הוראת קבע", type="primary", use_container_width=True):
                if not order_name.strip():
                    st.warning("נא להזין שם.")
                elif order_amount <= 0:
                    st.warning("נא להזין סכום חיובי.")
                elif order_end_date < order_start_date:
                    st.warning("תאריך סיום לא יכול להיות לפני תאריך התחלה.")
                else:
                    finance_data["standing_orders"].append({
                        "name": order_name.strip(),
                        "amount": float(order_amount),
                        "frequency": order_frequency,
                        "start_date": order_start_date.isoformat(),
                        "end_date": order_end_date.isoformat(),
                    })
                    save_finance_data(finance_data)
                    st.rerun()
            
            st.markdown("---")
            st.subheader("רשימת הוראות הקבע של הסטודיו")
            if finance_data["standing_orders"]:
                for idx, order in enumerate(finance_data["standing_orders"]):
                    c1, c2, c3, c4 = st.columns([3, 2, 4, 1])
                    c1.markdown(f"**{order['name']}**")
                    c2.markdown(f"<div style='color:#ef4444;'>{float(order['amount']):.1f} {currency}</div>", unsafe_allow_html=True)
                    c3.markdown(f"{order['start_date']} עד {order['end_date']}")
                    if c4.button("❌", key=f"delete_standing_{idx}"):
                        finance_data["standing_orders"].pop(idx)
                        save_finance_data(finance_data)
                        st.rerun()
            else:
                st.info("אין הוראות קבע פעילות.")
"""

text = re.sub(
    r'elif st\.session_state\.current_view == "פיננסי":[\r\n\s]*st\.title\("💰 ניהול פיננסי"\)',
    finance_ui,
    text
)

with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Injected successfully!")
