import streamlit as st
import pandas as pd
from utils import get_calculated_inventory, process_image, save_inventory_to_sheet


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

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("סוגי בדים במלאי", f"{total_fabrics}")
            with m2:
                st.metric("סה״כ מטרים בארגז", f"{total_box:.2f}")
            with m3:
                st.metric("סה״כ מטרים פנויים", f"{total_available:.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- חלוקה ללשוניות ---
        tab_list, tab_add = st.tabs(["📋 רשימת מלאי קיימת", "➕ הוספת בד חדש"])

        with tab_list:
            if not inv_display.empty:

                # ── dialog: עדכון תמונה ────────────────────────────────────
                @st.dialog("🖼️ עדכון תמונת בד")
                def _update_image_dialog(orig_idx: int, fabric_name: str):
                    st.markdown(f"**עדכון תמונה עבור: {fabric_name}**")
                    img_method = st.radio(
                        "שיטת העלאה:",
                        ["העלאת קובץ מהמחשב/טלפון", "הפעלת מצלמה (צילום כעת)"],
                        horizontal=True,
                        key="upd_img_method"
                    )
                    if "העלאת קובץ" in img_method:
                        new_file = st.file_uploader(
                            "בחרי תמונה", type=["jpg", "jpeg", "png"], key="upd_img_file"
                        )
                    else:
                        new_file = st.camera_input("צלמי את הבד", key="upd_img_cam")

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 שמרי תמונה", type="primary",
                                     use_container_width=True, key="upd_img_save"):
                            if not new_file:
                                st.warning("יש לבחור תמונה לפני השמירה.")
                            else:
                                with st.spinner("מעדכנת תמונה..."):
                                    new_url = process_image(new_file)
                                    st.session_state.inventory_df.at[orig_idx, "Image URL"] = new_url
                                    save_inventory_to_sheet(
                                        inventory_sheet, st.session_state.inventory_df
                                    )
                                st.toast("התמונה עודכנה בהצלחה!", icon="✅")
                                st.rerun()
                    with col_cancel:
                        if st.button("ביטול", use_container_width=True, key="upd_img_cancel"):
                            st.rerun()

                # ── סרגל חיפוש ────────────────────────────────────────────
                col_search, _ = st.columns([1, 1])
                with col_search:
                    search_term = st.text_input(
                        "🔍 חיפוש קל (לפי שם או מק\"ט):", placeholder="הקלידי כאן..."
                    )

                inv_display["_Original_Index"] = inv_display.index

                if search_term:
                    mask = (
                        inv_display["Fabric Name"].astype(str).str.contains(
                            search_term, case=False, na=False
                        ) |
                        inv_display["Fabric ID"].astype(str).str.contains(
                            search_term, case=False, na=False
                        )
                    )
                    filtered_inv = inv_display[mask]
                else:
                    filtered_inv = inv_display

                if filtered_inv.empty:
                    st.info("לא נמצאו בדים התואמים לחיפוש שלך.")
                else:
                    df_view = filtered_inv.rename(columns={
                        "Fabric Name": "שם הבד/צבע",
                        "Fabric ID": "מק\"ט",
                        "Image URL": "תמונה"
                    })

                    # עמודת בחירה תמיד פעילה
                    df_view["✔"] = False
                    cols = [
                        "✔", "תמונה", "כמות זמינה (מ')", "כמות בארגז (מ')",
                        "מק\"ט", "שם הבד/צבע", "_Original_Index"
                    ]
                    df_view = df_view[cols].copy()

                    # וידוא טיפוסי נתונים
                    df_view["מק\"ט"] = df_view["מק\"ט"].astype(str)
                    df_view["שם הבד/צבע"] = df_view["שם הבד/צבע"].astype(str)
                    df_view["כמות בארגז (מ')"] = pd.to_numeric(
                        df_view["כמות בארגז (מ')"], errors="coerce"
                    )
                    df_view["כמות זמינה (מ')"] = pd.to_numeric(
                        df_view["כמות זמינה (מ')"], errors="coerce"
                    )

                    config = {
                        "✔": st.column_config.CheckboxColumn("בחרי", default=False, width="small"),
                        "שם הבד/צבע": st.column_config.TextColumn("שם הבד/צבע", alignment="right"),
                        "מק\"ט": st.column_config.TextColumn("מק\"ט", width="small", alignment="right"),
                        "כמות בארגז (מ')": st.column_config.NumberColumn(
                            "בארגז (מ')", format="%.2f", width="small", alignment="right"
                        ),
                        "כמות זמינה (מ')": st.column_config.NumberColumn(
                            "זמין (מ')", format="%.2f", width="small", alignment="right"
                        ),
                        "תמונה": st.column_config.ImageColumn("תמונה", width="small"),
                        "_Original_Index": None,
                    }

                    st.caption("💡 טיפ: סמני שורה אחת לפעולות מחיקה/עדכון תמונה, או ערכי ישירות בטבלה.")

                    edited_inv = st.data_editor(
                        df_view,
                        use_container_width=True,
                        hide_index=True,
                        column_config=config,
                        key=f"inv_editor_{search_term}"
                    )

                    # ── זיהוי שורות מסומנות ───────────────────────────────
                    selected_rows = edited_inv[edited_inv["✔"] == True]
                    n_selected = len(selected_rows)

                    # ── כפתורי פעולה דינמיים ──────────────────────────────
                    if n_selected > 0:
                        st.markdown("---")
                        if n_selected == 1:
                            col_del, col_img, _ = st.columns([2, 2, 4])
                        else:
                            col_del, _ = st.columns([2, 6])
                            col_img = None

                        with col_del:
                            lbl = f"🗑️ מחיקת {n_selected} פריט(ים)"
                            if st.button(lbl, type="primary",
                                         use_container_width=True, key="btn_delete_sel"):
                                with st.spinner("מוחקת..."):
                                    ids_to_delete = selected_rows["מק\"ט"].tolist()
                                    st.session_state.inventory_df = (
                                        st.session_state.inventory_df[
                                            ~st.session_state.inventory_df["Fabric ID"].isin(ids_to_delete)
                                        ].reset_index(drop=True)
                                    )
                                    save_inventory_to_sheet(
                                        inventory_sheet, st.session_state.inventory_df
                                    )
                                st.toast("הפריטים שנבחרו נמחקו!", icon="✅")
                                st.rerun()

                        if col_img is not None:
                            with col_img:
                                if st.button("🖼️ עדכון תמונה",
                                             use_container_width=True, key="btn_update_img"):
                                    sel_orig_idx = int(selected_rows.iloc[0]["_Original_Index"])
                                    sel_name = str(selected_rows.iloc[0]["שם הבד/צבע"])
                                    _update_image_dialog(sel_orig_idx, sel_name)

                    # ── שמירת עריכות טקסט/מספרים ─────────────────────────
                    compare_cols = [c for c in df_view.columns if c != "✔"]
                    changed = not edited_inv[compare_cols].equals(df_view[compare_cols])
                    if changed:
                        st.markdown("---")
                        if st.button("💾 שמרי שינויים", type="primary", key="btn_save_edits"):
                            if edited_inv["מק\"ט"].duplicated().any():
                                st.error("❌ שגיאה: יש כפילות במק\"ט! בדקי שוב.")
                            elif edited_inv["שם הבד/צבע"].duplicated().any():
                                st.error("❌ שגיאה: יש כפילות בשם הבד! אנא השתמשי בשמות ייחודיים.")
                            else:
                                with st.spinner("שומרת..."):
                                    # Failsafe: guarantee string dtypes before .at[] assignment
                                    st.session_state.inventory_df["Fabric ID"] = (
                                        st.session_state.inventory_df["Fabric ID"].astype(str)
                                    )
                                    st.session_state.inventory_df["Fabric Name"] = (
                                        st.session_state.inventory_df["Fabric Name"].astype(str)
                                    )
                                    for idx, row in edited_inv.iterrows():
                                        orig_idx = int(row["_Original_Index"])
                                        st.session_state.inventory_df.at[orig_idx, "Fabric ID"] = (
                                            str(row["מק\"ט"]).strip()
                                        )
                                        st.session_state.inventory_df.at[orig_idx, "Fabric Name"] = (
                                            str(row["שם הבד/צבע"]).strip()
                                        )

                                        old_row = df_view.loc[idx]
                                        new_box = float(row["כמות בארגז (מ')"] or 0)
                                        new_avail = float(row["כמות זמינה (מ')"] or 0)
                                        old_box = float(old_row["כמות בארגז (מ')"] or 0)
                                        old_avail = float(old_row["כמות זמינה (מ')"] or 0)

                                        if "Initial Meters" not in st.session_state.inventory_df.columns:
                                            st.session_state.inventory_df["Initial Meters"] = 0.0
                                        if "Reserved Meters" not in st.session_state.inventory_df.columns:
                                            st.session_state.inventory_df["Reserved Meters"] = 0.0

                                        curr_initial = float(
                                            st.session_state.inventory_df.at[orig_idx, "Initial Meters"] or 0
                                        )

                                        if new_box != old_box:
                                            delta = new_box - old_box
                                            curr_initial = round(curr_initial + delta, 2)
                                            st.session_state.inventory_df.at[orig_idx, "Initial Meters"] = curr_initial

                                        if new_avail != old_avail:
                                            new_reserved = round(curr_initial - new_avail, 2)
                                            st.session_state.inventory_df.at[orig_idx, "Reserved Meters"] = (
                                                max(new_reserved, 0.0)
                                            )

                                    save_inventory_to_sheet(
                                        inventory_sheet, st.session_state.inventory_df
                                    )
                                st.toast("המלאי עודכן בהצלחה!", icon="✅")
                                st.rerun()
            else:
                st.info("עדיין אין בדים במערכת. עברי ללשונית 'הוספת בד חדש' כדי להתחיל!")

        # Excel export
    import io as _io_inv
    _iv = _io_inv.BytesIO()
    inventory_df[["Fabric ID", "Fabric Name", "Initial Meters"]].to_excel(
        _iv, index=False, engine="openpyxl"
    )
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
                uploaded_file = st.file_uploader(
                    "בחרי תמונה מהמכשיר", type=["jpg", "jpeg", "png"], key=f"img_up_{f_key}"
                )
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
                        f_img_clean = process_image(uploaded_file) if uploaded_file else ""

                        new_fabric = {
                            "Fabric ID": str(f_id).strip(),
                            "Fabric Name": str(f_name).strip(),
                            "Initial Meters": f_meters,
                            "Reserved Meters": 0.0,
                            "Image URL": f_img_clean.strip(),
                        }
                        st.session_state.inventory_df = pd.concat(
                            [st.session_state.inventory_df, pd.DataFrame([new_fabric])],
                            ignore_index=True
                        )
                        save_inventory_to_sheet(inventory_sheet, st.session_state.inventory_df)

                        st.session_state.fabric_form_key += 1
                        st.toast(f"הבד '{f_name}' התווסף למאגר בהצלחה!", icon="✅")
                        st.rerun()
