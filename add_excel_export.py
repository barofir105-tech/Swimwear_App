import subprocess, sys, re

# ── Excel export helper to inject into each view ─────────────────────────
# We'll add a download button after the data_editor in key views.

# ─── views/orders.py: add export after the search/filter section ──────────
ord_text = open("views/orders.py", encoding="utf-8").read()
EXPORT_ORD = '''
            # Excel export
            _xls_buf = __import__("io").BytesIO()
            orders_df.to_excel(_xls_buf, index=False, engine="openpyxl")
            st.download_button(
                label="\\U0001f4e5 \\u05d9\\u05d9\\u05e6\\u05d5\\u05d0 \\u05d4\\u05d6\\u05de\\u05e0\\u05d5\\u05ea \\u05dc-Excel",
                data=_xls_buf.getvalue(),
                file_name="orders.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_orders_excel"
            )
'''
ANCHOR_ORD = '        else:\n            st.info("\\u05e2\\u05d3\\u05d9\\u05d9\\u05df \\u05d0\\u05d9\\u05df \\u05d4\\u05d6\\u05de\\u05e0\\u05d5\\u05ea'
# Instead of fragile string search, append the export button just before the final else of orders
old_else_ord = '        else:\n            st.info("\u05e2\u05d3\u05d9\u05d9\u05df \u05d0\u05d9\u05df \u05d4\u05d6\u05de\u05e0\u05d5\u05ea \u05d1\u05de\u05e2\u05e8\u05db\u05ea. \u05d4\u05d5\u05e1\u05d9\u05e4\u05d9 \u05d0\u05ea \u05d4\u05d4\u05d6\u05de\u05e0\u05d4 \u05d4\u05e8\u05d0\u05e9\u05d5\u05e0\u05d4 \u05dc\u05de\u05d8\u05d4!")'
new_else_ord = '''            # Excel export
            import io as _io_ord
            _xls_buf = _io_ord.BytesIO()
            orders_df.to_excel(_xls_buf, index=False, engine="openpyxl")
            st.download_button(
                "\U0001f4e5 \u05d9\u05d9\u05e6\u05d5\u05d0 \u05d4\u05d6\u05de\u05e0\u05d5\u05ea \u05dc-Excel",
                data=_xls_buf.getvalue(),
                file_name="orders.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_orders_excel"
            )

        else:
            st.info("\u05e2\u05d3\u05d9\u05d9\u05df \u05d0\u05d9\u05df \u05d4\u05d6\u05de\u05e0\u05d5\u05ea \u05d1\u05de\u05e2\u05e8\u05db\u05ea. \u05d4\u05d5\u05e1\u05d9\u05e4\u05d9 \u05d0\u05ea \u05d4\u05d4\u05d6\u05de\u05e0\u05d4 \u05d4\u05e8\u05d0\u05e9\u05d5\u05e0\u05d4 \u05dc\u05de\u05d8\u05d4!")'''

if old_else_ord in ord_text:
    ord_text = ord_text.replace(old_else_ord, new_else_ord, 1)
    open("views/orders.py", "w", encoding="utf-8").write(ord_text)
    print("OK  orders excel export")
else:
    print("SKIP orders (anchor not found)")

# ─── views/customers.py: export after customers table ──────────────────────
cust_text = open("views/customers.py", encoding="utf-8").read()
old_cust_export_anchor = '    else:\n        st.info("\u05d0\u05d9\u05df \u05dc\u05e7\u05d5\u05d7\u05d5\u05ea \u05d1\u05de\u05e2\u05e8\u05db\u05ea'
new_cust_section = '''    # Excel export
    import io as _io_cust
    _xb = _io_cust.BytesIO()
    customers_df.drop(columns=["Image URL"] if "Image URL" in customers_df.columns else [], errors="ignore").to_excel(_xb, index=False, engine="openpyxl")
    st.download_button(
        "\U0001f4e5 \u05d9\u05d9\u05e6\u05d5\u05d0 \u05dc\u05e7\u05d5\u05d7\u05d5\u05ea \u05dc-Excel",
        data=_xb.getvalue(),
        file_name="customers.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_customers_excel"
    )

    else:
        st.info("\u05d0\u05d9\u05df \u05dc\u05e7\u05d5\u05d7\u05d5\u05ea \u05d1\u05de\u05e2\u05e8\u05db\u05ea'''
if old_cust_export_anchor in cust_text:
    cust_text = cust_text.replace(old_cust_export_anchor, new_cust_section, 1)
    open("views/customers.py", "w", encoding="utf-8").write(cust_text)
    print("OK  customers excel export")
else:
    print("SKIP customers (anchor not found)")

# ─── views/inventory.py: export after inventory table ──────────────────────
inv_text = open("views/inventory.py", encoding="utf-8").read()
old_inv = '    with tab_add:'
new_inv_pre = '''    # Excel export (above "add fabric" tab)
    import io as _io_inv
    _iv = _io_inv.BytesIO()
    inventory_df[["Fabric ID", "Fabric Name", "Initial Meters"]].to_excel(_iv, index=False, engine="openpyxl")
    st.download_button(
        "\U0001f4e5 \u05d9\u05d9\u05e6\u05d5\u05d0 \u05de\u05dc\u05d0\u05d9 \u05dc-Excel",
        data=_iv.getvalue(),
        file_name="inventory.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_inventory_excel"
    )

    with tab_add:'''
if old_inv in inv_text:
    inv_text = inv_text.replace(old_inv, new_inv_pre, 1)
    open("views/inventory.py", "w", encoding="utf-8").write(inv_text)
    print("OK  inventory excel export")
else:
    print("SKIP inventory (anchor not found)")

# ─── Compile checks ──────────────────────────────────────────────────────
print("\nCompile checks:")
for f in ["views/orders.py", "views/customers.py", "views/inventory.py",
          "views/financial.py", "views/patterns.py", "views/dashboard.py"]:
    r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True, text=True)
    print(f"  {'OK ' if r.returncode==0 else 'ERR'} {f}" + ("" if r.returncode==0 else f" — {r.stderr.strip()[:100]}"))
