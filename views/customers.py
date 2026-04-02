import streamlit as st
import pandas as pd
from datetime import datetime


def render_customers():
    customers_df = st.session_state.customers_df
    customers_sheet = st.session_state.customers_sheet
    orders_df = st.session_state.orders_df

    st.title("👥 ניהול לקוחות")

    if not customers_df.empty:
        if "Notes" not in customers_df.columns:
            customers_df["Notes"] = ""

        df_display = customers_df.copy()
        df_display["שם"] = (df_display["First Name"].astype(str) + " " + df_display["Last Name"].astype(str)).str.strip()
        df_display = df_display.rename(columns={"Phone Number": "מספר טלפון", "Address": "כתובת", "Notes": "הערות"})

        st.markdown("### 📇 כרטיס לקוחה")
        customer_options = ["בחרי לקוחה..."] + [f"{row['שם']} ({row['מספר טלפון']})" for index, row in df_display.iterrows()]
        selected_option = st.selectbox("בחרי לקוחה להצגת כרטיס אישי והיסטוריית רכישות:", customer_options)

        if selected_option != "בחרי לקוחה...":
            phone_extracted = selected_option.split("(")[-1].replace(")", "")
            st.session_state.selected_customer_phone = phone_extracted
            st.session_state.current_view = "כרטיס_לקוחה"
            st.rerun()

        st.markdown("---")
        st.markdown("### 📋 רשימת הלקוחות")
        search_query = st.text_input("🔍 חפשי לקוחה (לפי שם או טלפון):", "")

        if search_query:
            mask = (df_display["שם"].astype(str).str.contains(search_query, na=False) |
                    df_display["מספר טלפון"].astype(str).str.contains(search_query, na=False))
            filtered_df = df_display[mask].copy()
        else:
            filtered_df = df_display.copy()

        cols = ["הערות", "כתובת", "מספר טלפון", "שם"]

        if st.session_state.delete_mode:
            filtered_df["בחרי"] = False
            cols = ["בחרי"] + cols

        filtered_df = filtered_df[cols]

        column_config = {
            "מספר טלפון": st.column_config.TextColumn("טלפון", width="small"),
            "שם": st.column_config.TextColumn("שם", width="medium"),
            "כתובת": st.column_config.TextColumn("כתובת", width="medium"),
            "הערות": st.column_config.TextColumn("הערות")
        }
        if st.session_state.delete_mode:
            column_config["בחרי"] = st.column_config.CheckboxColumn("בחרי", default=False)

        edited_df = st.data_editor(filtered_df, use_container_width=True, hide_index=True, column_config=column_config)

        col_space, col_btn_save, col_btn_select = st.columns([6, 2, 2])

        with col_btn_select: 
            if not st.session_state.delete_mode:
                if st.button("בחרי", use_container_width=True):
                    st.session_state.delete_mode = True; st.rerun()
            else:
                if st.button("בטלי", use_container_width=True):
                    st.session_state.delete_mode = False; st.rerun()

        with col_btn_save: 
            if st.session_state.delete_mode:
                customers_to_delete = edited_df[edited_df["בחרי"] == True]
                if not customers_to_delete.empty:
                    if st.button("מחקי מסומנות 🗑️", type="primary", use_container_width=True):
                        with st.spinner("מוחק..."):
                            phones_to_delete = customers_to_delete["מספר טלפון"].tolist()
                            st.session_state.customers_df = customers_df[~customers_df["Phone Number"].isin(phones_to_delete)]

                            save_df = st.session_state.customers_df[["Phone Number", "First Name", "Last Name", "Address", "Notes"]]
                            customers_sheet.clear()
                            if save_df.empty: customers_sheet.update([save_df.columns.values.tolist()])
                            else: customers_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())

                            st.session_state.delete_mode = False; st.toast("נמחק!", icon="✅"); st.rerun()
            else:
                if not edited_df.equals(filtered_df):
                    if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                        with st.spinner("שומר מהר..."):
                            full_updated_df = df_display.copy()
                            full_updated_df.update(edited_df)

                            # Split שם back into First Name / Last Name
                            def _split_name(n):
                                parts = str(n).strip().split(" ", 1)
                                return parts[0], parts[1] if len(parts) > 1 else ""
                            if "שם" in full_updated_df.columns:
                                full_updated_df[["First Name", "Last Name"]] = full_updated_df["שם"].apply(
                                    lambda n: pd.Series(_split_name(n)))
                            else:
                                full_updated_df["First Name"] = full_updated_df.get("שם פרטי", "")
                                full_updated_df["Last Name"]  = full_updated_df.get("שם משפחה", "")

                            save_df = full_updated_df.rename(columns={
                                "מספר טלפון": "Phone Number", "כתובת": "Address", "הערות": "Notes"
                            })
                            save_df = save_df[["Phone Number", "First Name", "Last Name", "Address", "Notes"]]
                            st.session_state.customers_df = save_df

                            customers_sheet.clear()
                            customers_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())
                            st.toast("נשמר בהצלחה!", icon="✅"); st.rerun()
        # Excel export
        import io as _io_c
        _xb = _io_c.BytesIO()
        customers_df[["Phone Number", "First Name", "Last Name", "Address", "Notes"]].to_excel(_xb, index=False, engine="openpyxl")
        st.download_button(
            "📥 ייצוא לקוחות ל-Excel",
            data=_xb.getvalue(),
            file_name="customers.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_customers_excel"
        )
    else:
        st.info("עדיין אין לקוחות במערכת. הוסיפי את הלקוחה הראשונה למטה!")

    st.markdown("---")
    st.subheader("➕ הוספת לקוחה חדשה ישירות למאגר")
    with st.form("add_customer_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            full_name_input = st.text_input("שם מלא*")
            phone = st.text_input("מספר טלפון (מזהה ראשי)*")
        with c2:
            address = st.text_input("כתובת למשלוח")
            st.empty()  # placeholder for symmetry

        if st.form_submit_button("שמרי לקוחה במסד הנתונים"):
            if phone and full_name_input:
                name_parts = full_name_input.strip().split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                new_cust = pd.DataFrame([{"Phone Number": phone, "First Name": first_name, "Last Name": last_name, "Address": address, "Notes": ""}])
                st.session_state.customers_df = pd.concat([st.session_state.customers_df, new_cust], ignore_index=True)
                customers_sheet.append_row([phone, first_name, last_name, address, ""])
                st.toast(f"הלקוחה {full_name_input} נוספה בהצלחא!", icon="✅"); st.rerun()
            else:
                st.warning("חובה להזין מספר טלפון ושם.")

    # ==========================================
    #               כרטיס לקוחה אישי
    # ==========================================



def render_customer_card():
    customers_df = st.session_state.customers_df
    customers_sheet = st.session_state.customers_sheet
    orders_df = st.session_state.orders_df
    orders_sheet = st.session_state.orders_sheet

    if st.button("🔙 חזרה לרשימת הלקוחות"):
        st.session_state.current_view = "לקוחות"
        st.session_state.selected_customer_phone = None
        st.rerun()

    if not customers_df.empty:
        customer_data = customers_df[customers_df["Phone Number"] == st.session_state.selected_customer_phone]

        if not customer_data.empty:
            customer = customer_data.iloc[0]
            full_name = f"{customer['First Name']} {customer.get('Last Name', '')}".strip()

            # Customer KPIs from orders
            cust_orders = orders_df[orders_df["Phone Number"] == st.session_state.selected_customer_phone] if not orders_df.empty else pd.DataFrame()
            total_cust_orders = len(cust_orders)
            total_spent = pd.to_numeric(cust_orders["Price"], errors="coerce").fillna(0).sum() if not cust_orders.empty and "Price" in cust_orders.columns else 0
            active_cust = len(cust_orders[cust_orders["Status"] != "✅ נמסרה ללקוחה"]) if not cust_orders.empty and "Status" in cust_orders.columns else 0

            # Hero header
            phone_display = customer['Phone Number']
            address_display = customer.get('Address', '') or 'לא צוינה'
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:16px;padding:24px 28px;color:white;margin-bottom:20px;">
                <div style="font-size:2.2rem;font-weight:800;">✨ {full_name}</div>
                <div style="opacity:0.85;margin-top:6px;font-size:1rem;">📞 {phone_display} &nbsp;&nbsp; 📍 {address_display}</div>
            </div>
            """, unsafe_allow_html=True)

            # KPI strip
            kc1, kc2, kc3 = st.columns(3)
            with kc1:
                st.metric("🛍️ סה\"כ הזמנות", total_cust_orders)
            with kc2:
                st.metric("⚡ הזמנות פעילות", active_cust)
            with kc3:
                st.metric("💰 סכום ששולם", f"₪{total_spent:,.0f}")

            st.markdown("---")

            # Notes
            st.markdown("### 📝 הערות")
            current_notes = customer.get("Notes", "")
            new_notes = st.text_area("הוסיפי או ערכי הערות על הלקוחה:", value=current_notes, height=100)

            if st.button("💾 שמרי הערות", type="primary"):
                with st.spinner("שומר..."):
                    st.session_state.customers_df.loc[st.session_state.customers_df["Phone Number"] == st.session_state.selected_customer_phone, "Notes"] = new_notes
                    save_df = st.session_state.customers_df[["Phone Number", "First Name", "Last Name", "Address", "Notes"]]
                    customers_sheet.clear()
                    customers_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())
                    st.toast("ההערות נשמרו!", icon="✅")

            st.markdown("---")
            st.markdown("### 🛍️ היסטוריית רכישות של הלקוחה")

            if not orders_df.empty:
                customer_orders = orders_df[orders_df["Phone Number"] == st.session_state.selected_customer_phone].copy()

                if not customer_orders.empty:
                    if "Order Date" in customer_orders.columns:
                        customer_orders["Order Date"] = pd.to_datetime(customer_orders["Order Date"], format="%d/%m/%Y", errors="coerce").dt.date
                    if "Delivery Date" in customer_orders.columns:
                        customer_orders["Delivery Date"] = pd.to_datetime(customer_orders["Delivery Date"], format="%d/%m/%Y", errors="coerce").dt.date

                    display_cust_orders = customer_orders.rename(columns={
                        "Order ID": "מספר הזמנה", "Order Date": "תאריך הזמנה", "Delivery Date": "תאריך אספקה",
                        "Item": "פריט", "Status": "סטטוס", "Payment Status": "סטטוס תשלום",
                        "Top Size": "עליון", "Bottom Size": "תחתון", "Custom Size": "התאמות", "Fabric Usage": "צריכת בד (מ')"
                    })

                    # צמצום והגדרת עמודות כדי למנוע גלילה הצידה
                    cols = ["מחיר", "סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "תאריך הזמנה", "פריט"]
                    cols = [c for c in cols if c in display_cust_orders.columns]
                    # Migrate old values → bare emoji only
                    if "סטטוס תשלום" in display_cust_orders.columns:
                        display_cust_orders["סטטוס תשלום"] = (
                            display_cust_orders["סטטוס תשלום"].astype(str)
                            .str.replace("🟡", "🧡", regex=False)
                            .str.replace("🟢", "💚", regex=False)
                            .str.split(" ").str[0]  # שמור רק את האמוג'י
                        )
                    if "סטטוס" in display_cust_orders.columns:
                        display_cust_orders["סטטוס"] = display_cust_orders["סטטוס"].astype(str) \
                            .str.replace("ממתינה לייצור", "ממתינה להכנה", regex=False)

                    config = {
                        "מספר הזמנה": st.column_config.TextColumn("מ\"ה", disabled=True, width="small"),
                        "פריט": st.column_config.TextColumn("פריט"),
                        "תאריך הזמנה": st.column_config.DateColumn("הזמנה", format="DD/MM/YYYY", width="small"),
                        "תאריך אספקה": st.column_config.DateColumn("מסירה", format="DD/MM/YYYY", width="small"),
                        "התאמות": st.column_config.TextColumn("התאמות", width="small"),
                        "סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה להכנה)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"], width="medium"),
                        "סטטוס תשלום": st.column_config.SelectboxColumn("תשלום", options=["🔴", "🧡", "💚"], width="small"),
                        "מחיר": st.column_config.NumberColumn("מחיר", format="₪%d", width="small"),
                        "עליון": st.column_config.TextColumn("עליון", width="small"),
                        "תחתון": st.column_config.TextColumn("תחתון", width="small")
                    }

                    active_mask_cust = display_cust_orders["סטטוס"] != "✅ נמסרה ללקוחה"
                    active_cust_orders = display_cust_orders[active_mask_cust].copy()
                    completed_cust_orders = display_cust_orders[~active_mask_cust].copy()

                    st.markdown("#### 📋 הזמנות פעילות")
                    if not active_cust_orders.empty:
                        edited_active_cust = st.data_editor(active_cust_orders, key="active_cust_editor", use_container_width=True, hide_index=True, column_config=config)
                    else:
                        st.info("אין ללקוחה זו הזמנות פעילות כרגע.")

                    st.markdown("#### ✅ הזמנות שהושלמו")
                    if not completed_cust_orders.empty:
                        edited_completed_cust = st.data_editor(completed_cust_orders, key="completed_cust_editor", use_container_width=True, hide_index=True, column_config=config)
                    else:
                        st.info("אין ללקוחה זו הזמנות שהושלמו בעבר.")

                    has_changes_cust = not edited_active_cust.equals(active_cust_orders) or not edited_completed_cust.equals(completed_cust_orders)
                    if has_changes_cust:
                        if st.button("💾 שמרי שינויים בהזמנות הלקוחה", type="primary", use_container_width=True):
                            with st.spinner("מעדכן מסד נתונים..."):
                                save_orders = pd.concat([edited_active_cust, edited_completed_cust])
                                save_orders["תאריך הזמנה"] = save_orders["תאריך הזמנה"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
                                save_orders["תאריך אספקה"] = save_orders["תאריך אספקה"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")

                                save_orders = save_orders.rename(columns={
                                    "מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage"
                                })

                                orders_indexed = orders_df.set_index("Order ID")
                                save_indexed = save_orders.set_index("Order ID")
                                orders_indexed.update(save_indexed)
                                orders_indexed.reset_index(inplace=True)

                                for col in ["Payment Date", "Swimsuit Type", "Pattern", "Order Notes", "Fabric 2", "Fabric Usage 2"]:
                                    if col not in orders_indexed.columns:
                                        orders_indexed[col] = ""
                                final_save = orders_indexed[[
                                    "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                                    "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                                    "Swimsuit Type", "Pattern", "Order Notes",
                                    "Status", "Payment Status", "Supply Type", "Price", "Payment Date"
                                ]]

                                st.session_state.orders_df = final_save
                                orders_sheet.clear()
                                orders_sheet.update([final_save.columns.values.tolist()] + final_save.values.tolist())
                                st.toast("ההזמנות עודכנו בהצלחה!", icon="✅"); st.rerun()
                else:
                    st.info("ללקוחה זו עדיין אין היסטוריית הזמנות במערכת.")
            else:
                st.info("לא קיימות הזמנות במערכת הכללית.")


