import re

with open(r'c:\Users\barof\OneDrive\Desktop\Swimwear_App\views\orders.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
target_imports = "from utils import get_next_order_id"
new_imports = "from utils import get_next_order_id, sync_order_to_finance, save_finance_data"
content = content.replace(target_imports, new_imports)

# 2. Creation Sync
target_creation = """                if inventory_sheet is not None:
                    inv_save_df = st.session_state.inventory_df[["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]].copy()
                    inv_save_df["Image URL"] = inv_save_df["Image URL"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
                    inventory_sheet.clear()
                    if inv_save_df.empty:
                        inventory_sheet.update([["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]])
                    else:
                        inventory_sheet.update([inv_save_df.columns.values.tolist()] + inv_save_df.values.tolist())

                st.toast(f"הזמנה {order_id} נוצרה ונשמרה בהצלחה!", icon="✅"); st.rerun()"""

new_creation = """                if inventory_sheet is not None:
                    inv_save_df = st.session_state.inventory_df[["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]].copy()
                    inv_save_df["Image URL"] = inv_save_df["Image URL"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
                    inventory_sheet.clear()
                    if inv_save_df.empty:
                        inventory_sheet.update([["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]])
                    else:
                        inventory_sheet.update([inv_save_df.columns.values.tolist()] + inv_save_df.values.tolist())

                changed_f = sync_order_to_finance(order_row_dict, st.session_state.finance_data)
                if changed_f:
                    save_finance_data(st.session_state.finance_data)

                st.toast(f"הזמנה {order_id} נוצרה ונשמרה בהצלחה!", icon="✅"); st.rerun()"""

content = content.replace(target_creation, new_creation)

# 3. Deletion Sync
target_deletion = """                                st.session_state.delete_mode_orders = False
                                st.toast("ההזמנות נמחקו!", icon="✅"); st.rerun()"""

new_deletion = """                                any_f_changes = False
                                for _, d_row in deleted_full_rows.iterrows():
                                    d_dict = d_row.to_dict()
                                    d_dict["Payment Status"] = "🔴"
                                    d_dict["Price"] = 0.0
                                    if sync_order_to_finance(d_dict, st.session_state.finance_data):
                                        any_f_changes = True
                                if any_f_changes:
                                    save_finance_data(st.session_state.finance_data)

                                st.session_state.delete_mode_orders = False
                                st.toast("ההזמנות נמחקו!", icon="✅"); st.rerun()"""

content = content.replace(target_deletion, new_deletion)

# 4. Edit Sync
target_edit_loop = """                                today_str = datetime.now().strftime("%d/%m/%Y")
                                for o_id, row in save_indexed.iterrows():"""

new_edit_loop = """                                any_f_changes_edit = False
                                today_str = datetime.now().strftime("%d/%m/%Y")
                                for o_id, row in save_indexed.iterrows():"""

content = content.replace(target_edit_loop, new_edit_loop)

target_edit_loop_end = """                                    else:
                                        save_indexed.at[o_id, "Payment Date"] = ""

                                orders_indexed.update(save_indexed)"""

new_edit_loop_end = """                                    else:
                                        save_indexed.at[o_id, "Payment Date"] = ""

                                    # Sync finance
                                    row_dict = row.to_dict()
                                    row_dict["Order ID"] = o_id
                                    if sync_order_to_finance(row_dict, st.session_state.finance_data):
                                        any_f_changes_edit = True

                                orders_indexed.update(save_indexed)"""

content = content.replace(target_edit_loop_end, new_edit_loop_end)

target_edit_save = """                                st.session_state.orders_df = final_save
                                orders_sheet.clear()
                                orders_sheet.update([final_save_df.columns.values.tolist()] + final_save_df.values.tolist())
                                st.toast("נשמר בהצלחה!", icon="✅"); st.rerun()"""

new_edit_save = """                                st.session_state.orders_df = final_save
                                orders_sheet.clear()
                                orders_sheet.update([final_save_df.columns.values.tolist()] + final_save_df.values.tolist())
                                
                                if any_f_changes_edit:
                                    save_finance_data(st.session_state.finance_data)

                                st.toast("נשמר בהצלחה!", icon="✅"); st.rerun()"""

content = content.replace(target_edit_save, new_edit_save)

with open(r'c:\Users\barof\OneDrive\Desktop\Swimwear_App\views\orders.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated orders.py successfully.")
