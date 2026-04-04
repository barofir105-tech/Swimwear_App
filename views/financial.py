import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from calendar import monthrange
import uuid
from utils import save_finance_data, get_standing_order_hits


def render_financial():
    finance_data = st.session_state.finance_data
    finance_sheet = st.session_state.finance_sheet
    orders_df = st.session_state.orders_df

    st.title("💰 ניהול פיננסי ומאזן עסק")

    if finance_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Finance' ב-Google Sheets. אנא צרי אותו כדי להתחיל לשמור נתונים פיננסיים.")
    else:
        st.markdown("---")

        user_settings = finance_data.get("settings", {})
        currency = "₪"

        # Data Migration to Flat Transactions
        import uuid
        if "transactions" not in finance_data:
            finance_data["transactions"] = []
            english_months_mig = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            for m_key, m_items in finance_data.get("monthly_expenses", {}).items():
                try:
                    yr, mo_name = m_key.split("-")
                    mo_idx = english_months_mig.index(mo_name) + 1
                    mig_date = f"{yr}-{mo_idx:02d}-01"
                    for itm in m_items:
                        finance_data["transactions"].append({
                            "id": str(uuid.uuid4()),
                            "name": itm.get("name", ""),
                            "amount": float(itm.get("amount", 0)),
                            "Type": itm.get("Type", "Expense"),
                            "date": mig_date
                        })
                except:
                    pass
            save_finance_data(finance_data)

        # UI: Dashboard View Selectors
        st.markdown("### בחירת סקירה")
        view_mode = st.radio("סוג תצוגה:", ["סקירה חודשית", "טווח תאריכים מותאם אישית"], horizontal=True, label_visibility="collapsed")

        if view_mode == "סקירה חודשית":
            english_months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            hebrew_months = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
            hebrew_to_english = dict(zip(hebrew_months, english_months))
            year_options = list(range(2025, 2035))
            current_dt = datetime.now()
            cur_year_idx = year_options.index(current_dt.year) if current_dt.year in year_options else 1
            cur_month_idx = current_dt.month - 1

            c_y, c_m = st.columns([1, 2])
            with c_y:
                selected_year = st.selectbox("שנה", options=year_options, index=cur_year_idx)
            with c_m:
                selected_month_heb = st.selectbox("חודש", options=hebrew_months, index=cur_month_idx)
                selected_month = hebrew_to_english[selected_month_heb]

            month_index = english_months.index(selected_month) + 1
            from calendar import monthrange
            _, last_day = monthrange(selected_year, month_index)
            range_start = date(selected_year, month_index, 1)
            range_end = date(selected_year, month_index, last_day)

            st.markdown(f"<h3 style='text-align: center; margin-bottom: 2rem;'>דו״ח פיננסי - {selected_month_heb} {selected_year}</h3>", unsafe_allow_html=True)

        else:
            curr_date = date.today()
            first_of_month = curr_date.replace(day=1)
            date_range = st.date_input("בחר טווח תאריכים לסקירה", value=(first_of_month, curr_date))

            if isinstance(date_range, tuple) and len(date_range) == 2:
                range_start, range_end = date_range
                st.markdown(f"<h3 style='text-align: center; margin-bottom: 2rem;'>דו״ח ביצועים ({range_start.strftime('%d/%m/%Y')} - {range_end.strftime('%d/%m/%Y')})</h3>", unsafe_allow_html=True)
            else:
                st.warning("אנא בחר טווח תאריכים מלא (התחלה וסיום) לבניית הדו״ח.")
                st.stop()

        # --- Aggregation Engine ---
        def get_standing_order_hits(order, rng_start, rng_end):
            try:
                so_start = pd.to_datetime(order["start_date"]).date()
                so_end = pd.to_datetime(order["end_date"]).date()
            except:
                return 0

            actual_end = min(rng_end, so_end)
            if rng_start > actual_end: return 0
            if so_start > rng_end: return 0

            curr = pd.to_datetime(so_start)
            actual_end_dt = pd.to_datetime(actual_end)
            rng_start_dt = pd.to_datetime(rng_start)

            hits = 0
            freq = order.get("frequency", "Monthly")
            if freq == "Monthly":
                offset = pd.DateOffset(months=1)
            elif freq == "Yearly":
                offset = pd.DateOffset(years=1)
            elif freq == "Custom":
                val = int(order.get("custom_interval", 1))
                unit = order.get("custom_unit", "Months")
                if unit == "Days": offset = pd.DateOffset(days=val)
                elif unit == "Weeks": offset = pd.DateOffset(weeks=val)
                elif unit == "Months": offset = pd.DateOffset(months=val)
                elif unit == "Years": offset = pd.DateOffset(years=val)
                else: offset = pd.DateOffset(months=1)
            else:
                offset = pd.DateOffset(months=1)

            if freq == "Custom" and val <= 0: offset = pd.DateOffset(months=1)

            while curr <= actual_end_dt:
                if curr >= rng_start_dt:
                    hits += 1
                curr += offset

            return hits

        # 1. Gather Automated Incomes
        automated_incomes = []
        if not orders_df.empty and "Payment Status" in orders_df.columns:
            if "Payment Date" not in orders_df.columns:
                orders_df["Payment Date"] = orders_df["Order Date"]

            paid_orders = orders_df[orders_df["Payment Status"] == "💚"].copy()
            if not paid_orders.empty:
                paid_orders["Parsed Date"] = paid_orders.apply(
                    lambda r: pd.to_datetime(r["Payment Date"], format="%d/%m/%Y", errors="coerce").date() if pd.notnull(r.get("Payment Date")) and str(r.get("Payment Date")).strip() != "" 
                    else pd.to_datetime(r["Order Date"], format="%d/%m/%Y", errors="coerce").date(),
                    axis=1
                )
                paid_orders = paid_orders.dropna(subset=["Parsed Date"])

                paid_in_range = paid_orders[
                    (paid_orders["Parsed Date"] >= range_start) & 
                    (paid_orders["Parsed Date"] <= range_end)
                ]

                for _, ro in paid_in_range.iterrows():
                    price_val = pd.to_numeric(ro.get("Price", 0), errors='coerce')
                    if pd.notnull(price_val) and price_val > 0:
                        automated_incomes.append({
                            "name": f"הזמנה #{ro.get('Order ID', '?')} - {ro.get('Customer Name', '')}",
                            "amount": float(price_val),
                            "Type": "Income",
                            "Item": str(ro.get("Item", "כללי")),
                            "date": ro["Parsed Date"].strftime("%Y-%m-%d"),
                            "is_automated": True
                        })

        # 2. Gather Manual Transactions
        manual_in_range = []
        for txn in finance_data.get("transactions", []):
            try:
                txn_date = datetime.strptime(txn.get("date", "2000-01-01"), "%Y-%m-%d").date()
                if range_start <= txn_date <= range_end:
                    manual_in_range.append(txn)
            except:
                pass

        # 3. Gather Standing Orders 
        so_in_range = []
        standing_orders_total = 0
        for o in finance_data.get("standing_orders", []):
            hits = get_standing_order_hits(o, range_start, range_end)
            if hits > 0:
                amount_hit = float(o.get("amount", 0)) * hits
                standing_orders_total += amount_hit
                o_clone = o.copy()
                o_clone["amount"] = amount_hit
                so_in_range.append(o_clone)

        # Totals
        extra_income = sum(float(x.get("amount", 0)) for x in manual_in_range if x.get("Type") == "Income") + sum(float(x["amount"]) for x in automated_incomes)
        manual_expenses_total = sum(float(x.get("amount", 0)) for x in manual_in_range if x.get("Type") == "Expense")
        total_expenses = manual_expenses_total + standing_orders_total
        net_balance = extra_income - total_expenses

        st.markdown(f"""
        <div style="display: flex; justify-content: space-around; background-color: rgba(245,245,245,0.7); padding: 20px; border-radius: 10px; margin-bottom: 2rem; border: 1px solid #ddd;">
            <div style="text-align: center;">
                <h4 style="margin:0; color: #555;">הוצאות</h4>
                <h2 style="margin:0; color: #ef4444;">{total_expenses:,.0f} {currency}</h2>
            </div>
            <div style="text-align: center; border-right: 2px solid #ddd; padding-right: 30px;">
                <h4 style="margin:0; color: #555;">הכנסות</h4>
                <h2 style="margin:0; color: #22c55e;">{extra_income:,.0f} {currency}</h2>
            </div>
            <div style="text-align: center; border-right: 2px solid #ddd; padding-right: 30px;">
                <h4 style="margin:0; color: #555;">מאזן נטו</h4>
                <h2 style="margin:0; color: {'#22c55e' if net_balance >= 0 else '#ef4444'};">{net_balance:,.0f} {currency}</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
                st.markdown("<h4 style='text-align: center;'>פילוח תצרוכת הוצאות</h4>", unsafe_allow_html=True)
                exp_rows = [{"Category": item.get("name", "כללי"), "Value": float(item.get("amount", 0))} for item in manual_in_range if item.get("Type") == "Expense"]
                exp_rows.extend([{"Category": o.get("name", "הוראת קבע"), "Value": float(o.get("amount", 0))} for o in so_in_range])

                if exp_rows:
                    exp_df = pd.DataFrame(exp_rows).groupby("Category", as_index=False).sum()
                    fig_exp = px.pie(exp_df, names="Category", values="Value", hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
                    fig_exp.update_traces(textinfo="label+percent", textposition="inside", hovertemplate="%{label}: %{value} " + currency + "<extra></extra>")
                    fig_exp.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
                    st.plotly_chart(fig_exp, use_container_width=True)
                else:
                    st.info("אין הוצאות להצגה.")

            with c_inc:
                st.markdown("<h4 style='text-align: center;'>פילוח דגמים והכנסות</h4>", unsafe_allow_html=True)
                inc_rows = [{"Category": item.get("name", "הכנסה ידנית"), "Value": float(item.get("amount", 0))} for item in manual_in_range if item.get("Type") == "Income"]
                for a in automated_incomes:
                    cat_name = a.get("Item", "כללי")
                    if str(cat_name).strip() == "": cat_name = "כללי"
                    inc_rows.append({"Category": cat_name, "Value": float(a.get("amount", 0))})

                if inc_rows:
                    inc_df = pd.DataFrame(inc_rows).groupby("Category", as_index=False).sum()
                    fig_inc = px.pie(inc_df, names="Category", values="Value", hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
                    fig_inc.update_traces(textinfo="label+percent", textposition="inside", hovertemplate="%{label}: %{value} " + currency + "<extra></extra>")
                    fig_inc.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
                    st.plotly_chart(fig_inc, use_container_width=True)
                else:
                    st.info("אין הכנסות להצגה.")

        st.markdown("---")

        expenses_tab, standing_orders_tab = st.tabs(["💸 תנועות ידניות", "🔄 הוצאות שוטפות"])

        with expenses_tab:
            st.subheader("הוספת תנועה חדשה")
            with st.form("add_txn_form", clear_on_submit=True):
                col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
                with col_f1: transaction_name = st.text_input("שם התנועה/קטגוריה (למשל: בדים / משלוח)")
                with col_f2: transaction_type = st.selectbox("סוג", ["Expense", "Income"], format_func=lambda x: "הוצאה" if x=="Expense" else "הכנסה")
                with col_f3: transaction_amount = st.number_input(f"סכום ({currency})", min_value=0.0, step=1.0)
                with col_f4: transaction_date = st.date_input("תאריך", value=date.today())

                if st.form_submit_button("➕ הוסיפי תנועה", use_container_width=True):
                    if transaction_name.strip() and transaction_amount > 0:
                        finance_data["transactions"].append({
                            "id": str(uuid.uuid4()),
                            "name": transaction_name.strip(),
                            "amount": float(transaction_amount),
                            "Type": transaction_type,
                            "date": transaction_date.strftime("%Y-%m-%d")
                        })
                        save_finance_data(finance_data)
                        st.toast("התנועה נוספה!", icon="✅")
                        st.rerun()
                    else:
                        st.warning("נא להזין שם תקין וסכום.")

            st.markdown("### 📋 טבלת תנועות")
            if finance_data.get("transactions", []):
                txn_df = pd.DataFrame(finance_data.get("transactions", []))

                if st.session_state.get("delete_mode_txn", False) == True:
                    txn_df["בחרי"] = False

                txn_df["date_ts"] = pd.to_datetime(txn_df["date"], errors="coerce")
                txn_df = txn_df.sort_values(by="date_ts", ascending=False)

                txn_display = txn_df[["id"]].copy()
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
                    "תאריך": st.column_config.DateColumn("תאריך", format="DD/MM/YYYY", width="small"),
                    "סוג": st.column_config.SelectboxColumn("סוג", options=["הוצאה", "הכנסה"], width="small"),
                    "סכום": st.column_config.NumberColumn("סכום", format="₪%d", width="small")
                }

                edited_txn = st.data_editor(txn_display.drop("id", axis=1), use_container_width=True, hide_index=True, column_config=conf, key="txn_editor")
                edited_txn["id"] = txn_display["id"]

                c_del, c_save, c_sel = st.columns([6, 2, 2])
                with c_sel:
                    if not st.session_state.get("delete_mode_txn", False):
                        if st.button("בחרי למחיקה", key="sel_t", use_container_width=True):
                            st.session_state.delete_mode_txn = True; st.rerun()
                    else:
                        if st.button("בטלי בחירה", key="canc_t", use_container_width=True):
                            st.session_state.delete_mode_txn = False; st.rerun()

                with c_save:
                    if st.session_state.get("delete_mode_txn", False):
                        to_del = edited_txn[edited_txn["בחרי"] == True]
                        if not to_del.empty:
                            if st.button("מחקי מסומנות 🗑️", type="primary", use_container_width=True):
                                ids_to_del = to_del["id"].tolist()
                                finance_data["transactions"] = [x for x in finance_data["transactions"] if x["id"] not in ids_to_del]
                                save_finance_data(finance_data)
                                st.session_state.delete_mode_txn = False
                                st.rerun()
                    else:
                        if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                            for _, r in edited_txn.iterrows():
                                for t in finance_data["transactions"]:
                                    if t["id"] == r["id"]:
                                        t["name"] = str(r["שם התנועה"])
                                        t["amount"] = float(r["סכום"])
                                        t["Type"] = "Expense" if r["סוג"] == "הוצאה" else "Income"
                                        if pd.notnull(r["תאריך"]):
                                            t["date"] = r["תאריך"].strftime("%Y-%m-%d") 
                            save_finance_data(finance_data)
                            st.toast("המידע התעדכן במערכת!", icon="✅")
                            st.rerun()

            else:
                st.info("אין תנועות במערכת ברשימה ההסטורית.")

        with standing_orders_tab:
            st.subheader("ניהול הוצאות קבועות")
            with st.form("add_so_form", clear_on_submit=True):
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1: order_name = st.text_input("שם ההוצאה הקבועה")
                with col_s2: order_amount = st.number_input(f"סכום חיוב ({currency})", min_value=0.0, step=1.0)
                with col_s3: order_frequency = st.selectbox("תדירות חיוב", ["Monthly", "Yearly", "Custom"], format_func=lambda x: {"Monthly": "חודשית", "Yearly": "שנתית", "Custom": "מותאם אישית"}[x])

                st.caption("אם בחרת 'מותאם אישית', נא למלא (למשל כל 3 חודשים):")
                col_s4, col_s5 = st.columns(2)
                with col_s4: val_c = st.number_input("מספר", min_value=1, step=1)
                with col_s5: unit_c = st.selectbox("תקופה", ["Days", "Weeks", "Months", "Years"], format_func=lambda x: {"Days": "ימים", "Weeks": "שבועות", "Months": "חודשים", "Years": "שנים"}[x])

                c_d1, c_d2 = st.columns(2)
                with c_d1: order_start_date = st.date_input("תאריך התחלה", value=date.today())
                with c_d2: order_end_date = st.date_input("תאריך סיום", value=date(2035, 12, 31))

                if st.form_submit_button("הוסיפי הוראת קבע", use_container_width=True):
                    if order_name.strip() and order_amount > 0:
                        finance_data["standing_orders"].append({
                            "id": str(uuid.uuid4()),
                            "name": order_name.strip(),
                            "amount": float(order_amount),
                            "frequency": order_frequency,
                            "custom_interval": val_c,
                            "custom_unit": unit_c,
                            "start_date": order_start_date.strftime("%Y-%m-%d"),
                            "end_date": order_end_date.strftime("%Y-%m-%d"),
                        })
                        save_finance_data(finance_data)
                        st.toast("הוראת הקבע נוספה!", icon="✅")
                        st.rerun()
                    else:
                        st.warning("נא להזין שם תקני וסכום.")

            st.markdown("### 📋 עריכת הוראות קבע")
            if finance_data.get("standing_orders", []):
                for so in finance_data["standing_orders"]:
                    if "id" not in so: so["id"] = str(uuid.uuid4())

                so_df = pd.DataFrame(finance_data.get("standing_orders", []))

                if st.session_state.get("delete_mode_so", False) == True:
                    so_df["בחרי"] = False

                so_disp = so_df[["id"]].copy()

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
                if "בחרי" in so_df.columns: so_disp["בחרי"] = so_df["בחרי"]

                conf = {
                    "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "שם ההוצאה": st.column_config.TextColumn("שם ההוצאה", disabled=True),
                    "תדירות": st.column_config.TextColumn("תדירות", disabled=True),
                    "סכום": st.column_config.NumberColumn("סכום (₪)", disabled=True),
                    "התחלה": st.column_config.DateColumn("התחלה", format="DD/MM/YYYY", disabled=True),
                    "סיום": st.column_config.DateColumn("סיום", format="DD/MM/YYYY", disabled=True)
                }

                edited_so = st.data_editor(so_disp.drop("id", axis=1), use_container_width=True, hide_index=True, column_config=conf, key="so_editor")
                edited_so["id"] = so_disp["id"]

                c_del_s, c_emp_s, c_sel_s = st.columns([6, 2, 2])
                with c_sel_s:
                    if not st.session_state.get("delete_mode_so", False):
                        if st.button("בחרי למחיקה", key="so_sel", use_container_width=True):
                            st.session_state.delete_mode_so = True; st.rerun()
                    else:
                        if st.button("בטלי בחירה", key="canc_so", use_container_width=True):
                            st.session_state.delete_mode_so = False; st.rerun()

                with c_emp_s:
                    if st.session_state.get("delete_mode_so", False):
                        to_del = edited_so[edited_so["בחרי"] == True]
                        if not to_del.empty:
                            if st.button("מחקים 🗑️", type="primary", use_container_width=True):
                                ids_to_del = to_del["id"].tolist()
                                finance_data["standing_orders"] = [x for x in finance_data["standing_orders"] if x["id"] not in ids_to_del]
                                save_finance_data(finance_data)
                                st.session_state.delete_mode_so = False
                                st.rerun()
            else:
                st.info("אין הוראות קבע פעילות.")


