import re

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update get_calculated_inventory
old_inventory_func = """def get_calculated_inventory():
    inv_df = st.session_state.inventory_df.copy()
    ord_df = st.session_state.orders_df.copy()

    if inv_df.empty: return inv_df

    inv_df["Initial Meters"] = pd.to_numeric(inv_df["Initial Meters"], errors='coerce').fillna(0)

    if not ord_df.empty and "Fabric Usage" in ord_df.columns:
        ord_df["Fabric Usage"] = pd.to_numeric(ord_df["Fabric Usage"], errors='coerce').fillna(0)
        # מחשבים את צריכת כל הבדים מכל ההזמנות אי פעם כדי שכאשר הזמנה נמסרת הבד עדיין יישאר מנוכה מהמלאי
        # כפי שקורה במציאות - הבד נגזר גם אם ההזמנה סופקה.
        usage_by_fabric = ord_df.groupby("Fabric")["Fabric Usage"].sum().reset_index()

        inv_df = inv_df.merge(usage_by_fabric, left_on="Fabric Name", right_on="Fabric", how="left").fillna(0)
        inv_df["כמות זמינה (מ')"] = inv_df["Initial Meters"] - inv_df["Fabric Usage"]
        inv_df = inv_df.drop(columns=["Fabric Usage", "Fabric"], errors='ignore')
    else:
        inv_df["כמות זמינה (מ')"] = inv_df["Initial Meters"]

    return inv_df"""

new_inventory_func = """def get_calculated_inventory():
    inv_df = st.session_state.inventory_df.copy()
    ord_df = st.session_state.orders_df.copy()

    if inv_df.empty: return inv_df

    inv_df["Initial Meters"] = pd.to_numeric(inv_df["Initial Meters"], errors='coerce').fillna(0)

    if not ord_df.empty and "Fabric Usage" in ord_df.columns:
        ord_df["Fabric Usage"] = pd.to_numeric(ord_df["Fabric Usage"], errors='coerce').fillna(0)
        
        # 1. Used by ALL orders (for Available Amount)
        all_usage = ord_df.groupby("Fabric")["Fabric Usage"].sum().reset_index()
        all_usage = all_usage.rename(columns={"Fabric Usage": "All_Usage"})
        
        # 2. Used by DELIVERED orders (for Amount in Box)
        # Assuming "✅ נמסרה ללקוחה" is the EXACT status text
        delivered_mask = ord_df["Status"] == "✅ נמסרה ללקוחה"
        delivered_usage = ord_df[delivered_mask].groupby("Fabric")["Fabric Usage"].sum().reset_index()
        delivered_usage = delivered_usage.rename(columns={"Fabric Usage": "_Delivered_Usage"})
        
        inv_df = inv_df.merge(all_usage, left_on="Fabric Name", right_on="Fabric", how="left").fillna({"All_Usage": 0})
        inv_df = inv_df.merge(delivered_usage, left_on="Fabric Name", right_on="Fabric", how="left").fillna({"_Delivered_Usage": 0})
        
        inv_df["כמות בארגז (מ')"] = inv_df["Initial Meters"] - inv_df["_Delivered_Usage"]
        inv_df["כמות זמינה (מ')"] = inv_df["Initial Meters"] - inv_df["All_Usage"]
        
        inv_df = inv_df.drop(columns=["All_Usage", "Fabric_x", "Fabric_y"], errors='ignore')
    else:
        inv_df["כמות בארגז (מ')"] = inv_df["Initial Meters"]
        inv_df["כמות זמינה (מ')"] = inv_df["Initial Meters"]
        inv_df["_Delivered_Usage"] = 0.0

    return inv_df"""

text = text.replace(old_inventory_func, new_inventory_func)

# 2. Update rename mapping
old_rename = """                    df_view = filtered_inv.rename(columns={
                        "Fabric Name": "שם הבד/צבע",
                        "Fabric ID": "מק\"ט",
                        "Initial Meters": "כמות בארגז (מ')",
                        "Image URL": "תמונה"
                    })"""

new_rename = """                    df_view = filtered_inv.rename(columns={
                        "Fabric Name": "שם הבד/צבע",
                        "Fabric ID": "מק\"ט",
                        "Image URL": "תמונה"
                    })"""
text = text.replace(old_rename, new_rename)

# 3. Update cols list
old_cols = """                    cols = ["תמונה", "כמות זמינה (מ')", "כמות בארגז (מ')", "מק\"ט", "שם הבד/צבע", "_Original_Index"]"""
new_cols = """                    cols = ["תמונה", "כמות זמינה (מ')", "כמות בארגז (מ')", "מק\"ט", "שם הבד/צבע", "_Original_Index", "_Delivered_Usage"]"""
text = text.replace(old_cols, new_cols)

# 4. Update config dict
old_config = """                    config = {
                        "שם הבד/צבע": st.column_config.TextColumn("שם הבד/צבע (ניתן לערוך)"),
                        "מק\"ט": st.column_config.TextColumn("מק\"ט (ניתן לערוך)"),
                        "כמות בארגז (מ')": st.column_config.NumberColumn("כמות בארגז (מ')", format="%g"),
                        "כמות זמינה (מ')": st.column_config.NumberColumn("כמות זמינה (מ')", format="%g", disabled=True),
                        "תמונה": st.column_config.ImageColumn("תמונה"),
                        "_Original_Index": None,  # הסתרת עמודת אינדקס העזר
                    }"""

new_config = """                    config = {
                        "שם הבד/צבע": st.column_config.TextColumn("שם הבד/צבע (ניתן לערוך)"),
                        "מק\"ט": st.column_config.TextColumn("מק\"ט (ניתן לערוך)"),
                        "כמות בארגז (מ')": st.column_config.NumberColumn("כמות בארגז (מ')", format="%g"),
                        "כמות זמינה (מ')": st.column_config.NumberColumn("כמות זמינה (מ')", format="%g", disabled=True),
                        "תמונה": st.column_config.ImageColumn("תמונה"),
                        "_Original_Index": None,  # הסתרת עמודת אינדקס העזר
                        "_Delivered_Usage": None,  # הסתרת עמודת צריכה מנמסרו
                    }"""
text = text.replace(old_config, new_config)

# 5. Update save loop
old_save_loop = """                                            # חילוץ נתוני העריכה ומיזוגם בחזרה לטבלת המלאי בהתאם לאינדקס המקורי
                                            for _, row in edited_inv.iterrows():
                                                orig_idx = int(row["_Original_Index"])
                                                st.session_state.inventory_df.at[orig_idx, "Fabric ID"] = str(row["מק\"ט"]).strip()
                                                st.session_state.inventory_df.at[orig_idx, "Fabric Name"] = str(row["שם הבד/צבע"]).strip()
                                                st.session_state.inventory_df.at[orig_idx, "Initial Meters"] = row["כמות בארגז (מ')"]
                                            
                                            save_df = st.session_state.inventory_df[["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]]"""

new_save_loop = """                                            # חילוץ נתוני העריכה ומיזוגם בחזרה לטבלת המלאי בהתאם לאינדקס המקורי
                                            for _, row in edited_inv.iterrows():
                                                orig_idx = int(row["_Original_Index"])
                                                st.session_state.inventory_df.at[orig_idx, "Fabric ID"] = str(row["מק\"ט"]).strip()
                                                st.session_state.inventory_df.at[orig_idx, "Fabric Name"] = str(row["שם הבד/צבע"]).strip()
                                                
                                                # Save inverse logic: Initial Meters (Total Bought) = Current Box + Delivered. 
                                                st.session_state.inventory_df.at[orig_idx, "Initial Meters"] = float(row["כמות בארגז (מ')"]) + float(row.get("_Delivered_Usage", 0))
                                            
                                            save_df = st.session_state.inventory_df[["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]]"""
text = text.replace(old_save_loop, new_save_loop)

# 6. Check if Total Metrics string calculation needs an update (Lines 206)
# `total_qty = pd.to_numeric(inv_display["Initial Meters"], errors='coerce').fillna(0).sum()`
# Actually, `inv_display["כמות בארגז (מ')"]` should be used instead of `Initial Meters` for visual accuracy!
# Because the metric says "סה״כ מטרים (התחלתי)", maybe they meant Total Box? Let's check.
old_metric_logic = """            total_qty = pd.to_numeric(inv_display["Initial Meters"], errors='coerce').fillna(0).sum()
            total_available = pd.to_numeric(inv_display["כמות זמינה (מ')"], errors='coerce').fillna(0).sum()
            
            # עיצוב מותאם למדדים
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("סוגי בדים במלאי", f"{total_fabrics}")
            with m2:
                st.metric("סה״כ מטרים (התחלתי)", f"{total_qty:g}")
            with m3:
                st.metric("סה״כ מטרים (זמין כעת)", f"{total_available:g}")"""

new_metric_logic = """            total_box = pd.to_numeric(inv_display["כמות בארגז (מ')"], errors='coerce').fillna(0).sum()
            total_available = pd.to_numeric(inv_display["כמות זמינה (מ')"], errors='coerce').fillna(0).sum()
            
            # עיצוב מותאם למדדים
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("סוגי בדים במלאי", f"{total_fabrics}")
            with m2:
                st.metric("סה״כ מטרים בארגז", f"{total_box:g}")
            with m3:
                st.metric("סה״כ מטרים פנויים", f"{total_available:g}")"""
text = text.replace(old_metric_logic, new_metric_logic)

with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("done")
