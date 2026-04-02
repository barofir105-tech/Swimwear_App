import re

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = """            fabric_options = ["בחרי בד..."] + (inventory_df["Fabric Name"].tolist() if not inventory_df.empty else ["אין בדים במלאי"])
            
            col_f1, col_f2 = st.columns(2)
            with col_f1: sel_fabric = st.selectbox("בחרי בד מהמלאי*", fabric_options)
            with col_f2: fabric_usage = st.number_input("כמות בד דרושה (במטרים)*", min_value=0.0, step=0.1)"""

new_block = """            fabric_options = ["בחרי בד..."] + (inventory_df["Fabric Name"].tolist() if not inventory_df.empty else ["אין בדים במלאי"])
            
            with st.expander("🖼️ קטלוג בדים חזותי (לחצי לתצוגה)"):
                st.markdown("כאן תוכלי לראות את כל הבדים שבמלאי כדי להקל על הבחירה בתיבה למטה.", unsafe_allow_html=True)
                if not inventory_df.empty:
                    html_grid = '<div dir="rtl" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 15px; padding: 10px;">'
                    for _, row in inventory_df.iterrows():
                        b64 = row.get("Image URL", "")
                        name = row.get("Fabric Name", "ללא שם")
                        sku = row.get("Fabric ID", "")
                        if b64 and str(b64).startswith("data:image"):
                            html_grid += f'''
                            <div style="position: relative; width: 100%; aspect-ratio: 1/1; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                                <img src="{b64}" style="width: 100%; height: 100%; object-fit: cover;" />
                                <div style="position: absolute; top: 0; left: 0; right: 0; padding: 10px 5px; background: linear-gradient(to bottom, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%); color: white; text-align: center; font-weight: bold; font-size: 14px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9); pointer-events: none;">
                                    {name}
                                </div>
                                <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 10px 5px; background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%); color: white; text-align: center; font-size: 13px; text-shadow: 1px 1px 3px rgba(0,0,0,0.9); pointer-events: none;">
                                    {sku}
                                </div>
                            </div>
                            '''
                    html_grid += '</div>'
                    st.markdown(html_grid, unsafe_allow_html=True)
                else:
                    st.info("אין תמונות בדים במלאי.")

            col_f1, col_f2 = st.columns(2)
            with col_f1: sel_fabric = st.selectbox("בחרי בד מהמלאי*", fabric_options)
            with col_f2: fabric_usage = st.number_input("כמות בד דרושה (במטרים)*", min_value=0.0, step=0.1)"""

text = text.replace(old_block, new_block)

with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Injected HTML catalog successfully")
