"""
utils.py — Shared helpers, Google Sheets data-fetching, and pure utility functions.
The `spreadsheet` gspread object is passed explicitly to fetch functions.
`save_finance_data` retrieves the connection from st.session_state._spreadsheet
so it can be called from background threads without needing a parameter.
"""

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

# ── Constants ─────────────────────────────────────────────────────────────
INVENTORY_IMAGE_THUMB = (240, 240)


# ── Google Sheets connection (cached for lifetime of server process) ──────
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    
    # Try Streamlit Secrets first (for Cloud deployment)
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), 
            scopes=scopes
        )
    else:
        # Fallback to local file (for local development)
        creds = Credentials.from_service_account_file("google_credentials.json", scopes=scopes)
        
    return gspread.authorize(creds)


# ── Image helpers ─────────────────────────────────────────────────────────
def process_image(uploaded_file, max_size=INVENTORY_IMAGE_THUMB):
    """Resize and base64-encode an uploaded image for storage in Google Sheets."""
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img = ImageOps.fit(img, max_size)
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            st.error(f"שגיאה בעיבוד התמונה: {e}")
            return ""
    return ""


# ── Data Fetching ─────────────────────────────────────────────────────────
def fetch_customers_from_cloud(spreadsheet):
    try:
        sheet = spreadsheet.worksheet("Customers")
        df = pd.DataFrame(sheet.get_all_records())
        if not df.empty and "Phone Number" in df.columns:
            df["Phone Number"] = df["Phone Number"].astype(str).apply(
                lambda x: "0" + x if len(x) == 9 and not x.startswith("0") else x
            )
        else:
            df = pd.DataFrame(columns=["Phone Number", "First Name", "Last Name", "Address", "Notes"])
        return df, sheet
    except:
        return pd.DataFrame(columns=["Phone Number", "First Name", "Last Name", "Address", "Notes"]), None


def fetch_orders_from_cloud(spreadsheet):
    _COLS = [
        "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
        "Top Size", "Bottom Size", "Custom Size", "Top Cut", "Bottom Cut", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
        "Swimsuit Type", "Pattern", "Order Notes", "Status", "Payment Status", "Supply Type", "Price", "Payment Date",
    ]
    try:
        sheet = spreadsheet.worksheet("Orders")
        df = pd.DataFrame(sheet.get_all_records())
        if not df.empty and "Phone Number" in df.columns:
            df["Phone Number"] = df["Phone Number"].astype(str).apply(
                lambda x: "0" + x if len(x) == 9 and not x.startswith("0") else x
            )
            for col in ["Payment Date", "Swimsuit Type", "Pattern", "Top Cut", "Bottom Cut", "Order Notes", "Fabric 2", "Fabric Usage 2"]:
                if col not in df.columns:
                    df[col] = ""
            # One-time migration for old ORD-XXXX IDs
            if df["Order ID"].astype(str).str.contains("ORD-").any():
                df["Order ID"] = [f"{i+1:04d}" for i in range(len(df))]
                sheet.clear()
                sheet.update([df.columns.values.tolist()] + df.values.tolist())
        else:
            df = pd.DataFrame(columns=_COLS)
        return df, sheet
    except:
        return pd.DataFrame(columns=_COLS), None


def fetch_inventory_from_cloud(spreadsheet):
    try:
        sheet = spreadsheet.worksheet("Inventory")
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty:
            df = pd.DataFrame(columns=["Fabric ID", "Fabric Name", "Initial Meters", "Reserved Meters", "Image URL"])
        else:
            if "Reserved Meters" not in df.columns:
                df["Reserved Meters"] = 0.0
            if "Image URL" in df.columns:
                df["Image URL"] = df["Image URL"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
        return df, sheet
    except:
        return pd.DataFrame(columns=["Fabric ID", "Fabric Name", "Initial Meters", "Reserved Meters", "Image URL"]), None


def fetch_patterns_from_cloud(spreadsheet):
    try:
        sheet = spreadsheet.worksheet("Patterns")
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty:
            df = pd.DataFrame(columns=["Pattern Name", "Category"])
        else:
            if "Pattern Name" not in df.columns:
                df["Pattern Name"] = ""
            if "Category" not in df.columns:
                df["Category"] = ""
            df = df[["Pattern Name", "Category"]]
            df["Pattern Name"] = df["Pattern Name"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
            df["Category"] = df["Category"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
        return df, sheet
    except:
        return pd.DataFrame(columns=["Pattern Name", "Category"]), None


def fetch_finance_from_cloud(spreadsheet):
    _EMPTY = {"settings": {"currency": "₪"}, "month_settings": {}, "monthly_expenses": {}, "standing_orders": []}
    try:
        sheet = spreadsheet.worksheet("Finance")
        raw_value = "".join(sheet.col_values(1))
        if not raw_value.strip():
            return _EMPTY, sheet
        data = json.loads(raw_value)
        for key in ["settings", "month_settings", "monthly_expenses", "standing_orders"]:
            data.setdefault(key, {} if key != "standing_orders" else [])
        return data, sheet
    except:
        return _EMPTY, None


# ── Finance save (threaded, uses session_state connection) ────────────────
def _background_save_finance(data_snapshot: dict) -> None:
    try:
        # Re-open the spreadsheet using the cached client
        client = init_connection()
        sp = client.open("SwimwearDB")
        sheet = sp.worksheet("Finance")
        json_string = json.dumps(data_snapshot, ensure_ascii=False)
        chunk_size = 40000
        chunks = [json_string[i:i + chunk_size] for i in range(0, len(json_string), chunk_size)]
        sheet.clear()
        sheet.update(range_name=f"A1:A{len(chunks)}", values=[[c] for c in chunks])
    except Exception as e:
        print(f"Background save finance failed: {e}")


def save_finance_data(data: dict) -> None:
    """Saves finance JSON to Google Sheets in a background thread (non-blocking)."""
    data_snapshot = copy.deepcopy(data)
    thread = threading.Thread(target=_background_save_finance, args=(data_snapshot,))
    thread.start()


# ── Business logic helpers ────────────────────────────────────────────────
def get_calculated_inventory():
    """Returns inventory DataFrame with computed availability columns according to 3 strict rules."""
    inv_df = st.session_state.inventory_df.copy()
    if inv_df.empty:
        return inv_df
    
    # ── Strict Definitions ──────────────────────────────────────────────────
    # 'In Box' = Initial Meters (Physical)
    # 'Available' = Initial Meters - Reserved Meters
    # Rule 3 (Hard Cap): Available <= In Box (Reserved >= 0)
    
    if "Initial Meters" not in inv_df.columns:
        inv_df["Initial Meters"] = 0.0
    inv_df["Initial Meters"] = pd.to_numeric(inv_df["Initial Meters"], errors="coerce").fillna(0.0).astype(float)
    
    if "Reserved Meters" not in inv_df.columns:
        inv_df["Reserved Meters"] = 0.0
    inv_df["Reserved Meters"] = pd.to_numeric(inv_df["Reserved Meters"], errors="coerce").fillna(0.0).astype(float)
    
    # Calculate display columns
    inv_df["כמות בארגז (מ')"] = inv_df["Initial Meters"]
    inv_df["כמות זמינה (מ')"] = inv_df["Initial Meters"] - inv_df["Reserved Meters"]
    
    # Rule 3 Enforcement (Hard Cap/Safety Override)
    # If Reserved < 0 (Available > Box), set Available = Box (Reserved = 0)
    mask_over = inv_df["כמות זמינה (מ')"] > inv_df["כמות בארגז (מ')"]
    if mask_over.any():
        inv_df.loc[mask_over, "כמות זמינה (מ')"] = inv_df.loc[mask_over, "כמות בארגז (מ')"]
        inv_df.loc[mask_over, "Reserved Meters"] = 0.0
    
    return inv_df


def get_next_order_id(df) -> str:
    """Returns the next sequential 4-digit Order ID string."""
    if df.empty:
        return "0001"
    valid_ids = pd.to_numeric(df["Order ID"], errors="coerce")
    max_id = valid_ids.max()
    if pd.isna(max_id):
        return "0001"
    return f"{int(max_id) + 1:04d}"


def get_standing_order_hits(order, rng_start, rng_end) -> int:
    """Returns the number of times a standing order fires within a date range."""
    try:
        so_start = pd.to_datetime(order["start_date"]).date()
        so_end = pd.to_datetime(order["end_date"]).date()
    except:
        return 0

    actual_end = min(rng_end, so_end)
    if rng_start > actual_end or so_start > rng_end:
        return 0

    curr = pd.to_datetime(so_start)
    actual_end_dt = pd.to_datetime(actual_end)
    rng_start_dt = pd.to_datetime(rng_start)

    freq = order.get("frequency", "Monthly")
    if freq == "Monthly":
        offset = pd.DateOffset(months=1)
    elif freq == "Yearly":
        offset = pd.DateOffset(years=1)
    elif freq == "Custom":
        val = int(order.get("custom_interval", 1))
        unit = order.get("custom_unit", "Months")
        offset = {
            "Days": pd.DateOffset(days=val),
            "Weeks": pd.DateOffset(weeks=val),
            "Months": pd.DateOffset(months=val),
            "Years": pd.DateOffset(years=val),
        }.get(unit, pd.DateOffset(months=1))
        if val <= 0:
            offset = pd.DateOffset(months=1)
    else:
        offset = pd.DateOffset(months=1)

    hits = 0
    while curr <= actual_end_dt:
        if curr >= rng_start_dt:
            hits += 1
        curr += offset
    return hits


def is_standing_order_active(order: dict, target_year: int, target_month: int) -> bool:
    start_date = datetime.fromisoformat(order["start_date"]).date()
    end_date = datetime.fromisoformat(order["end_date"]).date()
    target_period = target_year * 12 + target_month
    start_period = start_date.year * 12 + start_date.month
    end_period = end_date.year * 12 + end_date.month
    if target_period < start_period or target_period > end_period:
        return False
    if order["frequency"] == "Monthly":
        return True
    return target_month == start_date.month

def sync_order_to_finance(order_row: dict, finance_data: dict) -> bool:
    """
    Evaluates order payment status and creates persistent transactions in finance_data.
    Returns True if changes were made to finance_data, otherwise False.
    """
    if "transactions" not in finance_data:
        finance_data["transactions"] = []

    order_id = str(order_row.get("Order ID", "???"))
    customer_name = str(order_row.get("Customer Name", ""))
    payment_status = str(order_row.get("Payment Status", "")).strip()

    # Normalize payment status emoji
    for st in ["🔴", "🧡", "💚"]:
        if st in payment_status:
            payment_status = st
            break

    try:
        total_price = float(order_row.get("Price", 0.0))
    except (ValueError, TypeError):
        total_price = 0.0

    today_str = date.today().strftime("%Y-%m-%d")

    # Get existing automated transactions for this order
    existing_txns = [t for t in finance_data["transactions"] if t.get("order_id") == order_id and t.get("is_automated")]
    amount_paid = sum(float(t.get("amount", 0.0)) for t in existing_txns)

    target_amount = 0.0
    payment_desc = ""
    icon = ""

    if payment_status == "💚":
        target_amount = total_price
        payment_desc = "תשלום סופי"
        icon = "💚"
    elif payment_status == "🧡":
        target_amount = total_price * 0.5
        payment_desc = "מקדמה"
        icon = "🧡"
    else: # "🔴" or other
        target_amount = 0.0
        payment_desc = "קיזוז/החזר"
        icon = "↩️"

    balance_due = target_amount - amount_paid
    
    # We round to avoid floating point issues
    if abs(balance_due) < 0.01:
        return False
        
    import uuid
    tx_id = f"Order_{order_id}_{uuid.uuid4().hex[:8]}"

    if balance_due > 0:
        new_transaction = {
            "id": tx_id,
            "name": f"הזמנה #{order_id} - \"{customer_name}\" [{icon} {payment_desc}]",
            "amount": float(balance_due),
            "Type": "Income",
            "Item": str(order_row.get("Item", "כללי")),
            "date": today_str,
            "order_id": order_id,
            "payment_type": payment_desc,
            "is_automated": True,
            "icon": icon
        }
        finance_data["transactions"].append(new_transaction)
        return True

    elif balance_due < 0:
        # Negative income for refunds
        new_transaction = {
            "id": tx_id,
            "name": f"הזמנה #{order_id} - \"{customer_name}\" [{icon} קיזוז]",
            "amount": float(balance_due),  # negative amount
            "Type": "Income",  
            "Item": str(order_row.get("Item", "כללי")),
            "date": today_str,
            "order_id": order_id,
            "payment_type": "offset",
            "is_automated": True,
            "icon": "↩️"
        }
        finance_data["transactions"].append(new_transaction)
        return True

        
    return False
