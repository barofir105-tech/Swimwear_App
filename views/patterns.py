import streamlit as st
import pandas as pd


def render_patterns():
    patterns_df = st.session_state.patterns_df
    patterns_sheet = st.session_state.patterns_sheet

    st.title("✂️ ניהול גזרות")

    if patterns_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Patterns' ב-Google Sheets. צרי אותו כדי להתחיל לשמור גזרות.")
    else:
        st.subheader("📋 רשימת הגזרות")
        patterns_view = st.session_state.patterns_df.rename(
            columns={"Pattern Name": "שם הגזרה", "Category": "קטגוריה"}
        )

        cols = ["שם הגזרה", "קטגוריה"]
        if st.session_state.delete_mode_patterns:
            patterns_view["בחרי"] = False
            cols = ["בחרי"] + cols

        patterns_view = patterns_view[cols]
        patterns_cfg = {
            "שם הגזרה": st.column_config.TextColumn("שם הגזרה (ניתן לעריכה)"),
            "קטגוריה": st.column_config.SelectboxColumn("קטגוריה", options=["בגד ים שלם", "ביקיני"], required=True),
        }
        if st.session_state.delete_mode_patterns:
            patterns_cfg["בחרי"] = st.column_config.CheckboxColumn("בחרי", default=False)

        center_l, center_m, center_r = st.columns([1, 4, 1])
        with center_m:
            edited_patterns = st.data_editor(
                patterns_view,
                use_container_width=True,
                hide_index=True,
                column_config=patterns_cfg,
                key="patterns_editor",
            )

        col_space, col_btn_save, col_btn_select = st.columns([6, 2, 2])
        with col_btn_select:
            if not st.session_state.delete_mode_patterns:
                if st.button("בחרי", key="sel_pat", use_container_width=True):
                    st.session_state.delete_mode_patterns = True
                    st.rerun()
            else:
                if st.button("בטלי", key="canc_pat", use_container_width=True):
                    st.session_state.delete_mode_patterns = False
                    st.rerun()

        with col_btn_save:
            if st.session_state.delete_mode_patterns:
                patterns_to_delete = edited_patterns[edited_patterns["בחרי"] == True]
                if not patterns_to_delete.empty:
                    if st.button("מחקי מסומנות 🗑️", type="primary", use_container_width=True):
                        with st.spinner("מוחקת גזרות..."):
                            names_to_delete = patterns_to_delete["שם הגזרה"].astype(str).tolist()
                            st.session_state.patterns_df = st.session_state.patterns_df[
                                ~st.session_state.patterns_df["Pattern Name"].astype(str).isin(names_to_delete)
                            ]

                            patterns_sheet.clear()
                            save_patterns = st.session_state.patterns_df[["Pattern Name", "Category"]]
                            if save_patterns.empty:
                                patterns_sheet.update([["Pattern Name", "Category"]])
                            else:
                                patterns_sheet.update(
                                    [save_patterns.columns.values.tolist()] + save_patterns.values.tolist()
                                )

                            st.session_state.delete_mode_patterns = False
                            st.toast("הגזרות נמחקו בהצלחה!", icon="✅")
                            st.rerun()
            else:
                if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                    with st.spinner("שומרת בענן..."):
                        upd_pat = edited_patterns.copy()
                        if "בחרי" in upd_pat.columns:
                            upd_pat = upd_pat.drop(columns=["בחרי"])
                        upd_pat = upd_pat.rename(columns={"שם הגזרה (ניתן לעריכה)": "Pattern Name", "שם הגזרה": "Pattern Name", "קטגוריה": "Category"})
                        upd_pat = upd_pat[["Pattern Name", "Category"]]
                        upd_pat = upd_pat[upd_pat["Pattern Name"].astype(str).str.strip() != ""]
                        st.session_state.patterns_df = upd_pat.reset_index(drop=True)
                        patterns_sheet.clear()
                        if upd_pat.empty:
                            patterns_sheet.update([["Pattern Name", "Category"]])
                        else:
                            patterns_sheet.update([upd_pat.columns.values.tolist()] + upd_pat.values.tolist())
                        st.toast("הגזרות עודכנו!", icon="✅")
                        st.rerun()

        st.markdown("---")
        st.subheader("➕ הוספת גזרה חדשה")
        with st.form("add_pattern_form", clear_on_submit=True):
            p_name = st.text_input("שם הגזרה*")
            p_category = st.selectbox("קטגוריה*", ["בגד ים שלם", "ביקיני"])

            if st.form_submit_button("הוסיפי גזרה", type="primary"):
                p_name_clean = str(p_name).strip()
                if not p_name_clean:
                    st.warning("חובה להזין שם גזרה.")
                elif p_name_clean in st.session_state.patterns_df["Pattern Name"].astype(str).values:
                    st.error("❌ שגיאה: שם הגזרה כבר קיים במערכת.")
                else:
                    new_pattern = {"Pattern Name": p_name_clean, "Category": p_category}
                    st.session_state.patterns_df = pd.concat(
                        [st.session_state.patterns_df, pd.DataFrame([new_pattern])], ignore_index=True
                    )
                    if patterns_sheet.get_all_records() == []:
                        patterns_sheet.append_row(["Pattern Name", "Category"])
                    patterns_sheet.append_row([new_pattern["Pattern Name"], new_pattern["Category"]])
                    st.toast(f"הגזרה '{p_name_clean}' נוספה בהצלחה!", icon="✅")
                    st.rerun()


