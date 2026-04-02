"""
fix_views_v2.py — Properly indent all view bodies by adding 4 spaces to every line.
"""
import subprocess, sys

def wrap_as_function(raw_body_chunk, func_sig, bindings):
    """
    Takes the raw body text (already at 0-based indentation after stripping the elif line),
    adds 4-space indent to every line, and wraps it in a function def.
    """
    lines = raw_body_chunk.splitlines(keepends=True)
    indented = []
    for line in lines:
        if line.strip() == "":
            indented.append("\n")
        else:
            indented.append("    " + line)
    
    binding_block = "\n".join(f"    {b}" for b in bindings) + "\n\n"
    return func_sig + "\n" + binding_block + "".join(indented) + "\n"


# ── Load source ─────────────────────────────────────────────────────────────
src_lines = open("swimwear_app.py", encoding="utf-8").readlines()

def get_block(start, end):
    """Get lines[start:end], strip the first elif/if line, return as-is (0-indent)."""
    chunk = src_lines[start:end]
    first_line = chunk[0]
    # Remove 0-4 spaces from the beginning of each line (the elif was at indent 0)
    body = []
    for line in chunk[1:]:  # skip the elif/if line itself
        if line.startswith("    "):
            body.append(line[4:])  # strip one level of indent
        else:
            body.append(line)
    return "".join(body)


# ─────────────────────── views/inventory.py ────────────────────────────────
body = get_block(319, 534)
content = (
    "import streamlit as st\n"
    "import pandas as pd\n"
    "from utils import get_calculated_inventory, process_image\n\n\n"
    + wrap_as_function(body, "def render_inventory():", [
        "inventory_df = st.session_state.inventory_df",
        "inventory_sheet = st.session_state.inventory_sheet",
    ])
)
open("views/inventory.py", "w", encoding="utf-8").write(content)
print("Written views/inventory.py")

# ─────────────────────── views/patterns.py ─────────────────────────────────
body = get_block(537, 646)
content = (
    "import streamlit as st\n"
    "import pandas as pd\n\n\n"
    + wrap_as_function(body, "def render_patterns():", [
        "patterns_df = st.session_state.patterns_df",
        "patterns_sheet = st.session_state.patterns_sheet",
    ])
)
open("views/patterns.py", "w", encoding="utf-8").write(content)
print("Written views/patterns.py")

# ─────────────────────── views/orders.py ───────────────────────────────────
body = get_block(649, 1149)
content = (
    "import streamlit as st\n"
    "import pandas as pd\n"
    "from datetime import datetime\n"
    "from utils import get_next_order_id\n\n\n"
    + wrap_as_function(body, "def render_orders():", [
        "orders_df = st.session_state.orders_df",
        "orders_sheet = st.session_state.orders_sheet",
        "inventory_df = st.session_state.inventory_df",
        "inventory_sheet = st.session_state.inventory_sheet",
        "customers_df = st.session_state.customers_df",
        "customers_sheet = st.session_state.customers_sheet",
        "patterns_df = st.session_state.patterns_df",
    ])
)
open("views/orders.py", "w", encoding="utf-8").write(content)
print("Written views/orders.py")

# ─────────────────────── views/customers.py ────────────────────────────────
body_cust = get_block(1152, 1271)
body_card = get_block(1271, 1393)

cust_fn = wrap_as_function(body_cust, "def render_customers():", [
    "customers_df = st.session_state.customers_df",
    "customers_sheet = st.session_state.customers_sheet",
    "orders_df = st.session_state.orders_df",
])
card_fn = wrap_as_function(body_card, "def render_customer_card():", [
    "customers_df = st.session_state.customers_df",
    "customers_sheet = st.session_state.customers_sheet",
    "orders_df = st.session_state.orders_df",
    "orders_sheet = st.session_state.orders_sheet",
])

content = (
    "import streamlit as st\n"
    "import pandas as pd\n"
    "from datetime import datetime\n\n\n"
    + cust_fn + "\n\n" + card_fn
)
open("views/customers.py", "w", encoding="utf-8").write(content)
print("Written views/customers.py")

# ─────────────────────── views/financial.py ────────────────────────────────
body = get_block(1396, 1824)
content = (
    "import streamlit as st\n"
    "import pandas as pd\n"
    "import plotly.express as px\n"
    "from datetime import datetime, date\n"
    "from calendar import monthrange\n"
    "import uuid\n"
    "from utils import save_finance_data, get_standing_order_hits\n\n\n"
    + wrap_as_function(body, "def render_financial():", [
        "finance_data = st.session_state.finance_data",
        "finance_sheet = st.session_state.finance_sheet",
        "orders_df = st.session_state.orders_df",
    ])
)
open("views/financial.py", "w", encoding="utf-8").write(content)
print("Written views/financial.py")

# ─────────────────────── Compile check ─────────────────────────────────────
print("\nCompile checks:")
files = [
    "utils.py", "main.py",
    "views/inventory.py", "views/patterns.py", "views/orders.py",
    "views/customers.py", "views/financial.py",
]
all_ok = True
for f in files:
    r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True, text=True)
    status = "OK " if r.returncode == 0 else "ERR"
    if r.returncode != 0:
        all_ok = False
        print(f"  {status} {f}: {r.stderr.strip()[:120]}")
    else:
        print(f"  {status} {f}")

print("\nResult:", "ALL CLEAN" if all_ok else "ERRORS FOUND")
