"""
fix_views.py — Adds session_state bindings and fixes indentation in all view files.
"""
import re, os

def add_session_state_header(body, bindings):
    """Prepend session state local variable bindings to a render function body."""
    header = "\n".join(f"    {b}" for b in bindings) + "\n\n"
    return header + body

def indent_body(raw: str) -> str:
    """Ensure every non-empty line in the body has at least 4 spaces of indent."""
    lines = raw.splitlines(keepends=True)
    out = []
    for line in lines:
        if line.strip() == "":
            out.append(line)
        elif not line.startswith("    ") and not line.startswith("\t"):
            out.append("    " + line)
        else:
            out.append(line)
    return "".join(out)


# ─────────────────────── inventory.py ──────────────────────────────────────
inv = open("views/inventory.py", encoding="utf-8").read()
# Fix indentation of body
inv_lines = inv.splitlines(keepends=True)
header_end = next(i for i, l in enumerate(inv_lines) if l.startswith("def render_inventory"))
prefix = "".join(inv_lines[:header_end+1])
body = "".join(inv_lines[header_end+1:])
body = indent_body(body)
# Inject session_state bindings at top of function
bindings = [
    "inventory_df = st.session_state.inventory_df",
    "inventory_sheet = st.session_state.inventory_sheet",
]
open("views/inventory.py", "w", encoding="utf-8").write(
    prefix + add_session_state_header(body, bindings)
)
print("Fixed views/inventory.py")


# ─────────────────────── patterns.py ───────────────────────────────────────
pat = open("views/patterns.py", encoding="utf-8").read()
pat_lines = pat.splitlines(keepends=True)
header_end = next(i for i, l in enumerate(pat_lines) if l.startswith("def render_patterns"))
prefix = "".join(pat_lines[:header_end+1])
body = "".join(pat_lines[header_end+1:])
body = indent_body(body)
bindings = [
    "patterns_df = st.session_state.patterns_df",
    "patterns_sheet = st.session_state.patterns_sheet",
]
open("views/patterns.py", "w", encoding="utf-8").write(
    prefix + add_session_state_header(body, bindings)
)
print("Fixed views/patterns.py")


# ─────────────────────── orders.py ─────────────────────────────────────────
ord_text = open("views/orders.py", encoding="utf-8").read()
ord_lines = ord_text.splitlines(keepends=True)
header_end = next(i for i, l in enumerate(ord_lines) if l.startswith("def render_orders"))
prefix = "".join(ord_lines[:header_end+1])
body = "".join(ord_lines[header_end+1:])
body = indent_body(body)
bindings = [
    "orders_df = st.session_state.orders_df",
    "orders_sheet = st.session_state.orders_sheet",
    "inventory_df = st.session_state.inventory_df",
    "inventory_sheet = st.session_state.inventory_sheet",
    "customers_df = st.session_state.customers_df",
    "customers_sheet = st.session_state.customers_sheet",
    "patterns_df = st.session_state.patterns_df",
]
# Also add get_next_order_id import
prefix = prefix.replace(
    "from datetime import datetime",
    "from datetime import datetime\nfrom utils import get_next_order_id"
)
open("views/orders.py", "w", encoding="utf-8").write(
    prefix + add_session_state_header(body, bindings)
)
print("Fixed views/orders.py")


# ─────────────────────── customers.py ──────────────────────────────────────
cust_text = open("views/customers.py", encoding="utf-8").read()
cust_lines = cust_text.splitlines(keepends=True)

def fix_function(lines, func_name, bindings):
    header_end = next(i for i, l in enumerate(lines) if l.startswith(f"def {func_name}"))
    prefix = "".join(lines[:header_end+1])
    body_lines = lines[header_end+1:]
    # find next def or end
    next_def = next((i for i, l in enumerate(body_lines) if l.startswith("def ")), len(body_lines))
    body = "".join(body_lines[:next_def])
    rest = "".join(body_lines[next_def:])
    body = indent_body(body)
    return prefix + add_session_state_header(body, bindings), rest

cust_bindings = [
    "customers_df = st.session_state.customers_df",
    "customers_sheet = st.session_state.customers_sheet",
    "orders_df = st.session_state.orders_df",
]
card_bindings = [
    "customers_df = st.session_state.customers_df",
    "customers_sheet = st.session_state.customers_sheet",
    "orders_df = st.session_state.orders_df",
    "orders_sheet = st.session_state.orders_sheet",
]

cust_part, rest = fix_function(cust_lines, "render_customers", cust_bindings)
rest_lines = rest.splitlines(keepends=True)
card_part, _ = fix_function(rest_lines, "render_customer_card", card_bindings)

open("views/customers.py", "w", encoding="utf-8").write(cust_part + card_part)
print("Fixed views/customers.py")


# ─────────────────────── financial.py ──────────────────────────────────────
fin_text = open("views/financial.py", encoding="utf-8").read()
fin_lines = fin_text.splitlines(keepends=True)
header_end = next(i for i, l in enumerate(fin_lines) if l.startswith("def render_financial"))
prefix = "".join(fin_lines[:header_end+1])
body = "".join(fin_lines[header_end+1:])
body = indent_body(body)
bindings = [
    "finance_data = st.session_state.finance_data",
    "finance_sheet = st.session_state.finance_sheet",
    "orders_df = st.session_state.orders_df",
]
# Add missing imports at top
prefix = prefix.replace(
    "from utils import save_finance_data",
    "from utils import save_finance_data, get_standing_order_hits"
)
open("views/financial.py", "w", encoding="utf-8").write(
    prefix + add_session_state_header(body, bindings)
)
print("Fixed views/financial.py")

print("\nAll view files fixed. Running compile checks...")
import subprocess, sys
all_ok = True
for f in ["utils.py", "main.py", "views/inventory.py", "views/patterns.py",
          "views/orders.py", "views/customers.py", "views/financial.py"]:
    r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  OK  {f}")
    else:
        print(f"  ERR {f}: {r.stderr.strip()}")
        all_ok = False

print("\n" + ("✅ All files compile cleanly." if all_ok else "❌ Some files have errors."))
