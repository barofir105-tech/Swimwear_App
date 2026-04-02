"""
Refactoring script: splits swimwear_app.py into modular files.
Run once from the project directory.
"""
import os, sys, textwrap

src = open('swimwear_app.py', encoding='utf-8').read()
lines = src.splitlines(keepends=True)

# ─────────────────────────────────────────
# Helper: strip the leading elif/if keyword and dedent body
# ─────────────────────────────────────────
def extract_body(raw_lines, start, end):
    """Return the body lines of a top-level if/elif block, dedented."""
    chunk = raw_lines[start:end]
    # First line is 'if/elif ... :' — skip it
    body = chunk[1:]
    # Strip exactly 4 spaces of indent from each line
    out = []
    for l in body:
        if l.startswith('    '):
            out.append(l[4:])
        else:
            out.append(l)
    return ''.join(out)

# ─────────────────────────────────────────
# Slice boundaries (0-indexed line numbers)
# ─────────────────────────────────────────
INV_S,  INV_E  = 319, 534
PAT_S,  PAT_E  = 537, 646
ORD_S,  ORD_E  = 649, 1149
CUST_S, CUST_E = 1152, 1271
CARD_S, CARD_E = 1271, 1393
FIN_S,  FIN_E  = 1396, 1824

# ─────────────────────────────────────────
# Create views/ directory
# ─────────────────────────────────────────
os.makedirs('views', exist_ok=True)
open('views/__init__.py', 'w').close()
print("Created views/__init__.py")

# ─────────────────────────────────────────
# utils.py  (lines 62-270 of original)
# ─────────────────────────────────────────
utils_header = """\
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import base64
from PIL import Image, ImageOps
import io
import json
import threading
import copy

"""
utils_body = ''.join(lines[62:270])   # from INVENTORY_IMAGE_THUMB to end of get_calculated_inventory

utils_content = utils_header + utils_body
open('utils.py', 'w', encoding='utf-8').write(utils_content)
print(f"Created utils.py ({len(utils_content)} chars)")

# ─────────────────────────────────────────
# views/inventory.py
# ─────────────────────────────────────────
inv_imports = """\
import streamlit as st
import pandas as pd
from utils import get_calculated_inventory, process_image


def render_inventory():
"""
inv_body = extract_body(lines, INV_S, INV_E)
open('views/inventory.py', 'w', encoding='utf-8').write(inv_imports + inv_body)
print(f"Created views/inventory.py")

# ─────────────────────────────────────────
# views/patterns.py
# ─────────────────────────────────────────
pat_imports = """\
import streamlit as st
import pandas as pd


def render_patterns():
"""
pat_body = extract_body(lines, PAT_S, PAT_E)
open('views/patterns.py', 'w', encoding='utf-8').write(pat_imports + pat_body)
print(f"Created views/patterns.py")

# ─────────────────────────────────────────
# views/orders.py
# ─────────────────────────────────────────
ord_imports = """\
import streamlit as st
import pandas as pd
from datetime import datetime


def render_orders():
"""
ord_body = extract_body(lines, ORD_S, ORD_E)
open('views/orders.py', 'w', encoding='utf-8').write(ord_imports + ord_body)
print(f"Created views/orders.py")

# ─────────────────────────────────────────
# views/customers.py
# ─────────────────────────────────────────
cust_imports = """\
import streamlit as st
import pandas as pd
from datetime import datetime


def render_customers():
"""
cust_body = extract_body(lines, CUST_S, CUST_E)

card_imports = """\

def render_customer_card():
"""
card_body = extract_body(lines, CARD_S, CARD_E)

open('views/customers.py', 'w', encoding='utf-8').write(
    cust_imports + cust_body + card_imports + card_body
)
print(f"Created views/customers.py")

# ─────────────────────────────────────────
# views/financial.py
# ─────────────────────────────────────────
fin_imports = """\
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from calendar import monthrange
import uuid
from utils import save_finance_data


def render_financial():
"""
fin_body = extract_body(lines, FIN_S, FIN_E)
open('views/financial.py', 'w', encoding='utf-8').write(fin_imports + fin_body)
print(f"Created views/financial.py")

print("\nDone. Now compile-checking all files...")
