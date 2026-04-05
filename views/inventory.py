import streamlit as st
import pandas as pd
from utils import get_calculated_inventory, process_image


def render_inventory():
    inventory_df = st.session_state.inventory_df
    inventory_sheet = st.session_state.inventory_sheet

    st.title("🧵 ניהול בדים ומלאי")

    if inventory_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Inventory' ב-Google Sheets. צרי אותו כדי להתחיל לשמור מלאי.")
    else:
        inv_display = get_calculated_inventory()

        # --- תצוגת מדדים (Metrics) בראש הדף ---
        if not inv_display.empty:
            total_fabrics = len(inv_display)
            total_box = pd.to_numeric(inv_display["כמות בארגז (מ')"], errors='coerce').fillna(0).sum()
            total_available = pd.to_numeric(inv_display["כמות זמינה (מ')"], errors='coerce').fillna(0).sum()

            # עיצוב מותאם למדדים
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("סוגי בדים במלאי", f"{total_fabrics}")
            with m2:
                st.metric("סה״כ מטרים בארגז", f"{total_box:g}")
            with m3:
                st.metric("סה״כ מטרים פנויים", f"{total_available:g}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- חלוקה ללשוניות ---
        tab_list, tab_add = st.tabs(["📋 רשימת מלאי קיימת", "➕ הוספת בד חדש"])

        with tab_list:
            if not inv_display.empty:
                # --- סרגל חיפוש ---
                col_search, col_space = st.columns([1, 1])
                with col_search:
                    search_term = st.text_input("🔍 חיפוש קל (לפי שם או מק\"ט):", placeholder="הקלידי כאן...")

                # מוסיפים אינדקס מקורי כדי שנוכל לחבר עריכות ומחיקות בחזרה למסד הנתונים
                inv_display["_Original_Index"] = inv_display.index

                # סינון לפי חיפוש
                if search_term:
                    mask = (
                        inv_display["Fabric Name"].astype(str).str.contains(search_term, case=False, na=False) |
                        inv_display["Fabric ID"].astype(str).str.contains(search_term, case=False, na=False)
                    )
                    filtered_inv = inv_display[mask]
                else:
                    filtered_inv = inv_display

                if filtered_inv.empty:
                    st.info("לא נמצאו בדים התואמים לחיפוש שלך.")
                else:
                    # שינוי שמות עמודות בהתאם לבקשת המשתמש
                    df_view = filtered_inv.rename(columns={
                        "Fabric Name": "שם הבד/צבע",
                        "Fabric ID": "מק\"ט",
                        "Image URL": "תמונה"
                    })

                    # סדר העמודות מתהפך כדי שבטבלה עצמה זה יופיע מימין לשמאל:
                    # הוספנו את "תמונה" משמאל ביותר שזה אומר שהיא הראשונה ברשימה (מימין במסך).
                    cols = ["תמונה", "כמות זמינה (מ')", "כמות בארגז (מ')", "מק\"ט", "שם הבד/צבע", "_Original_Index", "_Delivered_Usage"]

                    if st.session_state.delete_mode_inventory:
                        df_view["בחרי למחיקה"] = False
                        cols = ["בחרי למחיקה"] + cols

                    df_view = df_view[cols]

                    # קונפיגורציית עמודות
                    config = {
                        "שם הבד/צבע": st.column_config.TextColumn("שם הבד/צבע"),
                        "מק\"ט": st.column_config.TextColumn("מק\"ט", width="small"),
                        "כמות בארגז (מ')": st.column_config.NumberColumn("בארגז (מ')", format="%g", width="small"),
                        "כמות זמינה (מ')": st.column_config.NumberColumn("זמין (מ')", format="%g", width="small"),
                        "תמונה": st.column_config.ImageColumn("תמונה", width="small"),
                        "_Original_Index": None,
                        "_Delivered_Usage": None,
                    }
                    if st.session_state.delete_mode_inventory:
                        config["בחרי למחיקה"] = st.column_config.CheckboxColumn("למחיקה", default=False)

                    st.caption("💡 טיפ: ניתן ללחוץ על הטקסטים במסך ולערוך את נתוני המלאי או המק\"ט תוך כדי תנועה!")

                    # שימוש באפשרות ההרחבה לגובה שורות כדי לוודא תמונה גדולה (לפחות 100px)
                    edited_inv = st.data_editor(
                        df_view, 
                        use_container_width=True, 
                        hide_index=True, 
                        column_config=config,
                        **({"row_height": 120} if int(st.__version__.split(".")[1]) >= 43 or (int(st.__version__.split(".")[0]) >= 2) else {}),
                        key=f"inv_editor_{search_term}"
                    )

                    # --- פעולות עריכה ומחיקה מרוכזות ---
                    col_space_action, col_btn_save, col_btn_select = st.columns([6, 2, 2])

                    with col_btn_select:
                        if not st.session_state.delete_mode_inventory:
                            if st.button("מחיקת פריטים", key="sel_inv", use_container_width=True):
                                st.session_state.delete_mode_inventory = True; st.rerun()
                        else:
                            if st.button("בטלי מחיקה", key="canc_inv", use_container_width=True):
                                st.session_state.delete_mode_inventory = False; st.rerun()

                    with col_btn_save:
                        if st.session_state.delete_mode_inventory:
                            inv_to_delete = edited_inv[edited_inv["בחרי למחיקה"] == True]
                            if not inv_to_delete.empty:
                                if st.button("אישור מחיקה 🗑️", type="primary", use_container_width=True):
                                    with st.spinner("מוחקת מהמלאי (מסתנכרן עם הענן)..."):
                                        ids_to_delete = inv_to_delete["מק\"ט"].tolist()
                                        st.session_state.inventory_df = inventory_df[~inventory_df["Fabric ID"].isin(ids_to_delete)]

                                        inventory_sheet.clear()
                                        if st.session_state.inventory_df.empty:
                                            inventory_sheet.update([["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]])
                                        else:
                                            inventory_sheet.update([st.session_state.inventory_df.columns.values.tolist()] + st.session_state.inventory_df.values.tolist())

                                        st.session_state.delete_mode_inventory = False
                                        st.toast("הבדים שנבחרו נמחקו בהצלחה!", icon="✅"); st.rerun()
                        else:
                            if not edited_inv.equals(df_view):
                                if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                                    if edited_inv["מק\"ט"].duplicated().any():
                                        st.error("❌ שגיאה: יש כפילות במק\"ט! בדקי שוב.")
                                    elif edited_inv["שם הבד/צבע"].duplicated().any():
                                        st.error("❌ שגיאה: יש כפילות בשם הבד! אנא השתמשי בשמות ייחודיים.")
                                    else:
                                        with st.spinner("שומרת את המלאי המעודכן בענן..."):
                                            # חילוץ נתוני העריכה ומיזוגם בחזרה לטבלת המלאי בהתאם לאינדקס המקורי
                                            for idx, row in edited_inv.iterrows():
                                                orig_idx = int(row["_Original_Index"])
                                                st.session_state.inventory_df.at[orig_idx, "Fabric ID"] = str(row["מק\"ט"]).strip()
                                                st.session_state.inventory_df.at[orig_idx, "Fabric Name"] = str(row["שם הבד/צבע"]).strip()
                                                
                                                # Use raw numeric values for calculations
                                                old_row = df_view.loc[idx]
                                                new_box = float(row["כמות בארגז (מ')"])
                                                new_avail = float(row["כמות זמינה (מ')"])
                                                old_box = float(old_row["כמות בארגז (מ')"])
                                                old_avail = float(old_row["כמות זמינה (מ')"])
                                                
                                                # Current internal state
                                                curr_initial = float(st.session_state.inventory_df.at[orig_idx, "Initial Meters"])
                                                curr_reserved = float(st.session_state.inventory_df.at[orig_idx, "Reserved Meters"])
                                                
                                                # Rule 1: Box Update (Delta Preservation)
                                                # Rule 2: Available Update (Independence)
                                                if new_box != old_box:
                                                    # Box was edited. Apply delta to Initial Meters.
                                                    # Delta preservation is automatic: Available = (Initial + delta) - Reserved
                                                    delta = new_box - old_box
                                                    st.session_state.inventory_df.at[orig_idx, "Initial Meters"] = curr_initial + delta
                                                elif new_avail != old_avail:
                                                    # Available was edited. Update Reserved Meters only.
                                                    # New Avail = Initial - New Reserved  =>  New Reserved = Initial - New Avail
                                                    new_reserved = curr_initial - new_avail
                                                    st.session_state.inventory_df.at[orig_idx, "Reserved Meters"] = new_reserved
                                                
                                                # Rule 3: Hard Cap (Available <= Box / Reserved >= 0)
                                                final_initial = float(st.session_state.inventory_df.at[orig_idx, "Initial Meters"])
                                                final_reserved = float(st.session_state.inventory_df.at[orig_idx, "Reserved Meters"])
                                                if final_reserved < 0:
                                                    st.session_state.inventory_df.at[orig_idx, "Reserved Meters"] = 0.0

                                            save_df = st.session_state.inventory_df[["Fabric ID", "Fabric Name", "Initial Meters", "Reserved Meters", "Image URL"]]
                                            save_df["Image URL"] = save_df["Image URL"].apply(lambda x: "" if pd.isna(x) else str(x).strip())

                                            inventory_sheet.clear()
                                            inventory_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())
                                            st.toast("המלאי עודכן בהצלחה!", icon="✅"); st.rerun()
            else:
                st.info("עדיין אין בדים במערכת. עברי ללשונית 'הוספת בד חדש' כדי להתחיל!")

        # Excel export (above "add fabric" tab)
    import io as _io_inv
    _iv = _io_inv.BytesIO()
    inventory_df[["Fabric ID", "Fabric Name", "Initial Meters"]].to_excel(_iv, index=False, engine="openpyxl")
    st.download_button(
        "📥 ייצוא מלאי ל-Excel",
        data=_iv.getvalue(),
        file_name="inventory.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_inventory_excel"
    )

    with tab_add:
            st.markdown("### הוספת בד חדש לאוסף")
            st.caption("הוסיפי בד חדש עם הפרטים שלו וצילום. הוא יתווסף אוטומטית למאגר הבדים באפליקציה.")

            # החלפנו את st.form בניהול session_state כדי לפתור באגים במנגנון העלאת התמונות של Streamlit
            if "fabric_form_key" not in st.session_state:
                st.session_state.fabric_form_key = 0

            f_key = st.session_state.fabric_form_key

            with st.container():
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    f_name = st.text_input("שם הבד / תיאור צבע*", key=f"fname_{f_key}")
                    f_meters = st.number_input("כמות התחלתית (מטרים)*", min_value=0.0, step=0.5, key=f"fmeters_{f_key}")
                with col_f2:
                    f_id = st.text_input("מק\"ט*", key=f"fid_{f_key}")

                st.markdown("**תמונת הבד (אופציונלי אך מומלץ):**")
                img_method = st.radio(
                    "איך תרצי להוסיף תמונה?",
                    ["העלאת קובץ מהמחשב/טלפון", "הפעלת מצלמה (צילום כעת)"],
                    horizontal=True,
                    key=f"method_{f_key}"
                )

                if "העלאת קובץ" in img_method:
                    uploaded_file = st.file_uploader("בחרי תמונה מהמכשיר", type=["jpg", "jpeg", "png"], key=f"img_up_{f_key}")
                else:
                    uploaded_file = st.camera_input("הפעילי מצלמה וצלמי את הבד", key=f"img_cam_{f_key}")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✨ שמרי בד חדש באוסף", type="primary", use_container_width=True):
                    if not f_name or not f_id:
                        st.warning("חובה להזין את שם הבד ומק\"ט!")
                    elif f_id in st.session_state.inventory_df["Fabric ID"].values:
                        st.error("❌ שגיאה: המק\"ט כבר קיים במערכת! אנא בחרי מק\"ט ייחודי.")
                    elif f_name in st.session_state.inventory_df["Fabric Name"].values:
                        st.error("❌ שגיאה: שם הבד כבר קיים במערכת! אנא בחרי שם ייחודי.")
                    else:
                        with st.spinner("שומר בד באוסף..."):
                            # מעבדים את התמונה תמיד ברגע השמירה כדי למנוע את באג האיפוס
                            f_img_clean = process_image(uploaded_file) if uploaded_file else ""

                            new_fabric = {
                                "Fabric ID": str(f_id).strip(),
                                "Fabric Name": str(f_name).strip(),
                                "Initial Meters": f_meters,
                                "Image URL": f_img_clean.strip(),
                            }
                            st.session_state.inventory_df = pd.concat(
                                [st.session_state.inventory_df, pd.DataFrame([new_fabric])], ignore_index=True
                            )
                            if inventory_sheet.get_all_records() == []:
                                inventory_sheet.append_row(["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"])
                            inventory_sheet.append_row(
                                [
                                    new_fabric["Fabric ID"],
                                    new_fabric["Fabric Name"],
                                    new_fabric["Initial Meters"],
                                    new_fabric["Image URL"],
                                ]
                            )
                            # מאתחלים את הטופס באמצעות העלאת המפתח
                            st.session_state.fabric_form_key += 1
                            st.toast(f"הבד '{f_name}' התווסף למאגר בהצלחה!", icon="✅"); st.rerun()


