import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_next_order_id, save_finance_data


def render_orders():
    orders_df = st.session_state.orders_df
    orders_sheet = st.session_state.orders_sheet
    inventory_df = st.session_state.inventory_df
    inventory_sheet = st.session_state.inventory_sheet
    customers_df = st.session_state.customers_df
    customers_sheet = st.session_state.customers_sheet
    patterns_df = st.session_state.patterns_df

    st.title("📦 ניהול הזמנות")

    if orders_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Orders' ב-Google Sheets. אנא צרי אותו כדי להתחיל לשמור הזמנות.")
    else:
        st.markdown("---")

        st.subheader("➕ יצירת הזמנה חדשה")

        customer_options = ["✨ לקוחה חדשה..."]
        if not customers_df.empty:
            def _build_customer_label(r):
                # Support both "First Name"/"Last Name" columns and a merged "Name" column
                if "First Name" in r.index:
                    name = f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip()
                elif "Name" in r.index:
                    name = str(r.get("Name", "")).strip()
                else:
                    name = str(r.get("Customer Name", r.get("שם", "לא ידוע"))).strip()
                phone = str(r.get("Phone Number", "")).strip()
                return f"{name} ({phone})" if name else f"({phone})"
            customer_options += [_build_customer_label(r) for _, r in customers_df.iterrows()]

        selected_customer = st.selectbox("עבור איזו לקוחה ההזמנה?", customer_options)

        new_c_fname, new_c_lname, new_c_phone, new_c_address = "", "", "", ""
        if selected_customer == "✨ לקוחה חדשה...":
            st.info("📝 מלאי את פרטי הלקוחה החדשה. היא תתווסף אוטומטית למאגר הלקוחות שלך!")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                new_c_fname = st.text_input("שם פרטי (לקוחה חדשה)*")
                new_c_phone = st.text_input("מספר טלפון (לקוחה חדשה)*")
            with col_c2:
                new_c_lname = st.text_input("שם משפחה (לקוחה חדשה)")
                new_c_address = st.text_input("כתובת למשלוח (לקוחה חדשה)")

        with st.container():
            st.markdown("**פירוט ההזמנה והמלאי:**")
            swimsuit_type = st.radio("סוג בגד הים*", ["בגד ים שלם", "ביקיני"], horizontal=True)
            item_name = st.text_input("שם/תיאור הזמנה (אופציונלי)")

            st.markdown(
                '<div style="background:linear-gradient(135deg,#f8f9ff,#eef0ff);border-right:4px solid #6366f1;'
                'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">'
                '<span style="font-weight:700;color:#4338ca;font-size:15px;">📐 גזרה ומידות</span></div>',
                unsafe_allow_html=True)
            # --- שדות מידה/גזרה דינמיים לפי סוג ---
            top_size, bottom_size, custom_size, pattern_name = "", "", "", ""
            if swimsuit_type == "בגד ים שלם":
                custom_size = st.text_input("מידה / מידות*")
                one_piece_patterns = (
                    patterns_df[patterns_df["Category"].astype(str).str.strip() == "בגד ים שלם"]["Pattern Name"]
                    .astype(str)
                    .str.strip()
                    .tolist()
                    if not patterns_df.empty
                    else []
                )
                pattern_options = one_piece_patterns if one_piece_patterns else ["אין גזרות מתאימות"]
                pattern_name = st.selectbox("גזרה*", pattern_options)
            else:
                bikini_patterns = (
                    patterns_df[patterns_df["Category"].astype(str).str.strip() == "ביקיני"]["Pattern Name"]
                    .astype(str)
                    .str.strip()
                    .tolist()
                    if not patterns_df.empty
                    else []
                )
                bikini_pattern_options = bikini_patterns if bikini_patterns else ["אין גזרות מתאימות"]
                size_options = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "ללא (לא הוזמן)"]
                # Row 1: Top Cut and Size
                row_t1, row_t2 = st.columns([1, 1])
                with row_t1:
                    top_cut = st.selectbox("גזרת עליון", bikini_pattern_options, key="top_cut_bih")
                with row_t2:
                    top_size = st.selectbox("מידת עליון*", size_options, index=2)
                
                # Row 2: Bottom Cut and Size
                row_b1, row_b2 = st.columns([1, 1])
                with row_b1:
                    bottom_cut = st.selectbox("גזרת תחתון", bikini_pattern_options, key="bottom_cut_bih")
                with row_b2:
                    bottom_size = st.selectbox("מידת תחתון*", size_options, index=2)

                # pattern_name for bikini will be saved as "ביקיני" for consistency
                pattern_name = "ביקיני"

            # --- בחירת בדים חזותית ---
            fabric_options = inventory_df["Fabric Name"].astype(str).tolist() if not inventory_df.empty else []
            image_by_fabric = {}
            sku_by_fabric = {}
            if not inventory_df.empty:
                for _, row in inventory_df.iterrows():
                    name = str(row.get("Fabric Name", "")).strip()
                    if name:
                        image_by_fabric[name] = str(row.get("Image URL", "") or "")
                        sku_by_fabric[name] = str(row.get("Fabric ID", "") or "")

            if "order_fabric_primary" not in st.session_state:
                st.session_state.order_fabric_primary = fabric_options[0] if fabric_options else ""
            if "order_fabric_secondary" not in st.session_state:
                st.session_state.order_fabric_secondary = ""
            if "open_fabric_dialog_for" not in st.session_state:
                st.session_state.open_fabric_dialog_for = ""

            @st.dialog("בחירת בד להזמנה")
            def pick_fabric_dialog(target_key: str, exclude_fabric: str = ""):
                available = [f for f in fabric_options if f != exclude_fabric]
                if not available:
                    st.info("אין בדים זמינים לבחירה.")
                    return

                st.caption("בחרי בד מתוך התמונות למטה:")
                cards_per_row = 4
                for start in range(0, len(available), cards_per_row):
                    row_items = available[start:start + cards_per_row]
                    row_cols = st.columns(cards_per_row)
                    for idx, fabric_name in enumerate(row_items):
                        with row_cols[idx]:
                            st.markdown(f"**{fabric_name}**")
                            fabric_img = image_by_fabric.get(fabric_name, "")
                            if fabric_img:
                                st.image(fabric_img, width=140)
                            else:
                                st.info("אין תמונה")
                            st.caption(f"מק\"ט: {sku_by_fabric.get(fabric_name, '-')}")
                            if st.button("בחרי", key=f"pick_{target_key}_{start}_{idx}_{fabric_name}"):
                                if target_key == "primary":
                                    st.session_state.order_fabric_primary = fabric_name
                                    if st.session_state.order_fabric_secondary == fabric_name:
                                        st.session_state.order_fabric_secondary = ""
                                else:
                                    st.session_state.order_fabric_secondary = fabric_name
                                st.session_state.open_fabric_dialog_for = ""
                                st.rerun()

            st.markdown(
                '<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-right:4px solid #22c55e;'
                'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">'
                '<span style="font-weight:700;color:#15803d;font-size:15px;">🧵 בחירת בדים</span></div>',
                unsafe_allow_html=True)
            st.markdown("### 🧵 בחירת בד ראשי")
            if fabric_options:
                if st.session_state.order_fabric_primary not in fabric_options:
                    st.session_state.order_fabric_primary = fabric_options[0]
                sel_fabric = st.session_state.order_fabric_primary
                if st.button("בחרי בד ראשי מהגלריה", key="open_primary_fabric_dialog"):
                    st.session_state.open_fabric_dialog_for = "primary"
                    st.rerun()
                if st.session_state.open_fabric_dialog_for == "primary":
                    pick_fabric_dialog("primary")
                selected_img = image_by_fabric.get(sel_fabric, "")
                if selected_img:
                    c_img, c_meta = st.columns([1, 2])
                    with c_img:
                        st.image(selected_img, width=180)
                    with c_meta:
                        st.markdown(f"**{sel_fabric}**")
                        st.caption(f"מק\"ט: {sku_by_fabric.get(sel_fabric, '-')}")
                fabric_usage = st.number_input("כמות בד נדרשת לבד הראשי (מ')*", min_value=0.0, step=0.1)
            else:
                sel_fabric = ""
                fabric_usage = 0.0
                st.info("אין בדים במלאי כרגע.")

            add_second_fabric = st.checkbox("הוסיפי בד נוסף להזמנה")
            sel_fabric_2 = ""
            fabric_usage_2 = 0.0
            if add_second_fabric:
                st.markdown("### 🧵 בחירת בד נוסף")
                secondary_options = [f for f in fabric_options if f != sel_fabric] if sel_fabric else fabric_options
                if secondary_options:
                    if st.session_state.order_fabric_secondary not in secondary_options:
                        st.session_state.order_fabric_secondary = secondary_options[0]
                    sel_fabric_2 = st.session_state.order_fabric_secondary
                    if st.button("בחרי בד נוסף מהגלריה", key="open_secondary_fabric_dialog"):
                        st.session_state.open_fabric_dialog_for = "secondary"
                        st.rerun()
                    if st.session_state.open_fabric_dialog_for == "secondary":
                        pick_fabric_dialog("secondary", exclude_fabric=sel_fabric)
                    selected_img_2 = image_by_fabric.get(sel_fabric_2, "")
                    if selected_img_2:
                        c2_img, c2_meta = st.columns([1, 2])
                        with c2_img:
                            st.image(selected_img_2, width=180)
                        with c2_meta:
                            st.markdown(f"**{sel_fabric_2}**")
                            st.caption(f"מק\"ט: {sku_by_fabric.get(sel_fabric_2, '-')}")
                    fabric_usage_2 = st.number_input("כמות בד נדרשת לבד הנוסף (מ')*", min_value=0.0, step=0.1)
                else:
                    st.warning("לא נשארו בדים נוספים לבחירה.")

            st.markdown(
                '<div style="background:linear-gradient(135deg,#fffbeb,#fef9c3);border-right:4px solid #f59e0b;'
                'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">'
                '<span style="font-weight:700;color:#b45309;font-size:15px;">📅 תאריכים והערות</span></div>',
                unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1: form_order_date = st.date_input("תאריך הזמנה", value=datetime.today())
            with col_d2: form_delivery_date = st.date_input("תאריך מסירה מיועד", value=None)

            order_notes = ""
            if swimsuit_type == "ביקיני":
                order_notes = st.text_area("הערות להזמנה")

            st.markdown(
                '<div style="background:linear-gradient(135deg,#fff0f3,#ffe4e6);border-right:4px solid #f43f5e;'
                'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">'
                '<span style="font-weight:700;color:#be123c;font-size:15px;">💳 סטטוס ותשלום</span></div>',
                unsafe_allow_html=True)
            st.markdown("**סטטוס ותשלום:**")
            col_st1, col_st2, col_st3, col_st4 = st.columns([1.5, 1, 1, 1.5])
            with col_st1: status = st.selectbox("סטטוס הזמנה", ["🆕 התקבלה (ממתינה להכנה)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"])
            with col_st2: pay_status = st.selectbox("סטטוס תשלום", ["🔴", "🧡", "💚"])
            with col_st3: supply = st.selectbox("סוג אספקה", ["איסוף עצמי", "משלוח"])
            
            form_payment_date_val = ""
            with col_st4:
                if pay_status == "💚":
                    p_date = st.date_input("תאריך תשלום", value=datetime.today())
                    form_payment_date_val = p_date.strftime("%d/%m/%Y")
                else:
                    st.empty()

            price = st.number_input("מחיר סופי סך הכל (₪)", min_value=0, value=0, step=10)

            st.markdown("---")
            bypass_inventory = st.checkbox("התעלמי מהמלאי (שמירת הזמנה ללא חסימה גם אם הבד חסר)")

            if st.button("💾 שמרי הזמנה במערכת", type="primary", key="save_new_order_btn"):
                if swimsuit_type == "בגד ים שלם":
                    if not custom_size:
                        st.warning("חובה להזין מידה / מידות לבגד ים שלם."); st.stop()
                    if pattern_name == "אין גזרות מתאימות":
                        st.error("אין כרגע גזרות מסוג בגד ים שלם. הוסיפי גזרה בלשונית גזרות."); st.stop()
                    final_item = item_name.strip() if str(item_name).strip() else "One-piece"
                else:
                    if bikini_pattern_options == ["אין גזרות מתאימות"]:
                        st.error("אין כרגע גזרות מסוג ביקיני. הוסיפי גזרה בלשונית גזרות."); st.stop()
                    top_not_ordered = top_size == "ללא (לא הוזמן)"
                    bottom_not_ordered = bottom_size == "ללא (לא הוזמן)"
                    if top_not_ordered and bottom_not_ordered:
                        st.error("יש לבחור לפחות חלק אחד בביקיני (עליון, תחתון או שניהם)."); st.stop()
                    if top_not_ordered:
                        bikini_desc = "Bikini - Bottom Only"
                    elif bottom_not_ordered:
                        bikini_desc = "Bikini - Top Only"
                    else:
                        bikini_desc = "Bikini - Full Set"
                    final_item = bikini_desc if not str(item_name).strip() else f"{bikini_desc} | {str(item_name).strip()}"

                if not fabric_options:
                    st.error("אין בדים זמינים במלאי לבחירה."); st.stop()
                if not sel_fabric:
                    st.error("חובה לבחור בד ראשי."); st.stop()
                if fabric_usage <= 0:
                    st.error("חובה להזין כמות בד גדולה מ-0 לבד הראשי."); st.stop()
                if add_second_fabric and (not sel_fabric_2 or fabric_usage_2 <= 0):
                    st.error("כשמוסיפים בד נוסף יש לבחור בד ולהזין כמות גדולה מ-0."); st.stop()

                usage_map = {sel_fabric: float(fabric_usage)}
                if add_second_fabric and sel_fabric_2:
                    usage_map[sel_fabric_2] = usage_map.get(sel_fabric_2, 0.0) + float(fabric_usage_2)

                if not bypass_inventory:
                    inv_current = st.session_state.inventory_df.copy()
                    inv_current["Initial Meters"] = pd.to_numeric(inv_current["Initial Meters"], errors="coerce").fillna(0.0)
                    inv_current["Reserved Meters"] = pd.to_numeric(inv_current.get("Reserved Meters", 0.0), errors="coerce").fillna(0.0)
                    for fab_name, req_m in usage_map.items():
                        row = inv_current[inv_current["Fabric Name"] == fab_name]
                        if row.empty:
                            st.error(f"הבד '{fab_name}' לא נמצא במלאי."); st.stop()
                        
                        initial = float(row.iloc[0]["Initial Meters"])
                        reserved = float(row.iloc[0]["Reserved Meters"])
                        true_available = initial - reserved
                        
                        if req_m > true_available:
                            st.error(f"❌ הבד '{fab_name}' חסר במלאי! כמות זמינה: {true_available:.2f} מ', נדרש: {req_m:.2f} מ'."); st.stop()

                if selected_customer == "✨ לקוחה חדשה...":
                    if not new_c_fname or not new_c_phone:
                        st.warning("חובה להזין שם וטלפון ללקוחה החדשה!"); st.stop()
                    customer_phone = new_c_phone
                    customer_name = f"{new_c_fname} {new_c_lname}".strip()

                    new_cust_row = pd.DataFrame([{"Phone Number": new_c_phone, "First Name": new_c_fname, "Last Name": new_c_lname, "Address": new_c_address, "Notes": "נוצרה דרך מסך הזמנות"}])
                    st.session_state.customers_df = pd.concat([st.session_state.customers_df, new_cust_row], ignore_index=True)
                    if customers_sheet: customers_sheet.append_row([new_c_phone, new_c_fname, new_c_lname, new_c_address, "נוצרה דרך מסך הזמנות"])
                else:
                    customer_phone = selected_customer.split("(")[-1].replace(")", "")
                    customer_name = selected_customer.split("(")[0].strip()

                def get_next_order_id(df):
                    if df.empty: return "0001"
                    valid_ids = pd.to_numeric(df["Order ID"], errors='coerce')
                    max_id = valid_ids.max()
                    if pd.isna(max_id): return "0001"
                    return f"{int(max_id) + 1:04d}"
                order_id = get_next_order_id(st.session_state.orders_df)
                order_date_str = form_order_date.strftime("%d/%m/%Y") if form_order_date else ""
                delivery_date_str = form_delivery_date.strftime("%d/%m/%Y") if form_delivery_date else ""
                pay_status_emoji = pay_status.split(" ")[0]

                order_row_dict = {
                    "Order ID": order_id, "Order Date": order_date_str, "Delivery Date": delivery_date_str, 
                    "Phone Number": customer_phone, "Customer Name": customer_name, "Item": final_item, 
                    "Top Size": top_size, "Bottom Size": bottom_size, 
                    "Custom Size": order_notes if swimsuit_type == "ביקיני" else custom_size, 
                    "Top Cut": top_cut if swimsuit_type == "ביקיני" else "",
                    "Bottom Cut": bottom_cut if swimsuit_type == "ביקיני" else "",
                    "Fabric": sel_fabric, "Fabric Usage": float(fabric_usage),
                    "Fabric 2": sel_fabric_2 if add_second_fabric else "",
                    "Fabric Usage 2": float(fabric_usage_2) if add_second_fabric else 0.0,
                    "Swimsuit Type": swimsuit_type,
                    "Pattern": pattern_name,
                    "Order Notes": order_notes,
                    "Status": status, "Payment Status": pay_status_emoji, 
                    "Supply Type": supply, "Price": price, "Payment Date": form_payment_date_val,
                    "Bypass Inventory": bypass_inventory
                }

                new_order_df = pd.DataFrame([order_row_dict])
                st.session_state.orders_df = pd.concat([st.session_state.orders_df, new_order_df], ignore_index=True)

                # --- עדכון מלאי (לפי הכללים החדשים) ---
                if not bypass_inventory:
                    inv = st.session_state.inventory_df
                    # המרה למספרים ליתר ביטחון
                    inv["Initial Meters"] = pd.to_numeric(inv["Initial Meters"], errors="coerce").fillna(0.0)
                    inv["Reserved Meters"] = pd.to_numeric(inv.get("Reserved Meters", 0.0), errors="coerce").fillna(0.0)
                    
                    # זיהוי סטטוס ממתין (הרשמה) מול סטטוס גזור (הפחתה פיזית)
                    is_pending_new = any(kw in status for kw in ["התקבלה", "ממתינה"])
                    
                    for f_name, usage in [(sel_fabric, fabric_usage), (sel_fabric_2 if add_second_fabric else None, fabric_usage_2)]:
                        if f_name and float(usage) > 0:
                            mask = inv["Fabric Name"] == f_name
                            if mask.any():
                                if is_pending_new:
                                    # Rule: Available drops, Box stays same => Increase Reserved
                                    inv.loc[mask, "Reserved Meters"] += float(usage)
                                else:
                                    # Rule: Box drops, Available stays same => Decrease Initial (Physical)
                                    inv.loc[mask, "Initial Meters"] -= float(usage)
                    
                    st.session_state.inventory_df = inv
                    if inventory_sheet:
                        # שמירה לענן
                        inv_save = inv[["Fabric ID", "Fabric Name", "Initial Meters", "Reserved Meters", "Image URL"]]
                        inventory_sheet.clear()
                        inventory_sheet.update([inv_save.columns.values.tolist()] + inv_save.values.tolist())

                if orders_sheet:
                    if len(st.session_state.orders_df) == 1: 
                        orders_sheet.append_row([
                            "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                            "Top Size", "Bottom Size", "Custom Size", "Top Cut", "Bottom Cut", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                            "Swimsuit Type", "Pattern", "Order Notes", "Status", "Payment Status", "Supply Type", "Price", "Payment Date", "Bypass Inventory"
                        ])
                    orders_sheet.append_row([
                        order_row_dict["Order ID"], order_row_dict["Order Date"], order_row_dict["Delivery Date"],
                        order_row_dict["Phone Number"], order_row_dict["Customer Name"], order_row_dict["Item"],
                        order_row_dict["Top Size"], order_row_dict["Bottom Size"], order_row_dict["Custom Size"],
                        order_row_dict["Top Cut"], order_row_dict["Bottom Cut"],
                        order_row_dict["Fabric"], order_row_dict["Fabric Usage"], order_row_dict["Fabric 2"], order_row_dict["Fabric Usage 2"],
                        order_row_dict["Swimsuit Type"], order_row_dict["Pattern"], order_row_dict["Order Notes"],
                        order_row_dict["Status"], order_row_dict["Payment Status"], order_row_dict["Supply Type"],
                        order_row_dict["Price"], order_row_dict["Payment Date"], order_row_dict["Bypass Inventory"]
                    ])

                if inventory_sheet is not None:
                    inv_save_df = st.session_state.inventory_df[["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]].copy()
                    inv_save_df["Image URL"] = inv_save_df["Image URL"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
                    inventory_sheet.clear()
                    if inv_save_df.empty:
                        inventory_sheet.update([["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]])
                    else:
                        inventory_sheet.update([inv_save_df.columns.values.tolist()] + inv_save_df.values.tolist())



                st.toast(f"הזמנה {order_id} נוצרה ונשמרה בהצלחה!", icon="✅"); st.rerun()
        st.markdown("---")

        if not orders_df.empty:
            display_orders = orders_df.copy()

            # סטטיסטיקות מעל הטבלה
            _total  = len(orders_df)
            _active = len(orders_df[orders_df["Status"] != "✅ נמסרה ללקוחה"])
            _pickup = len(orders_df[orders_df["Status"] == "📦 מוכנה לאיסוף/משלוח"])
            _unpaid = len(orders_df[orders_df["Payment Status"] == "🔴"])
            _done   = _total - _active
            _s1, _s2, _s3, _s4, _s5 = st.columns(5)
            with _s1: st.metric('📦 סה"כ הזמנות', _total)
            with _s2: st.metric("⚡ הזמנות פעילות", _active)
            with _s3: st.metric("🚚 מוכנות לאיסוף", _pickup)
            with _s4: st.metric("🔴 טרם שולמו", _unpaid)
            with _s5: st.metric("✅ הושלמו", _done)
            st.markdown("---")

            st.markdown("### 🔍 חיפוש וסינון הזמנות")
            col_search1, col_search2 = st.columns([2, 1])
            with col_search1:
                search_query = st.text_input("חיפוש חופשי (שם לקוחה, מס' הזמנה, פריט, טלפון):", "")
            with col_search2:
                search_scope = st.radio("היכן לחפש?", ["גם וגם", "הזמנות פעילות", "הזמנות שהושלמו"], horizontal=True)

            if search_query:
                mask = (
                    display_orders["Customer Name"].astype(str).str.contains(search_query, na=False) |
                    display_orders["Order ID"].astype(str).str.contains(search_query, na=False) |
                    display_orders["Item"].astype(str).str.contains(search_query, na=False) |
                    display_orders["Phone Number"].astype(str).str.contains(search_query, na=False)
                )
                display_orders = display_orders[mask]

            if "Order Date" in display_orders.columns:
                display_orders["Order Date"] = pd.to_datetime(display_orders["Order Date"], format="%d/%m/%Y", errors="coerce").dt.date
            if "Delivery Date" in display_orders.columns:
                display_orders["Delivery Date"] = pd.to_datetime(display_orders["Delivery Date"], format="%d/%m/%Y", errors="coerce").dt.date
            if "Payment Date" in display_orders.columns:
                display_orders["Payment Date"] = pd.to_datetime(display_orders["Payment Date"], format="%d/%m/%Y", errors="coerce").dt.date
            if "Price" in display_orders.columns:
                display_orders["Price"] = pd.to_numeric(display_orders["Price"], errors="coerce").fillna(0)

            display_orders = display_orders.rename(columns={
                "Order ID": "מ\"ה", "Order Date": "הזמנה", "Delivery Date": "מסירה",
                "Customer Name": "שם לקוחה", "Item": "פריט", "Status": "סטטוס", "Payment Status": "תשלום",
                "Price": "מחיר", "Top Size": "עליון", "Bottom Size": "תחתון", "Custom Size": "התאמות", 
                "Top Cut": "גזרת עליון", "Bottom Cut": "גזרת תחתון", "Fabric Usage": "צריכת בד (מ')",
                "Payment Date": "תאריך תשלום"
            })

            # צמצום עמודות כדי למנוע גלילה אופקית, הצגת המידע החשוב בלבד בראייה רחבה
            if "מ\"ה" in display_orders.columns:
                display_orders = display_orders.sort_values(by="מ\"ה", key=lambda x: pd.to_numeric(x, errors="coerce"), ascending=False)
            
            # Left to Right list for RTL display: תשלום represents the leftmost, שם לקוחה the rightmost
            cols = ["תשלום", "מחיר", "סטטוס", "מ\"ה", "התאמות", "תחתון", "עליון", "גזרת תחתון", "גזרת עליון", "מסירה", "הזמנה", "פריט", "שם לקוחה"]
            cols = [c for c in cols if c in display_orders.columns]

            if st.session_state.delete_mode_orders:
                display_orders["בחרי"] = False
                cols = ["בחרי"] + cols

            display_orders = display_orders[cols]

            # Migrate old values → bare emoji only (backward compat)
            if "תשלום" in display_orders.columns:
                display_orders["תשלום"] = (
                    display_orders["תשלום"].astype(str)
                    .str.replace("🟡", "🧡", regex=False)  # old ירוק → כתום
                    .str.replace("🟢", "💚", regex=False)  # old ירוק → לב
                    .str.split(" ").str[0]               # שמור רק את האמוג'י
                )
            if "סטטוס" in display_orders.columns:
                display_orders["סטטוס"] = display_orders["סטטוס"].astype(str) \
                    .str.replace("ממתינה לייצור", "ממתינה להכנה", regex=False)

            config = {
                "בחרי": st.column_config.CheckboxColumn("בחרי", default=False),
                "מ\"ה": st.column_config.TextColumn("מ\"ה", disabled=True, width="small", alignment="right"),
                "שם לקוחה": st.column_config.TextColumn("שם לקוחה", disabled=True, width="medium", alignment="right"),
                "פריט": st.column_config.TextColumn("פריט", alignment="right"),
                "הזמנה": st.column_config.DateColumn("הזמנה", format="DD/MM/YYYY", width="small", alignment="right"),
                "מסירה": st.column_config.DateColumn("מסירה", format="DD/MM/YYYY", width="small", alignment="right"),
                "התאמות": st.column_config.TextColumn("התאמות", width="small", alignment="right"),
                "סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה להכנה)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"], width="medium"),
                "תשלום": st.column_config.SelectboxColumn("תשלום", options=["🔴", "🧡", "💚"], width="small"),
                "מחיר": st.column_config.NumberColumn("מחיר", format="₪%d", width="small", alignment="right"),
                "עליון": st.column_config.TextColumn("עליון", width="small", alignment="right"),
                "תחתון": st.column_config.TextColumn("תחתון", width="small", alignment="right"),
                "גזרת עליון": st.column_config.TextColumn("גזרת עליון", width="small", alignment="right"),
                "גזרת תחתון": st.column_config.TextColumn("גזרת תחתון", width="small", alignment="right")
            }
            if st.session_state.delete_mode_orders:
                config["בחרי"] = st.column_config.CheckboxColumn("בחרי", default=False)

            active_mask = display_orders["סטטוס"] != "✅ נמסרה ללקוחה"
            active_orders = display_orders[active_mask].copy()
            completed_orders = display_orders[~active_mask].copy()

            edited_active = active_orders
            edited_completed = completed_orders

            if search_scope in ["גם וגם", "הזמנות פעילות"]:
                st.markdown("### 📋 הזמנות פעילות")
                if not active_orders.empty:
                    edited_active = st.data_editor(active_orders, key="active_orders_editor", use_container_width=True, hide_index=True, column_config=config)
                else:
                    st.info("אין הזמנות פעילות שתואמות לחיפוש.")

            if search_scope in ["גם וגם", "הזמנות שהושלמו"]:
                st.markdown("### ✅ הזמנות שהושלמו (נמסרו)")
                if not completed_orders.empty:
                    edited_completed = st.data_editor(completed_orders, key="completed_orders_editor", use_container_width=True, hide_index=True, column_config=config)
                else:
                    st.info("אין הזמנות שהושלמו שתואמות לחיפוש.")

            col_space, col_btn_save, col_btn_select = st.columns([6, 2, 2])

            with col_btn_select:
                if not st.session_state.delete_mode_orders:
                    if st.button("בחרי", key="sel_ord", use_container_width=True):
                        st.session_state.delete_mode_orders = True; st.rerun()
                else:
                    if st.button("בטלי", key="canc_ord", use_container_width=True):
                        st.session_state.delete_mode_orders = False; st.rerun()

            with col_btn_save:
                if st.session_state.delete_mode_orders:
                    orders_to_delete = pd.concat([
                        edited_active[edited_active["בחרי"] == True] if not edited_active.empty else pd.DataFrame(),
                        edited_completed[edited_completed["בחרי"] == True] if not edited_completed.empty else pd.DataFrame()
                    ])
                    if not orders_to_delete.empty:
                        if st.button("מחקי מסומנות 🗑️", type="primary", use_container_width=True):
                            with st.spinner("מעדכן מסד נתונים..."):
                                ids_to_delete = orders_to_delete["מ\"ה"].tolist()
                                # Safety check for missing column in old data
                                if "Bypass Inventory" not in orders_df.columns:
                                    orders_df["Bypass Inventory"] = False
                                
                                st.session_state.orders_df = orders_df.copy() # Refresh with potential new col
                                deleted_full_rows = orders_df[orders_df["Order ID"].isin(ids_to_delete)]
                                
                                # --- החזרת הבד למלאי (לפי הכללים החדשים) ---
                                inv = st.session_state.inventory_df
                                inv["Initial Meters"] = pd.to_numeric(inv["Initial Meters"], errors="coerce").fillna(0.0)
                                inv["Reserved Meters"] = pd.to_numeric(inv.get("Reserved Meters", 0.0), errors="coerce").fillna(0.0)
                                
                                for _, o_row in deleted_full_rows.iterrows():
                                    bypass = str(o_row.get("Bypass Inventory", "")).strip().lower() == "true"
                                    if not bypass:
                                        status_old = str(o_row.get("Status", "")).strip()
                                        is_pending_old = any(kw in status_old for kw in ["התקבלה", "ממתינה"])
                                        
                                        # Primary & Secondary
                                        for f_name, usage in [(o_row.get("Fabric"), o_row.get("Fabric Usage")), (o_row.get("Fabric 2"), o_row.get("Fabric Usage 2"))]:
                                            if f_name and float(usage or 0) > 0:
                                                mask = inv["Fabric Name"] == f_name
                                                if mask.any():
                                                    if is_pending_old:
                                                        inv.loc[mask, "Reserved Meters"] -= float(usage)
                                                    else:
                                                        inv.loc[mask, "Initial Meters"] += float(usage)
                                
                                st.session_state.inventory_df = inv
                                if inventory_sheet:
                                    inv_save = inv[["Fabric ID", "Fabric Name", "Initial Meters", "Reserved Meters", "Image URL"]]
                                    inventory_sheet.clear()
                                    inventory_sheet.update([inv_save.columns.values.tolist()] + inv_save.values.tolist())

                                st.session_state.orders_df = orders_df[~orders_df["Order ID"].isin(ids_to_delete)]
                                orders_sheet.clear()
                                if st.session_state.orders_df.empty:
                                    orders_sheet.update([[
                                        "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                                        "Top Size", "Bottom Size", "Custom Size", "Top Cut", "Bottom Cut", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                                        "Swimsuit Type", "Pattern", "Order Notes",
                                        "Status", "Payment Status", "Supply Type", "Price", "Payment Date", "Bypass Inventory"
                                    ]])
                                else:
                                    # Ensure column order is consistent
                                    cols_to_save = [
                                        "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                                        "Top Size", "Bottom Size", "Custom Size", "Top Cut", "Bottom Cut", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                                        "Swimsuit Type", "Pattern", "Order Notes",
                                        "Status", "Payment Status", "Supply Type", "Price", "Payment Date", "Bypass Inventory"
                                    ]
                                    save_df = st.session_state.orders_df[cols_to_save].copy()
                                    # Sanitize for Google Sheets/JSON: fill NaN and convert to strings/numbers
                                    save_df = save_df.fillna("")
                                    for col in save_df.columns:
                                        if save_df[col].dtype == "object":
                                            save_df[col] = save_df[col].astype(str).replace("nan", "").replace("None", "")
                                    
                                    orders_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())



                                st.session_state.delete_mode_orders = False
                                st.toast("ההזמנות נמחקו!", icon="✅"); st.rerun()
                else:
                    has_changes = not edited_active.equals(active_orders) or not edited_completed.equals(completed_orders)
                    if has_changes:
                        if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                            with st.spinner("מעדכן שינויים..."):
                                save_orders = pd.concat([edited_active, edited_completed])
                                if "הזמנה" in save_orders.columns:
                                    save_orders["הזמנה"] = save_orders["הזמנה"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
                                if "מסירה" in save_orders.columns:
                                    save_orders["מסירה"] = save_orders["מסירה"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
                                if "תאריך תשלום" in save_orders.columns:
                                    save_orders["תאריך תשלום"] = save_orders["תאריך תשלום"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")

                                save_orders = save_orders.rename(columns={
                                    "מ\"ה": "Order ID", "הזמנה": "Order Date", "מסירה": "Delivery Date",
                                    "שם לקוחה": "Customer Name", "פריט": "Item", "סטטוס": "Status", "מחיר": "Price", "תשלום": "Payment Status",
                                    "תאריך תשלום": "Payment Date",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "גזרת עליון": "Top Cut", "גזרת תחתון": "Bottom Cut", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage",
                                    "Bypass Inventory": "Bypass Inventory"
                                })

                                orders_indexed = orders_df.set_index("Order ID")
                                save_indexed = save_orders.set_index("Order ID")


                                today_str = datetime.now().strftime("%d/%m/%Y")
                                for o_id, row in save_indexed.iterrows():
                                    # --- עדכון מלאי על שינוי סטטוס ---
                                    if o_id in orders_indexed.index:
                                        old_row = orders_indexed.loc[o_id]
                                        new_status = str(row["Status"]).strip()
                                        old_status = str(old_row["Status"]).strip()
                                        is_p_new = any(kw in new_status for kw in ["התקבלה", "ממתינה"])
                                        is_p_old = any(kw in old_status for kw in ["התקבלה", "ממתינה"])
                                        
                                        if is_p_new != is_p_old:
                                            bypass = str(old_row.get("Bypass Inventory", "")).strip().lower() == "true"
                                            if not bypass:
                                                inv = st.session_state.inventory_df
                                                inv["Initial Meters"] = pd.to_numeric(inv["Initial Meters"], errors="coerce").fillna(0.0)
                                                inv["Reserved Meters"] = pd.to_numeric(inv.get("Reserved Meters", 0.0), errors="coerce").fillna(0.0)
                                                
                                                for f_col, u_col in [("Fabric", "Fabric Usage"), ("Fabric 2", "Fabric Usage 2")]:
                                                    f_name = str(old_row.get(f_col, "")).strip()
                                                    usage = pd.to_numeric(old_row.get(u_col, 0.0), errors="coerce")
                                                    if f_name and usage > 0:
                                                        mask = inv["Fabric Name"] == f_name
                                                        if mask.any():
                                                            if is_p_old and not is_p_new: # Pending -> Cut
                                                                inv.loc[mask, "Initial Meters"] -= float(usage)
                                                                inv.loc[mask, "Reserved Meters"] -= float(usage)
                                                            elif not is_p_old and is_p_new: # Cut -> Pending
                                                                inv.loc[mask, "Initial Meters"] += float(usage)
                                                                inv.loc[mask, "Reserved Meters"] += float(usage)
                                                
                                                st.session_state.inventory_df = inv
                                                if inventory_sheet:
                                                    inv_save = inv[["Fabric ID", "Fabric Name", "Initial Meters", "Reserved Meters", "Image URL"]]
                                                    inventory_sheet.clear()
                                                    inventory_sheet.update([inv_save.columns.values.tolist()] + inv_save.values.tolist())

                                    if row["Payment Status"] == "💚":
                                        old_status = orders_indexed.loc[o_id, "Payment Status"] if o_id in orders_indexed.index else ""
                                        current_p_date = str(row.get("Payment Date", "")).strip()

                                        # if just became 💚 or is 💚 but empty date, set today
                                        if (old_status != "💚" or current_p_date == "") and current_p_date == "":
                                            save_indexed.at[o_id, "Payment Date"] = today_str
                                    else:
                                        save_indexed.at[o_id, "Payment Date"] = ""

                                    # Sync finance
                                    row_dict = row.to_dict()
                                    row_dict["Order ID"] = o_id


                                orders_indexed.update(save_indexed)
                                orders_indexed.reset_index(inplace=True)

                                for col in ["Payment Date", "Swimsuit Type", "Pattern", "Top Cut", "Bottom Cut", "Order Notes", "Fabric 2", "Fabric Usage 2"]:
                                    if col not in orders_indexed.columns:
                                        orders_indexed[col] = ""
                                final_save = orders_indexed[[
                                    "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                                    "Top Size", "Bottom Size", "Custom Size", "Top Cut", "Bottom Cut", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                                    "Swimsuit Type", "Pattern", "Order Notes",
                                    "Status", "Payment Status", "Supply Type", "Price", "Payment Date"
                                ]]

                                # Sanitize for Google Sheets/JSON
                                final_save_df = final_save.copy().fillna("")
                                for col in final_save_df.columns:
                                    if final_save_df[col].dtype == "object":
                                        final_save_df[col] = final_save_df[col].astype(str).replace("nan", "").replace("None", "")

                                st.session_state.orders_df = final_save
                                orders_sheet.clear()
                                orders_sheet.update([final_save_df.columns.values.tolist()] + final_save_df.values.tolist())
                                


                                st.toast("נשמר בהצלחה!", icon="✅"); st.rerun()

            # Excel export
            import io as _io_ord
            _xls_buf = _io_ord.BytesIO()
            orders_df.to_excel(_xls_buf, index=False, engine="openpyxl")
            st.download_button(
                "📥 ייצוא הזמנות ל-Excel",
                data=_xls_buf.getvalue(),
                file_name="orders.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_orders_excel"
            )

        else:
            st.info("עדיין אין הזמנות במערכת. הוסיפי את ההזמנה הראשונה למטה!")
