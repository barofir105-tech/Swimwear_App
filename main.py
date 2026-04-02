"""
swimwear_app.py — Main entrypoint (thin router).
Handles: page config, global CSS, Google Sheets connection,
         session state initialisation, navbar, and view routing.
"""

import streamlit as st

# ── Page config (MUST be first Streamlit call) ─────────────────────────
st.set_page_config(page_title="Kalimi Manager", page_icon="👙", layout="wide")

# ── Global CSS ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── RTL ── */
    .stApp { direction: rtl; }
    p, div, input, label, h1, h2, h3, h4, h5, h6 { text-align: right !important; }
    div[data-testid="stAlert"] > div { direction: rtl; text-align: right; }

    /* ── Hide Streamlit chrome ── */
    [data-testid="stHeader"],
    [data-testid="stAppHeader"],
    [data-testid="stDecoration"],
    #MainMenu { display: none !important; }
    footer { visibility: hidden !important; height: 0 !important; }

    /* ── Tight layout ── */
    .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    [data-testid="stHorizontalBlock"] { gap: 0.4rem !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { padding: 0.4rem !important; }

    /* ── Inventory images ── */
    [data-testid="stDataFrame"] td img,
    [data-testid="stDataFrame"] [role="gridcell"] img {
        width: 240px !important; height: 240px !important;
        max-width: 240px !important; max-height: 240px !important;
        object-fit: contain !important; margin: 0 auto !important; display: block !important;
    }

    /* ── Table alignment ── */
    [data-testid="stDataEditor"] [role="gridcell"],
    [data-testid="stDataEditor"] [role="columnheader"] {
        text-align: center !important; justify-content: center !important;
    }
    [data-testid="stDataEditor"] .ag-header-cell-label { justify-content: center !important; }

    /* ── Add fabric button ── */
    .st-key-add_fabric_btn button { background-color: #28a745 !important; color: white !important; border-color: #28a745 !important; }
    .st-key-add_fabric_btn button:hover { background-color: #218838 !important; border-color: #1e7e34 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Google Sheets Connection ────────────────────────────────────────────
from utils import (
    init_connection,
    fetch_customers_from_cloud,
    fetch_orders_from_cloud,
    fetch_inventory_from_cloud,
    fetch_patterns_from_cloud,
    fetch_finance_from_cloud,
)

try:
    client = init_connection()
    spreadsheet = client.open("SwimwearDB")
    # Make spreadsheet accessible to utils fetch functions via session_state
    st.session_state._spreadsheet = spreadsheet
except Exception as e:
    st.error(f"שגיאה בהתחברות לגוגל שיטס: {e}")
    st.stop()

# ── Data Loading (once per session) ────────────────────────────────────
if "data_loaded" not in st.session_state or not st.session_state.data_loaded:
    with st.spinner("טוענת נתונים מהענן..."):
        st.session_state.customers_df, st.session_state.customers_sheet = fetch_customers_from_cloud(spreadsheet)
        st.session_state.orders_df,    st.session_state.orders_sheet    = fetch_orders_from_cloud(spreadsheet)
        st.session_state.inventory_df, st.session_state.inventory_sheet = fetch_inventory_from_cloud(spreadsheet)
        st.session_state.patterns_df,  st.session_state.patterns_sheet  = fetch_patterns_from_cloud(spreadsheet)
        st.session_state.finance_data, st.session_state.finance_sheet   = fetch_finance_from_cloud(spreadsheet)
        st.session_state.data_loaded = True

# ── Session State Defaults ──────────────────────────────────────────────
if "current_view"          not in st.session_state: st.session_state.current_view          = "ראשי"
if "delete_mode"           not in st.session_state: st.session_state.delete_mode           = False
if "delete_mode_orders"    not in st.session_state: st.session_state.delete_mode_orders    = False
if "delete_mode_inventory" not in st.session_state: st.session_state.delete_mode_inventory = False
if "delete_mode_patterns"  not in st.session_state: st.session_state.delete_mode_patterns  = False
if "selected_customer_phone" not in st.session_state: st.session_state.selected_customer_phone = None

# ── Navbar ──────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1, 1, 1.4])

# Active nav button highlight
_view_nav_map = {
    "ראשי": "nav_home", "מלאי": "nav_inv", "גזרות": "nav_pat", "פיננסי": "nav_fin",
    "לקוחות": "nav_cust", "כרטיס_לקוחה": "nav_cust", "הזמנות": "nav_ord",
}
_ank = _view_nav_map.get(st.session_state.current_view, "nav_home")
st.markdown(
    f"""<style>.st-key-{_ank} button {{
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important; border-color: #6366f1 !important;
    box-shadow: 0 3px 12px rgba(99,102,241,0.45) !important;
    font-weight: 700 !important; transform: translateY(-1px);
}}</style>""",
    unsafe_allow_html=True,
)

with col1:
    if st.button("🏠 ראשי",    use_container_width=True, key="nav_home"):  st.session_state.current_view = "ראשי";    st.rerun()
with col2:
    if st.button("📦 הזמנות", use_container_width=True, key="nav_ord"):   st.session_state.current_view = "הזמנות";  st.rerun()
with col3:
    if st.button("👥 לקוחות", use_container_width=True, key="nav_cust"):  st.session_state.current_view = "לקוחות";  st.rerun()
with col4:
    if st.button("💰 פיננסי", use_container_width=True, key="nav_fin"):   st.session_state.current_view = "פיננסי";  st.rerun()
with col5:
    if st.button("✂️ גזרות",  use_container_width=True, key="nav_pat"):   st.session_state.current_view = "גזרות";   st.rerun()
with col6:
    if st.button("🧵 מלאי",   use_container_width=True, key="nav_inv"):   st.session_state.current_view = "מלאי";    st.rerun()
with col7:
    if st.button("🔄 רענון נתונים", use_container_width=True, key="nav_refresh"):
        st.session_state.data_loaded = False; st.rerun()

st.markdown('<hr style="margin: 0.3rem 0 0.5rem 0; border-color: #e5e7eb;">', unsafe_allow_html=True)

# ── View Routing ────────────────────────────────────────────────────────
view = st.session_state.current_view

if view == "ראשי":
    from views.dashboard import render_dashboard
    render_dashboard()

elif view == "מלאי":
    from views.inventory import render_inventory
    render_inventory()

elif view == "גזרות":
    from views.patterns import render_patterns
    render_patterns()

elif view == "הזמנות":
    from views.orders import render_orders
    render_orders()

elif view == "לקוחות":
    from views.customers import render_customers
    render_customers()

elif view == "כרטיס_לקוחה":
    from views.customers import render_customer_card
    render_customer_card()

elif view == "פיננסי":
    from views.financial import render_financial
    render_financial()
