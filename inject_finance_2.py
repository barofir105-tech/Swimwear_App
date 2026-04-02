import sys
import re

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add "Payment Date" to fetch_orders_from_cloud
fetch_orders_old = """        if not df.empty and "Phone Number" in df.columns:
            df["Phone Number"] = df["Phone Number"].astype(str).apply(lambda x: '0' + x if len(x) == 9 and not x.startswith('0') else x)
        else:
            df = pd.DataFrame(columns=["Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item", "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Status", "Payment Status", "Supply Type", "Price"])
        return df, sheet
    except:
        return pd.DataFrame(columns=["Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item", "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Status", "Payment Status", "Supply Type", "Price"]), None"""

fetch_orders_new = """        if not df.empty and "Phone Number" in df.columns:
            df["Phone Number"] = df["Phone Number"].astype(str).apply(lambda x: '0' + x if len(x) == 9 and not x.startswith('0') else x)
            if "Payment Date" not in df.columns:
                df["Payment Date"] = ""
        else:
            df = pd.DataFrame(columns=["Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item", "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Status", "Payment Status", "Supply Type", "Price", "Payment Date"])
        return df, sheet
    except:
        return pd.DataFrame(columns=["Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item", "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Status", "Payment Status", "Supply Type", "Price", "Payment Date"]), None"""

text = text.replace(fetch_orders_old, fetch_orders_new)

# 2. Add Payment Date logic parsing in Orders Save Logic
save_orders_old = """                                save_orders = save_orders.rename(columns={
                                    "מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "שם לקוחה": "Customer Name", "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage"
                                })
                                
                                orders_indexed = orders_df.set_index("Order ID")
                                save_indexed = save_orders.set_index("Order ID")
                                orders_indexed.update(save_indexed)
                                orders_indexed.reset_index(inplace=True)
                                
                                final_save = orders_indexed[["Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item", "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Status", "Payment Status", "Supply Type", "Price"]]"""

save_orders_new = """                                save_orders = save_orders.rename(columns={
                                    "מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "שם לקוחה": "Customer Name", "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage"
                                })
                                
                                orders_indexed = orders_df.set_index("Order ID")
                                save_indexed = save_orders.set_index("Order ID")
                                
                                # Dynamic Payment Date calculation
                                if "Payment Date" not in orders_indexed.columns:
                                    orders_indexed["Payment Date"] = ""
                                if "Payment Date" not in save_indexed.columns:
                                    save_indexed["Payment Date"] = ""
                                
                                today_str = datetime.now().strftime("%d/%m/%Y")
                                for order_id, row in save_indexed.iterrows():
                                    if row["Payment Status"] == "🟢":
                                        old_status = orders_indexed.loc[order_id, "Payment Status"] if order_id in orders_indexed.index else ""
                                        old_date = orders_indexed.loc[order_id, "Payment Date"] if order_id in orders_indexed.index else ""
                                        
                                        if old_status != "🟢" or pd.isna(old_date) or str(old_date).strip() == "":
                                            save_indexed.at[order_id, "Payment Date"] = today_str
                                        else:
                                            save_indexed.at[order_id, "Payment Date"] = old_date
                                    else:
                                        save_indexed.at[order_id, "Payment Date"] = ""
                                
                                orders_indexed.update(save_indexed)
                                orders_indexed.reset_index(inplace=True)
                                
                                final_save = orders_indexed[["Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item", "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Status", "Payment Status", "Supply Type", "Price", "Payment Date"]]"""

text = text.replace(save_orders_old, save_orders_new)

# 3. New Finance Module Replacement
finance_ui_regex = r'elif st\.session_state\.current_view == "פיננסי":[\s\S]*?(?=# ==========================================\n#               מסך הלקוחות|\Z)'

finance_ui_new = """elif st.session_state.current_view == "פיננסי":
    st.title("💰 ניהול פיננסי ומאזן עסק")
    
    if finance_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Finance' ב-Google Sheets. אנא צרי אותו כדי להתחיל לשמור נתונים פיננסיים.")
    else:
        st.markdown("---")
        
        user_settings = finance_data["settings"]
        currency = "₪"
        
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
            
        st.markdown(f"<h3 style='text-align: center; margin-bottom: 2rem;'>דו״ח פיננסי - {selected_month_heb} {selected_year}</h3>", unsafe_allow_html=True)
        
        month_state_key = f"{selected_year}-{selected_month}"
        month_index = english_months.index(selected_month) + 1
        finance_data["monthly_expenses"].setdefault(month_state_key, [])
        expenses_for_month = finance_data["monthly_expenses"][month_state_key]
        
        automated_incomes = []
        if not orders_df.empty and "Payment Status" in orders_df.columns:
            if "Payment Date" not in orders_df.columns:
                orders_df["Payment Date"] = orders_df["Order Date"]
            
            paid_orders = orders_df[orders_df["Payment Status"] == "🟢"].copy()
            if not paid_orders.empty:
                # Use Payment Date for categorizing
                paid_orders["Parsed Date"] = paid_orders.apply(
                    lambda r: pd.to_datetime(r["Payment Date"], format="%d/%m/%Y", errors="coerce") if pd.notnull(r.get("Payment Date")) and str(r.get("Payment Date")).strip() != "" 
                    else pd.to_datetime(r["Order Date"], format="%d/%m/%Y", errors="coerce"),
                    axis=1
                )
                paid_orders = paid_orders.dropna(subset=["Parsed Date"])
                
                paid_this_month = paid_orders[
                    (paid_orders["Parsed Date"].dt.year == selected_year) & 
                    (paid_orders["Parsed Date"].dt.month == month_index)
                ]
                
                for _, ro in paid_this_month.iterrows():
                    price_val = pd.to_numeric(ro.get("Price", 0), errors='coerce')
                    if pd.notnull(price_val) and price_val > 0:
                        automated_incomes.append({
                            "name": f"הזמנה #{ro.get('Order ID', '?')} - {ro.get('Customer Name', '')}",
                            "amount": float(price_val),
                            "Type": "Income",
                            "Item": str(ro.get("Item", "כללי")),
                            "is_automated": True
                        })
        
        combined_expenses_for_month = expenses_for_month + automated_incomes
        
        active_standing_orders = [o for o in finance_data["standing_orders"] if is_standing_order_active(o, selected_year, month_index)]
        standing_orders_total = sum(float(o["amount"]) for o in active_standing_orders)
        
        # Calculate Balances
        extra_income = sum(float(item["amount"]) for item in combined_expenses_for_month if item.get("Type", "Expense") == "Income")
        manual_expenses_total = sum(float(item["amount"]) for item in combined_expenses_for_month if item.get("Type", "Expense") == "Expense")
        total_expenses = manual_expenses_total + standing_orders_total
        net_balance = extra_income - total_expenses
        
        st.markdown(f\"\"\"
        <div style="display: flex; justify-content: space-around; background-color: rgba(245,245,245,0.7); padding: 20px; border-radius: 10px; margin-bottom: 2rem; border: 1px solid #ddd;">
            <div style="text-align: center;">
                <h4 style="margin:0; color: #555;">הוצאות החודש</h4>
                <h2 style="margin:0; color: #ef4444;">{total_expenses:,.0f} {currency}</h2>
            </div>
            <div style="text-align: center; border-right: 2px solid #ddd; padding-right: 30px;">
                <h4 style="margin:0; color: #555;">הכנסות החודש</h4>
                <h2 style="margin:0; color: #22c55e;">{extra_income:,.0f} {currency}</h2>
            </div>
            <div style="text-align: center; border-right: 2px solid #ddd; padding-right: 30px;">
                <h4 style="margin:0; color: #555;">מאזן נטו</h4>
                <h2 style="margin:0; color: {'#22c55e' if net_balance >= 0 else '#ef4444'};">{net_balance:,.0f} {currency}</h2>
            </div>
        </div>
        \"\"\", unsafe_allow_html=True)
        
        # --- Analytics Charts ---
        if extra_income > 0 or total_expenses > 0:
            c_main, c_exp, c_inc = st.columns(3)
            
            with c_main:
                st.markdown("<h4 style='text-align: center;'>מאזן כללי</h4>", unsafe_allow_html=True)
                main_df = pd.DataFrame([
                    {"Category": "הכנסות", "Value": extra_income},
                    {"Category": "הוצאות", "Value": total_expenses}
                ])
                fig_main = px.pie(main_df, names="Category", values="Value", hole=0.4, color="Category", 
                                color_discrete_map={"הכנסות": "#22c55e", "הוצאות": "#ef4444"})
                fig_main.update_traces(textinfo="label+percent", textposition="inside", hovertemplate="%{label}: %{value} " + currency + "<extra></extra>")
                fig_main.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
                st.plotly_chart(fig_main, use_container_width=True)
                
            with c_exp:
                st.markdown("<h4 style='text-align: center;'>פילוח הוצאות לפי קטגוריה</h4>", unsafe_allow_html=True)
                exp_rows = [{"Category": item["name"], "Value": float(item["amount"])} for item in combined_expenses_for_month if item.get("Type", "Expense") == "Expense"]
                exp_rows.extend([{"Category": o["name"], "Value": float(o["amount"])} for o in active_standing_orders])
                
                if exp_rows:
                    exp_df = pd.DataFrame(exp_rows).groupby("Category", as_index=False).sum()
                    fig_exp = px.pie(exp_df, names="Category", values="Value", hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
                    fig_exp.update_traces(textinfo="label+percent", textposition="inside", hovertemplate="%{label}: %{value} " + currency + "<extra></extra>")
                    fig_exp.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
                    st.plotly_chart(fig_exp, use_container_width=True)
                else:
                    st.info("אין הוצאות להצגה החודש.")
                    
            with c_inc:
                st.markdown("<h4 style='text-align: center;'>פילוח דגמים והכנסות</h4>", unsafe_allow_html=True)
                inc_rows = []
                for item in combined_expenses_for_month:
                    if item.get("Type", "Expense") == "Income":
                        cat_name = dict(item).get("Item", "הכנסה ידנית")
                        if cat_name == "": cat_name = "כללי"
                        inc_rows.append({"Category": cat_name, "Value": float(item["amount"])})
                        
                if inc_rows:
                    inc_df = pd.DataFrame(inc_rows).groupby("Category", as_index=False).sum()
                    fig_inc = px.pie(inc_df, names="Category", values="Value", hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
                    fig_inc.update_traces(textinfo="label+percent", textposition="inside", hovertemplate="%{label}: %{value} " + currency + "<extra></extra>")
                    fig_inc.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
                    st.plotly_chart(fig_inc, use_container_width=True)
                else:
                    st.info("אין הכנסות להצגה החודש.")
        
        st.markdown("---")
        
        expenses_tab, standing_orders_tab = st.tabs(["💸 תנועות ידניות", "🔄 הוצאות שוטפות"])
        
        with expenses_tab:
            left_col, right_col = st.columns([1, 1], gap="large")
            with left_col:
                st.subheader("הוספת תנועה ידנית")
                transaction_name = st.text_input("שם התנועה/קטגוריה (למשל: בדים / משלוח)", key=f"expense_name_{month_state_key}")
                transaction_type = st.selectbox("סוג התנועה", options=["Expense", "Income"], format_func=lambda x: "הוצאה" if x=="Expense" else "הכנסה", key=f"transaction_type_{month_state_key}")
                transaction_amount = st.number_input(f"סכום ({currency})", min_value=0.0, step=1.0, value=0.0, key=f"expense_amount_{month_state_key}")
                if st.button("הוסיפי תנועה", type="primary", key=f"add_expense_{month_state_key}", use_container_width=True):
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
                        
            with right_col:
                st.subheader("פעולות ותנועות החודש")
                if combined_expenses_for_month:
                    for idx, expense in enumerate(combined_expenses_for_month):
                        is_auto = expense.get('is_automated', False)
                        item_type = expense.get("Type", "Expense")
                        c1, c2, c3, c4 = st.columns([5, 3, 2, 0.5]) # מרווח אסתטי מוקטן
                        c1.markdown(f"<div style='text-align: right;'>{expense['name']} {('✨' if is_auto else '')}</div>", unsafe_allow_html=True)
                        amount_html = f"<span style='color: #22c55e;'>+{expense['amount']:.1f}</span>" if item_type == "Income" else f"<span style='color: #ef4444;'>-{expense['amount']:.1f}</span>"
                        c2.markdown(f"<div style='text-align: center;'>{amount_html}</div>", unsafe_allow_html=True)
                        type_str = "אוטומטי" if is_auto else ("ידני")
                        c3.markdown(f"<div style='text-align: center; color: gray; font-size: 0.9em;'>{type_str}</div>", unsafe_allow_html=True)
                        if not is_auto:
                            if c4.button("❌", key=f"del_e_{month_state_key}_{idx}", help="מחק תנועה", use_container_width=False):
                                if expense in expenses_for_month:
                                    expenses_for_month.remove(expense)
                                    save_finance_data(finance_data)
                                    st.rerun()
                        else:
                            c4.write("")
                else:
                    st.info("אין תנועות (הוצאות/הכנסות) בחודש זה.")

        with standing_orders_tab:
            st.subheader("ניהול הוצאות שוטפות")
            col_so1, col_so2, col_so3 = st.columns(3)
            with col_so1: order_name = st.text_input("שם ההוצאה", key="standing_name")
            with col_so2: order_amount = st.number_input(f"סכום ההוצאה ({currency})", min_value=0.0, step=1.0, value=0.0, key="standing_amount")
            with col_so3: order_frequency = st.selectbox("תדירות חיוב", options=["Monthly", "Yearly"], format_func=lambda x: "חודשי" if x=="Monthly" else "שנתי", key="standing_frequency")
            
            c_d1, c_d2 = st.columns(2)
            with c_d1: order_start_date = st.date_input("תאריך התחלה", value=date.today(), key="standing_start")
            with c_d2: order_end_date = st.date_input("תאריך סיום מוערך", value=date(2035, 12, 31), key="standing_end")
            
            if st.button("הוסיפי הוצאה קבועה", type="primary", use_container_width=True):
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
            if finance_data["standing_orders"]:
                for idx, order in enumerate(finance_data["standing_orders"]):
                    c1, c2, c3, c4 = st.columns([4, 2, 4, 1])
                    c1.markdown(f"**{order['name']}**")
                    c2.markdown(f"<div style='color:#ef4444;'>-{float(order['amount']):.1f} {currency}</div>", unsafe_allow_html=True)
                    c3.markdown(f"<div style='color: gray;'>מ-{order['start_date']} עד {order['end_date']}</div>", unsafe_allow_html=True)
                    if c4.button("❌", key=f"del_so_{idx}"):
                        finance_data["standing_orders"].pop(idx)
                        save_finance_data(finance_data)
                        st.rerun()
            else:
                st.info("אין הוראות קבע פעילות.")
\n"""

text = re.sub(finance_ui_regex, finance_ui_new, text)

with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Injected successfully!")
