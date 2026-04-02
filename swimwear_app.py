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
import plotly.express as px

# הגדרות עמוד בסיסיות
st.set_page_config(page_title="Kalimi Manager", page_icon="👙", layout="wide")

# --- הגדרת תמיכה מלאה בעברית (RTL) ועיצובים מיוחדים ---
st.markdown(
    """
    <style>
    .stApp { direction: rtl; }
    p, div, input, label, h1, h2, h3, h4, h5, h6 { text-align: right !important; }
    div[data-testid="stAlert"] > div { direction: rtl; text-align: right; }
    
    /* תמונות במלאי — גודל תצוגה מוגדל */
    [data-testid="stDataFrame"] td img,
    [data-testid="stDataFrame"] [role="gridcell"] img {
        width: 240px !important;
        height: 240px !important;
        max-width: 240px !important;
        max-height: 240px !important;
        object-fit: contain !important;
        margin: 0 auto !important;
        display: block !important;
    }
    
    /* יישור מרכזי לכל תאי הטבלה (data editor) */
    [data-testid="stDataEditor"] [role="gridcell"],
    [data-testid="stDataEditor"] [role="columnheader"] {
        text-align: center !important;
        justify-content: center !important;
    }
    [data-testid="stDataEditor"] .ag-header-cell-label {
        justify-content: center !important;
    }

    /* עיצוב ייעודי לכפתור "הוסיפי למלאי" כדי שיהיה ירוק */
    .st-key-add_fabric_btn button {
        background-color: #28a745 !important;
        color: white !important;
        border-color: #28a745 !important;
    }
    .st-key-add_fabric_btn button:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# גודל ממוזער לשמירה ב-Sheets ובתצוגה בטבלת המלאי כפול מבעבר לקבלת איכות גבוהה יותר
INVENTORY_IMAGE_THUMB = (240, 240)

# --- פונקציית עיבוד תמונות לענן ---
def process_image(uploaded_file, max_size=INVENTORY_IMAGE_THUMB):
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            # חיתוך תמונה לריבוע מדויק כדי שלא ייווצר שטח ריק בעמודת הטבלה
            img = ImageOps.fit(img, max_size)
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            st.error(f"שגיאה בעיבוד התמונה: {e}")
            return ""
    return ""

# --- מנגנון התחברות לגוגל שיטס ---
@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("google_credentials.json", scopes=scopes)
    return gspread.authorize(creds)

try:
    client = init_connection()
    spreadsheet = client.open("SwimwearDB") 
except Exception as e:
    st.error(f"שגיאה בהתחברות לגוגל שיטס: {e}")
    st.stop()

# --- פונקציות עזר לשליפת נתונים מהענן ---
def fetch_customers_from_cloud():
    try:
        sheet = spreadsheet.worksheet("Customers")
        df = pd.DataFrame(sheet.get_all_records())
        if not df.empty and "Phone Number" in df.columns:
            df["Phone Number"] = df["Phone Number"].astype(str).apply(lambda x: '0' + x if len(x) == 9 and not x.startswith('0') else x)
        else:
            df = pd.DataFrame(columns=["Phone Number", "First Name", "Last Name", "Address", "Notes"])
        return df, sheet
    except:
        return pd.DataFrame(columns=["Phone Number", "First Name", "Last Name", "Address", "Notes"]), None

def fetch_orders_from_cloud():
    try:
        sheet = spreadsheet.worksheet("Orders")
        df = pd.DataFrame(sheet.get_all_records())
        if not df.empty and "Phone Number" in df.columns:
            df["Phone Number"] = df["Phone Number"].astype(str).apply(lambda x: '0' + x if len(x) == 9 and not x.startswith('0') else x)
            for col in ["Payment Date", "Swimsuit Type", "Pattern", "Order Notes", "Fabric 2", "Fabric Usage 2"]:
                if col not in df.columns:
                    df[col] = ""
            
            # One-time migration for old Order IDs
            if df["Order ID"].astype(str).str.contains("ORD-").any():
                count = 1
                new_ids = []
                for val in df["Order ID"]:
                    new_ids.append(f"{count:04d}")
                    count += 1
                df["Order ID"] = new_ids
                sheet.clear()
                sheet.update([df.columns.values.tolist()] + df.values.tolist())
        else:
            df = pd.DataFrame(
                columns=[
                    "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                    "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                    "Swimsuit Type", "Pattern", "Order Notes",
                    "Status", "Payment Status", "Supply Type", "Price", "Payment Date"
                ]
            )
        return df, sheet
    except:
        return pd.DataFrame(
            columns=[
                "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                "Swimsuit Type", "Pattern", "Order Notes",
                "Status", "Payment Status", "Supply Type", "Price", "Payment Date"
            ]
        ), None

def fetch_inventory_from_cloud():
    try:
        sheet = spreadsheet.worksheet("Inventory")
        df = pd.DataFrame(sheet.get_all_records())
        if df.empty:
            df = pd.DataFrame(columns=["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"])
        else:
            if "Image URL" in df.columns:
                df["Image URL"] = df["Image URL"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
        return df, sheet
    except:
        return pd.DataFrame(columns=["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]), None


def fetch_patterns_from_cloud():
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


def fetch_finance_from_cloud():
    try:
        sheet = spreadsheet.worksheet("Finance")
        col_a_values = sheet.col_values(1)
        raw_value = "".join(col_a_values)
        if not raw_value.strip():
            return {"settings": {"currency": "₪"}, "month_settings": {}, "monthly_expenses": {}, "standing_orders": []}, sheet
        data = json.loads(raw_value)
        data.setdefault("settings", {"currency": "₪"})
        data.setdefault("month_settings", {})
        data.setdefault("monthly_expenses", {})
        data.setdefault("standing_orders", [])
        return data, sheet
    except:
        return {"settings": {"currency": "₪"}, "month_settings": {}, "monthly_expenses": {}, "standing_orders": []}, None

def _background_save_finance(data_snapshot: dict) -> None:
    try:
        sheet = spreadsheet.worksheet("Finance")
        json_string = json.dumps(data_snapshot, ensure_ascii=False)
        chunk_size = 40000
        chunks = [json_string[i:i + chunk_size] for i in range(0, len(json_string), chunk_size)]
        values_to_update = [[chunk] for chunk in chunks]
        sheet.clear()
        sheet.update(range_name=f"A1:A{len(chunks)}", values=values_to_update)
    except Exception as e:
        print(f"Background save finance failed: {e}")

def save_finance_data(data: dict) -> None:
    data_snapshot = copy.deepcopy(data)
    thread = threading.Thread(target=_background_save_finance, args=(data_snapshot,))
    thread.start()

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

# ==========================================
#        ניהול מצב מקומי (Local State)

# ==========================================
if "data_loaded" not in st.session_state or not st.session_state.data_loaded:
    with st.spinner("טוענת נתונים מהענן..."):
        st.session_state.customers_df, st.session_state.customers_sheet = fetch_customers_from_cloud()
        st.session_state.orders_df, st.session_state.orders_sheet = fetch_orders_from_cloud()
        st.session_state.inventory_df, st.session_state.inventory_sheet = fetch_inventory_from_cloud()
        st.session_state.patterns_df, st.session_state.patterns_sheet = fetch_patterns_from_cloud()
        st.session_state.finance_data, st.session_state.finance_sheet = fetch_finance_from_cloud()
        st.session_state.data_loaded = True

if "current_view" not in st.session_state: st.session_state.current_view = "הזמנות"
if "delete_mode" not in st.session_state: st.session_state.delete_mode = False
if "delete_mode_orders" not in st.session_state: st.session_state.delete_mode_orders = False
if "delete_mode_inventory" not in st.session_state: st.session_state.delete_mode_inventory = False
if "delete_mode_patterns" not in st.session_state: st.session_state.delete_mode_patterns = False
if "selected_customer_phone" not in st.session_state: st.session_state.selected_customer_phone = None

# משיכת הנתונים מהזיכרון המקומי
customers_df = st.session_state.customers_df
customers_sheet = st.session_state.customers_sheet
orders_df = st.session_state.orders_df
orders_sheet = st.session_state.orders_sheet
inventory_df = st.session_state.inventory_df
inventory_sheet = st.session_state.inventory_sheet
patterns_df = st.session_state.patterns_df
patterns_sheet = st.session_state.patterns_sheet
finance_data = st.session_state.finance_data
finance_sheet = st.session_state.finance_sheet

# --- פונקציית חישוב כמות זמינה במלאי ---
def get_calculated_inventory():
    inv_df = st.session_state.inventory_df.copy()
    if inv_df.empty: return inv_df

    inv_df["Initial Meters"] = pd.to_numeric(inv_df["Initial Meters"], errors='coerce').fillna(0)
    inv_df["כמות בארגז (מ')"] = inv_df["Initial Meters"]
    inv_df["כמות זמינה (מ')"] = inv_df["Initial Meters"]
    inv_df["_Delivered_Usage"] = 0.0

    return inv_df

# --- תפריט ניווט עליון (Navbar) ---
col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1.4])

with col1:
    st.markdown('<div style="margin-top: -15px;">', unsafe_allow_html=True)
    try:
        st.image("photos/logo.png", width=180) 
    except FileNotFoundError:
        st.markdown("<h3 style='margin-top: 10px; color: gold;'>👙 Kalimi</h3>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Active nav state CSS injection ---
_view_nav_map = {
    "מלאי": "nav_inv", "גזרות": "nav_pat", "פיננסי": "nav_fin",
    "לקוחות": "nav_cust", "כרטיס_לקוחה": "nav_cust", "הזמנות": "nav_ord"
}
_ank = _view_nav_map.get(st.session_state.get("current_view", "הזמנות"), "nav_ord")
st.markdown(
    f'''<style>.st-key-{_ank} button {{
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border-color: #6366f1 !important;
    box-shadow: 0 3px 12px rgba(99,102,241,0.45) !important;
    font-weight: 700 !important;
    transform: translateY(-1px);
}}</style>''',
    unsafe_allow_html=True
)

# סדר כפתורים מימין לשמאל: הזמנות | לקוחות | פיננסי | גזרות | מלאי | רענון נתונים
with col2:
    if st.button("📦 הזמנות", use_container_width=True, key="nav_ord"): st.session_state.current_view = "הזמנות"; st.rerun()
with col3:
    if st.button("👥 לקוחות", use_container_width=True, key="nav_cust"): st.session_state.current_view = "לקוחות"; st.rerun()
with col4:
    if st.button("💰 פיננסי", use_container_width=True, key="nav_fin"): st.session_state.current_view = "פיננסי"; st.rerun()
with col5:
    if st.button("✂️ גזרות", use_container_width=True, key="nav_pat"): st.session_state.current_view = "גזרות"; st.rerun()
with col6:
    if st.button("🧵 מלאי", use_container_width=True, key="nav_inv"): st.session_state.current_view = "מלאי"; st.rerun()
with col7:
    if st.button("🔄 רענון נתונים", use_container_width=True, key="nav_refresh"): st.session_state.data_loaded = False; st.rerun()

st.markdown("---")

# ==========================================
#               מסך המלאי
# ==========================================
if st.session_state.current_view == "מלאי":
    st.title("🧵 ניהול בדים ומלאי")
    
    if inventory_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Inventory' ב-Google Sheets. צרי אותו כדי להתחיל לשמור מלאי.")
    else:
        inv_display = get_calculated_inventory()
        
        # --- תצוגת מדדים (Metrics) בראש הדף ---
        if not inv_display.empty:
            total_fabrics = len(inv_display)
            total_box = pd.to_numeric(inv_display["כמות בארגז (מ')"], errors='coerce').fillna(0).sum()
            total_available = pd.to_numeric(inv_display["כמות זמינה (מ')"], errors='coerce').fillna(0).sum()
            
            # עיצוב מותאם למדדים
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("סוגי בדים במלאי", f"{total_fabrics}")
            with m2:
                st.metric("סה״כ מטרים בארגז", f"{total_box:g}")
            with m3:
                st.metric("סה״כ מטרים פנויים", f"{total_available:g}")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- חלוקה ללשוניות ---
        tab_list, tab_add = st.tabs(["📋 רשימת מלאי קיימת", "➕ הוספת בד חדש"])
        
        with tab_list:
            if not inv_display.empty:
                # --- סרגל חיפוש ---
                col_search, col_space = st.columns([1, 1])
                with col_search:
                    search_term = st.text_input("🔍 חיפוש קל (לפי שם או מק\"ט):", placeholder="הקלידי כאן...")
                
                # מוסיפים אינדקס מקורי כדי שנוכל לחבר עריכות ומחיקות בחזרה למסד הנתונים
                inv_display["_Original_Index"] = inv_display.index
                
                # סינון לפי חיפוש
                if search_term:
                    mask = (
                        inv_display["Fabric Name"].astype(str).str.contains(search_term, case=False, na=False) |
                        inv_display["Fabric ID"].astype(str).str.contains(search_term, case=False, na=False)
                    )
                    filtered_inv = inv_display[mask]
                else:
                    filtered_inv = inv_display
                
                if filtered_inv.empty:
                    st.info("לא נמצאו בדים התואמים לחיפוש שלך.")
                else:
                    # שינוי שמות עמודות בהתאם לבקשת המשתמש
                    df_view = filtered_inv.rename(columns={
                        "Fabric Name": "שם הבד/צבע",
                        "Fabric ID": "מק\"ט",
                        "Image URL": "תמונה"
                    })
                    
                    # סדר העמודות מתהפך כדי שבטבלה עצמה זה יופיע מימין לשמאל:
                    # הוספנו את "תמונה" משמאל ביותר שזה אומר שהיא הראשונה ברשימה (מימין במסך).
                    cols = ["תמונה", "כמות זמינה (מ')", "כמות בארגז (מ')", "מק\"ט", "שם הבד/צבע", "_Original_Index", "_Delivered_Usage"]
                    
                    if st.session_state.delete_mode_inventory:
                        df_view["בחרי למחיקה"] = False
                        cols = ["בחרי למחיקה"] + cols
                    
                    df_view = df_view[cols]
                    
                    # קונפיגורציית עמודות
                    config = {
                        "שם הבד/צבע": st.column_config.TextColumn("שם הבד/צבע (ניתן לערוך)"),
                        "מק\"ט": st.column_config.TextColumn("מק\"ט (ניתן לערוך)"),
                        "כמות בארגז (מ')": st.column_config.NumberColumn("כמות בארגז (מ')", format="%g"),
                        "כמות זמינה (מ')": st.column_config.NumberColumn("כמות זמינה (מ')", format="%g", disabled=True),
                        "תמונה": st.column_config.ImageColumn("תמונה"),
                        "_Original_Index": None,  # הסתרת עמודת אינדקס העזר
                        "_Delivered_Usage": None, # הסתרת עמודת שימוש מנמסרו
                    }
                    if st.session_state.delete_mode_inventory:
                        config["בחרי למחיקה"] = st.column_config.CheckboxColumn("למחיקה", default=False)
                    
                    st.caption("💡 טיפ: ניתן ללחוץ על הטקסטים במסך ולערוך את נתוני המלאי או המק\"ט תוך כדי תנועה!")
                    
                    # שימוש באפשרות ההרחבה לגובה שורות כדי לוודא תמונה גדולה (לפחות 100px)
                    edited_inv = st.data_editor(
                        df_view, 
                        use_container_width=True, 
                        hide_index=True, 
                        column_config=config,
                        # row_height קיים בגרסאות Streamlit חדשות כדי להריץ תמונה גדולה
                        **({"row_height": 120} if int(st.__version__.split(".")[1]) >= 43 or (int(st.__version__.split(".")[0]) >= 2) else {}),
                        key=f"inv_editor_{search_term}"
                    )
                    
                    # --- פעולות עריכה ומחיקה מרוכזות ---
                    col_space_action, col_btn_save, col_btn_select = st.columns([6, 2, 2])
                    
                    with col_btn_select:
                        if not st.session_state.delete_mode_inventory:
                            if st.button("מחיקת פריטים", key="sel_inv", use_container_width=True):
                                st.session_state.delete_mode_inventory = True; st.rerun()
                        else:
                            if st.button("בטלי מחיקה", key="canc_inv", use_container_width=True):
                                st.session_state.delete_mode_inventory = False; st.rerun()
                    
                    with col_btn_save:
                        if st.session_state.delete_mode_inventory:
                            inv_to_delete = edited_inv[edited_inv["בחרי למחיקה"] == True]
                            if not inv_to_delete.empty:
                                if st.button("אישור מחיקה 🗑️", type="primary", use_container_width=True):
                                    with st.spinner("מוחקת מהמלאי (מסתנכרן עם הענן)..."):
                                        ids_to_delete = inv_to_delete["מק\"ט"].tolist()
                                        st.session_state.inventory_df = inventory_df[~inventory_df["Fabric ID"].isin(ids_to_delete)]
                                        
                                        inventory_sheet.clear()
                                        if st.session_state.inventory_df.empty:
                                            inventory_sheet.update([["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]])
                                        else:
                                            inventory_sheet.update([st.session_state.inventory_df.columns.values.tolist()] + st.session_state.inventory_df.values.tolist())
                                        
                                        st.session_state.delete_mode_inventory = False
                                        st.success("הבדים שנבחרו נמחקו בהצלחה!"); st.rerun()
                        else:
                            if not edited_inv.equals(df_view):
                                if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                                    if edited_inv["מק\"ט"].duplicated().any():
                                        st.error("❌ שגיאה: יש כפילות במק\"ט! בדקי שוב.")
                                    elif edited_inv["שם הבד/צבע"].duplicated().any():
                                        st.error("❌ שגיאה: יש כפילות בשם הבד! אנא השתמשי בשמות ייחודיים.")
                                    else:
                                        with st.spinner("שומרת את המלאי המעודכן בענן..."):
                                            # חילוץ נתוני העריכה ומיזוגם בחזרה לטבלת המלאי בהתאם לאינדקס המקורי
                                            for _, row in edited_inv.iterrows():
                                                orig_idx = int(row["_Original_Index"])
                                                st.session_state.inventory_df.at[orig_idx, "Fabric ID"] = str(row["מק\"ט"]).strip()
                                                st.session_state.inventory_df.at[orig_idx, "Fabric Name"] = str(row["שם הבד/צבע"]).strip()
                                                # reverse calculation: Total Purchased (Initial) = Box (user edited) + Delivered
                                                st.session_state.inventory_df.at[orig_idx, "Initial Meters"] = float(row["כמות בארגז (מ')"]) + float(row.get("_Delivered_Usage", 0))
                                            
                                            save_df = st.session_state.inventory_df[["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]]
                                            save_df["Image URL"] = save_df["Image URL"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
                                            
                                            inventory_sheet.clear()
                                            inventory_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())
                                            st.success("המלאי עודכן בהצלחה!"); st.rerun()
            else:
                st.info("עדיין אין בדים במערכת. עברי ללשונית 'הוספת בד חדש' כדי להתחיל!")
        
        with tab_add:
            st.markdown("### הוספת בד חדש לאוסף")
            st.caption("הוסיפי בד חדש עם הפרטים שלו וצילום. הוא יתווסף אוטומטית למאגר הבדים באפליקציה.")
            
            # החלפנו את st.form בניהול session_state כדי לפתור באגים במנגנון העלאת התמונות של Streamlit
            if "fabric_form_key" not in st.session_state:
                st.session_state.fabric_form_key = 0
            
            f_key = st.session_state.fabric_form_key
            
            with st.container():
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    f_name = st.text_input("שם הבד / תיאור צבע*", key=f"fname_{f_key}")
                    f_meters = st.number_input("כמות התחלתית (מטרים)*", min_value=0.0, step=0.5, key=f"fmeters_{f_key}")
                with col_f2:
                    f_id = st.text_input("מק\"ט*", key=f"fid_{f_key}")
                    
                st.markdown("**תמונת הבד (אופציונלי אך מומלץ):**")
                img_method = st.radio(
                    "איך תרצי להוסיף תמונה?",
                    ["העלאת קובץ מהמחשב/טלפון", "הפעלת מצלמה (צילום כעת)"],
                    horizontal=True,
                    key=f"method_{f_key}"
                )
                
                if "העלאת קובץ" in img_method:
                    uploaded_file = st.file_uploader("בחרי תמונה מהמכשיר", type=["jpg", "jpeg", "png"], key=f"img_up_{f_key}")
                else:
                    uploaded_file = st.camera_input("הפעילי מצלמה וצלמי את הבד", key=f"img_cam_{f_key}")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✨ שמרי בד חדש באוסף", type="primary", use_container_width=True):
                    if not f_name or not f_id:
                        st.warning("חובה להזין את שם הבד ומק\"ט!")
                    elif f_id in st.session_state.inventory_df["Fabric ID"].values:
                        st.error("❌ שגיאה: המק\"ט כבר קיים במערכת! אנא בחרי מק\"ט ייחודי.")
                    elif f_name in st.session_state.inventory_df["Fabric Name"].values:
                        st.error("❌ שגיאה: שם הבד כבר קיים במערכת! אנא בחרי שם ייחודי.")
                    else:
                        with st.spinner("שומר בד באוסף..."):
                            # מעבדים את התמונה תמיד ברגע השמירה כדי למנוע את באג האיפוס
                            f_img_clean = process_image(uploaded_file) if uploaded_file else ""
                            
                            new_fabric = {
                                "Fabric ID": str(f_id).strip(),
                                "Fabric Name": str(f_name).strip(),
                                "Initial Meters": f_meters,
                                "Image URL": f_img_clean.strip(),
                            }
                            st.session_state.inventory_df = pd.concat(
                                [st.session_state.inventory_df, pd.DataFrame([new_fabric])], ignore_index=True
                            )
                            if inventory_sheet.get_all_records() == []:
                                inventory_sheet.append_row(["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"])
                            inventory_sheet.append_row(
                                [
                                    new_fabric["Fabric ID"],
                                    new_fabric["Fabric Name"],
                                    new_fabric["Initial Meters"],
                                    new_fabric["Image URL"],
                                ]
                            )
                            # מאתחלים את הטופס באמצעות העלאת המפתח
                            st.session_state.fabric_form_key += 1
                            st.success(f"הבד '{f_name}' התווסף למאגר בהצלחה!"); st.rerun()

# ==========================================
#               מסך הגזרות
# ==========================================
elif st.session_state.current_view == "גזרות":
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
                            st.success("הגזרות נמחקו בהצלחה!")
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
                        st.success("הגזרות עודכנו!")
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
                    st.success(f"הגזרה '{p_name_clean}' נוספה בהצלחה!")
                    st.rerun()

# ==========================================
#               מסך ההזמנות
# ==========================================
elif st.session_state.current_view == "הזמנות":
    st.title("📦 ניהול הזמנות")
    
    if orders_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Orders' ב-Google Sheets. אנא צרי אותו כדי להתחיל לשמור הזמנות.")
    else:
        st.markdown("---")
        
        st.subheader("➕ יצירת הזמנה חדשה")
        
        customer_options = ["✨ לקוחה חדשה..."]
        if not customers_df.empty:
            customer_options += [f"{r['First Name']} {r['Last Name']} ({r['Phone Number']})" for i, r in customers_df.iterrows()]
            
        selected_customer = st.selectbox("עבור איזו לקוחה ההזמנה?", customer_options)
        
        new_c_fname, new_c_lname, new_c_phone, new_c_address = "", "", "", ""
        if selected_customer == "✨ לקוחה חדשה...":
            st.info("📝 מלאי את פרטי הלקוחה החדשה. היא תתווסף אוטומטית למאגר הלקוחות שלך!")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                new_c_fname = st.text_input("שם פרטי (לקוחה חדשה)*")
                new_c_phone = st.text_input("מספר טלפון (לקוחה חדשה)*")
            with col_c2:
                new_c_lname = st.text_input("שם משפחה (לקוחה חדשה)")
                new_c_address = st.text_input("כתובת למשלוח (לקוחה חדשה)")
        
        with st.container():
            st.markdown("**פירוט ההזמנה והמלאי:**")
            swimsuit_type = st.radio("סוג בגד הים*", ["בגד ים שלם", "ביקיני"], horizontal=True)
            item_name = st.text_input("שם/תיאור הזמנה (אופציונלי)")

            st.markdown(
                '<div style="background:linear-gradient(135deg,#f8f9ff,#eef0ff);border-right:4px solid #6366f1;'
                'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">'
                '<span style="font-weight:700;color:#4338ca;font-size:15px;">📐 גזרה ומידות</span></div>',
                unsafe_allow_html=True)
            # --- שדות מידה/גזרה דינמיים לפי סוג ---
            top_size, bottom_size, custom_size, pattern_name = "", "", "", ""
            if swimsuit_type == "בגד ים שלם":
                custom_size = st.text_input("מידה / מידות*")
                one_piece_patterns = (
                    patterns_df[patterns_df["Category"].astype(str).str.strip() == "בגד ים שלם"]["Pattern Name"]
                    .astype(str)
                    .str.strip()
                    .tolist()
                    if not patterns_df.empty
                    else []
                )
                pattern_options = one_piece_patterns if one_piece_patterns else ["אין גזרות מתאימות"]
                pattern_name = st.selectbox("גזרה*", pattern_options)
            else:
                bikini_patterns = (
                    patterns_df[patterns_df["Category"].astype(str).str.strip() == "ביקיני"]["Pattern Name"]
                    .astype(str)
                    .str.strip()
                    .tolist()
                    if not patterns_df.empty
                    else []
                )
                bikini_pattern_options = bikini_patterns if bikini_patterns else ["אין גזרות מתאימות"]
                size_options = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "ללא (לא הוזמן)"]
                row_b1, row_b2, row_b3 = st.columns([1.3, 1, 1])
                with row_b1:
                    pattern_name = st.selectbox("גזרה*", bikini_pattern_options)
                with row_b2:
                    top_size = st.selectbox("מידת עליון*", size_options, index=2)
                with row_b3:
                    bottom_size = st.selectbox("מידת תחתון*", size_options, index=2)

            # --- בחירת בדים חזותית ---
            fabric_options = inventory_df["Fabric Name"].astype(str).tolist() if not inventory_df.empty else []
            image_by_fabric = {}
            sku_by_fabric = {}
            if not inventory_df.empty:
                for _, row in inventory_df.iterrows():
                    name = str(row.get("Fabric Name", "")).strip()
                    if name:
                        image_by_fabric[name] = str(row.get("Image URL", "") or "")
                        sku_by_fabric[name] = str(row.get("Fabric ID", "") or "")

            if "order_fabric_primary" not in st.session_state:
                st.session_state.order_fabric_primary = fabric_options[0] if fabric_options else ""
            if "order_fabric_secondary" not in st.session_state:
                st.session_state.order_fabric_secondary = ""
            if "open_fabric_dialog_for" not in st.session_state:
                st.session_state.open_fabric_dialog_for = ""

            @st.dialog("בחירת בד להזמנה")
            def pick_fabric_dialog(target_key: str, exclude_fabric: str = ""):
                available = [f for f in fabric_options if f != exclude_fabric]
                if not available:
                    st.info("אין בדים זמינים לבחירה.")
                    return

                st.caption("בחרי בד מתוך התמונות למטה:")
                cards_per_row = 4
                for start in range(0, len(available), cards_per_row):
                    row_items = available[start:start + cards_per_row]
                    row_cols = st.columns(cards_per_row)
                    for idx, fabric_name in enumerate(row_items):
                        with row_cols[idx]:
                            st.markdown(f"**{fabric_name}**")
                            fabric_img = image_by_fabric.get(fabric_name, "")
                            if fabric_img:
                                st.image(fabric_img, width=140)
                            else:
                                st.info("אין תמונה")
                            st.caption(f"מק\"ט: {sku_by_fabric.get(fabric_name, '-')}")
                            if st.button("בחרי", key=f"pick_{target_key}_{start}_{idx}_{fabric_name}"):
                                if target_key == "primary":
                                    st.session_state.order_fabric_primary = fabric_name
                                    if st.session_state.order_fabric_secondary == fabric_name:
                                        st.session_state.order_fabric_secondary = ""
                                else:
                                    st.session_state.order_fabric_secondary = fabric_name
                                st.session_state.open_fabric_dialog_for = ""
                                st.rerun()

            st.markdown(
                '<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-right:4px solid #22c55e;'
                'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">'
                '<span style="font-weight:700;color:#15803d;font-size:15px;">🧵 בחירת בדים</span></div>',
                unsafe_allow_html=True)
            st.markdown("### 🧵 בחירת בד ראשי")
            if fabric_options:
                if st.session_state.order_fabric_primary not in fabric_options:
                    st.session_state.order_fabric_primary = fabric_options[0]
                sel_fabric = st.session_state.order_fabric_primary
                if st.button("בחרי בד ראשי מהגלריה", key="open_primary_fabric_dialog"):
                    st.session_state.open_fabric_dialog_for = "primary"
                    st.rerun()
                if st.session_state.open_fabric_dialog_for == "primary":
                    pick_fabric_dialog("primary")
                selected_img = image_by_fabric.get(sel_fabric, "")
                if selected_img:
                    c_img, c_meta = st.columns([1, 2])
                    with c_img:
                        st.image(selected_img, width=180)
                    with c_meta:
                        st.markdown(f"**{sel_fabric}**")
                        st.caption(f"מק\"ט: {sku_by_fabric.get(sel_fabric, '-')}")
                fabric_usage = st.number_input("כמות בד נדרשת לבד הראשי (מ')*", min_value=0.0, step=0.1)
            else:
                sel_fabric = ""
                fabric_usage = 0.0
                st.info("אין בדים במלאי כרגע.")

            add_second_fabric = st.checkbox("הוסיפי בד נוסף להזמנה")
            sel_fabric_2 = ""
            fabric_usage_2 = 0.0
            if add_second_fabric:
                st.markdown("### 🧵 בחירת בד נוסף")
                secondary_options = [f for f in fabric_options if f != sel_fabric] if sel_fabric else fabric_options
                if secondary_options:
                    if st.session_state.order_fabric_secondary not in secondary_options:
                        st.session_state.order_fabric_secondary = secondary_options[0]
                    sel_fabric_2 = st.session_state.order_fabric_secondary
                    if st.button("בחרי בד נוסף מהגלריה", key="open_secondary_fabric_dialog"):
                        st.session_state.open_fabric_dialog_for = "secondary"
                        st.rerun()
                    if st.session_state.open_fabric_dialog_for == "secondary":
                        pick_fabric_dialog("secondary", exclude_fabric=sel_fabric)
                    selected_img_2 = image_by_fabric.get(sel_fabric_2, "")
                    if selected_img_2:
                        c2_img, c2_meta = st.columns([1, 2])
                        with c2_img:
                            st.image(selected_img_2, width=180)
                        with c2_meta:
                            st.markdown(f"**{sel_fabric_2}**")
                            st.caption(f"מק\"ט: {sku_by_fabric.get(sel_fabric_2, '-')}")
                    fabric_usage_2 = st.number_input("כמות בד נדרשת לבד הנוסף (מ')*", min_value=0.0, step=0.1)
                else:
                    st.warning("לא נשארו בדים נוספים לבחירה.")

            st.markdown(
                '<div style="background:linear-gradient(135deg,#fffbeb,#fef9c3);border-right:4px solid #f59e0b;'
                'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">'
                '<span style="font-weight:700;color:#b45309;font-size:15px;">📅 תאריכים והערות</span></div>',
                unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1: form_order_date = st.date_input("תאריך הזמנה", value=datetime.today())
            with col_d2: form_delivery_date = st.date_input("תאריך אספקה מיועד", value=None)

            order_notes = st.text_area("הערות להזמנה")

            st.markdown(
                '<div style="background:linear-gradient(135deg,#fff0f3,#ffe4e6);border-right:4px solid #f43f5e;'
                'padding:8px 16px;border-radius:8px;margin:18px 0 10px 0;">'
                '<span style="font-weight:700;color:#be123c;font-size:15px;">💳 סטטוס ותשלום</span></div>',
                unsafe_allow_html=True)
            st.markdown("**סטטוס ותשלום:**")
            col_st1, col_st2, col_st3 = st.columns(3)
            with col_st1: status = st.selectbox("סטטוס הזמנה", ["🆕 התקבלה (ממתינה לייצור)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"])
            with col_st2: pay_status = st.selectbox("סטטוס תשלום", ["🔴 טרם שולם", "🟡 שולמה מקדמה", "🟢 שולם במלואו"])
            with col_st3: supply = st.selectbox("סוג אספקה", ["איסוף עצמי", "משלוח"])

            price = st.number_input("מחיר סופי סך הכל (₪)", min_value=0, value=0, step=10)

            st.markdown("---")
            bypass_inventory = st.checkbox("התעלמי מהמלאי (שמירת הזמנה ללא חסימה גם אם הבד חסר)")

            if st.button("💾 שמרי הזמנה במערכת", type="primary", key="save_new_order_btn"):
                if swimsuit_type == "בגד ים שלם":
                    if not custom_size:
                        st.warning("חובה להזין מידה / מידות לבגד ים שלם."); st.stop()
                    if pattern_name == "אין גזרות מתאימות":
                        st.error("אין כרגע גזרות מסוג בגד ים שלם. הוסיפי גזרה בלשונית גזרות."); st.stop()
                    final_item = item_name.strip() if str(item_name).strip() else "One-piece"
                else:
                    if pattern_name == "אין גזרות מתאימות":
                        st.error("אין כרגע גזרות מסוג ביקיני. הוסיפי גזרה בלשונית גזרות."); st.stop()
                    top_not_ordered = top_size == "ללא (לא הוזמן)"
                    bottom_not_ordered = bottom_size == "ללא (לא הוזמן)"
                    if top_not_ordered and bottom_not_ordered:
                        st.error("יש לבחור לפחות חלק אחד בביקיני (עליון, תחתון או שניהם)."); st.stop()
                    if top_not_ordered:
                        bikini_desc = "Bikini - Bottom Only"
                    elif bottom_not_ordered:
                        bikini_desc = "Bikini - Top Only"
                    else:
                        bikini_desc = "Bikini - Full Set"
                    final_item = bikini_desc if not str(item_name).strip() else f"{bikini_desc} | {str(item_name).strip()}"

                if not fabric_options:
                    st.error("אין בדים זמינים במלאי לבחירה."); st.stop()
                if not sel_fabric:
                    st.error("חובה לבחור בד ראשי."); st.stop()
                if fabric_usage <= 0:
                    st.error("חובה להזין כמות בד גדולה מ-0 לבד הראשי."); st.stop()
                if add_second_fabric and (not sel_fabric_2 or fabric_usage_2 <= 0):
                    st.error("כשמוסיפים בד נוסף יש לבחור בד ולהזין כמות גדולה מ-0."); st.stop()

                usage_map = {sel_fabric: float(fabric_usage)}
                if add_second_fabric and sel_fabric_2:
                    usage_map[sel_fabric_2] = usage_map.get(sel_fabric_2, 0.0) + float(fabric_usage_2)

                if not bypass_inventory:
                    inv_current = st.session_state.inventory_df.copy()
                    inv_current["Initial Meters"] = pd.to_numeric(inv_current["Initial Meters"], errors="coerce").fillna(0.0)
                    for fab_name, req_m in usage_map.items():
                        row = inv_current[inv_current["Fabric Name"] == fab_name]
                        if row.empty:
                            st.error(f"הבד '{fab_name}' לא נמצא במלאי."); st.stop()
                        available = float(row.iloc[0]["Initial Meters"])
                        if req_m > available:
                            st.error(f"❌ הבד '{fab_name}' חסר במלאי! כמות זמינה: {available:.2f} מ', נדרש: {req_m:.2f} מ'."); st.stop()

                if selected_customer == "✨ לקוחה חדשה...":
                    if not new_c_fname or not new_c_phone:
                        st.warning("חובה להזין שם וטלפון ללקוחה החדשה!"); st.stop()
                    customer_phone = new_c_phone
                    customer_name = f"{new_c_fname} {new_c_lname}".strip()
                    
                    new_cust_row = pd.DataFrame([{"Phone Number": new_c_phone, "First Name": new_c_fname, "Last Name": new_c_lname, "Address": new_c_address, "Notes": "נוצרה דרך מסך הזמנות"}])
                    st.session_state.customers_df = pd.concat([st.session_state.customers_df, new_cust_row], ignore_index=True)
                    if customers_sheet: customers_sheet.append_row([new_c_phone, new_c_fname, new_c_lname, new_c_address, "נוצרה דרך מסך הזמנות"])
                else:
                    customer_phone = selected_customer.split("(")[-1].replace(")", "")
                    customer_name = selected_customer.split("(")[0].strip()

                def get_next_order_id(df):
                    if df.empty: return "0001"
                    valid_ids = pd.to_numeric(df["Order ID"], errors='coerce')
                    max_id = valid_ids.max()
                    if pd.isna(max_id): return "0001"
                    return f"{int(max_id) + 1:04d}"
                order_id = get_next_order_id(st.session_state.orders_df)
                order_date_str = form_order_date.strftime("%d/%m/%Y") if form_order_date else ""
                delivery_date_str = form_delivery_date.strftime("%d/%m/%Y") if form_delivery_date else ""
                pay_status_emoji = pay_status.split(" ")[0]
                
                order_row_dict = {
                    "Order ID": order_id, "Order Date": order_date_str, "Delivery Date": delivery_date_str, 
                    "Phone Number": customer_phone, "Customer Name": customer_name, "Item": final_item, 
                    "Top Size": top_size, "Bottom Size": bottom_size, "Custom Size": custom_size, 
                    "Fabric": sel_fabric, "Fabric Usage": float(fabric_usage),
                    "Fabric 2": sel_fabric_2 if add_second_fabric else "",
                    "Fabric Usage 2": float(fabric_usage_2) if add_second_fabric else 0.0,
                    "Swimsuit Type": swimsuit_type,
                    "Pattern": pattern_name,
                    "Order Notes": order_notes,
                    "Status": status, "Payment Status": pay_status_emoji, 
                    "Supply Type": supply, "Price": price, "Payment Date": ""
                }
                
                new_order_df = pd.DataFrame([order_row_dict])
                st.session_state.orders_df = pd.concat([st.session_state.orders_df, new_order_df], ignore_index=True)

                # ניכוי צריכת בד בפועל מהמלאי המקומי ומהענן לכל הבדים שנבחרו
                updated_inventory = st.session_state.inventory_df.copy()
                updated_inventory["Initial Meters"] = pd.to_numeric(updated_inventory["Initial Meters"], errors="coerce").fillna(0.0)
                for fab_name, req_m in usage_map.items():
                    mask = updated_inventory["Fabric Name"] == fab_name
                    if mask.any():
                        updated_inventory.loc[mask, "Initial Meters"] = updated_inventory.loc[mask, "Initial Meters"] - req_m
                st.session_state.inventory_df = updated_inventory
                
                if orders_sheet:
                    if len(st.session_state.orders_df) == 1: 
                        orders_sheet.append_row([
                            "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                            "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                            "Swimsuit Type", "Pattern", "Order Notes", "Status", "Payment Status", "Supply Type", "Price", "Payment Date"
                        ])
                    orders_sheet.append_row([
                        order_row_dict["Order ID"], order_row_dict["Order Date"], order_row_dict["Delivery Date"],
                        order_row_dict["Phone Number"], order_row_dict["Customer Name"], order_row_dict["Item"],
                        order_row_dict["Top Size"], order_row_dict["Bottom Size"], order_row_dict["Custom Size"],
                        order_row_dict["Fabric"], order_row_dict["Fabric Usage"], order_row_dict["Fabric 2"], order_row_dict["Fabric Usage 2"],
                        order_row_dict["Swimsuit Type"], order_row_dict["Pattern"], order_row_dict["Order Notes"],
                        order_row_dict["Status"], order_row_dict["Payment Status"], order_row_dict["Supply Type"],
                        order_row_dict["Price"], order_row_dict["Payment Date"]
                    ])

                if inventory_sheet is not None:
                    inv_save_df = st.session_state.inventory_df[["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]].copy()
                    inv_save_df["Image URL"] = inv_save_df["Image URL"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
                    inventory_sheet.clear()
                    if inv_save_df.empty:
                        inventory_sheet.update([["Fabric ID", "Fabric Name", "Initial Meters", "Image URL"]])
                    else:
                        inventory_sheet.update([inv_save_df.columns.values.tolist()] + inv_save_df.values.tolist())
                
                st.success(f"הזמנה {order_id} נוצרה ונשמרה בהצלחה!"); st.rerun()
        st.markdown("---")

        if not orders_df.empty:
            display_orders = orders_df.copy()
            
            st.markdown("### 🔍 חיפוש וסינון הזמנות")
            col_search1, col_search2 = st.columns([2, 1])
            with col_search1:
                search_query = st.text_input("חיפוש חופשי (שם לקוחה, מס' הזמנה, פריט, טלפון):", "")
            with col_search2:
                search_scope = st.radio("היכן לחפש?", ["גם וגם", "הזמנות פעילות", "הזמנות שהושלמו"], horizontal=True)

            if search_query:
                mask = (
                    display_orders["Customer Name"].astype(str).str.contains(search_query, na=False) |
                    display_orders["Order ID"].astype(str).str.contains(search_query, na=False) |
                    display_orders["Item"].astype(str).str.contains(search_query, na=False) |
                    display_orders["Phone Number"].astype(str).str.contains(search_query, na=False)
                )
                display_orders = display_orders[mask]
            
            if "Order Date" in display_orders.columns:
                display_orders["Order Date"] = pd.to_datetime(display_orders["Order Date"], format="%d/%m/%Y", errors="coerce").dt.date
            if "Delivery Date" in display_orders.columns:
                display_orders["Delivery Date"] = pd.to_datetime(display_orders["Delivery Date"], format="%d/%m/%Y", errors="coerce").dt.date
            
            display_orders = display_orders.rename(columns={
                "Order ID": "מספר הזמנה", "Order Date": "תאריך הזמנה", "Delivery Date": "תאריך אספקה",
                "Customer Name": "שם לקוחה", "Item": "פריט", "Status": "סטטוס", "Payment Status": "סטטוס תשלום",
                "Top Size": "עליון", "Bottom Size": "תחתון", "Custom Size": "התאמות", "Fabric Usage": "צריכת בד (מ')"
            })
            
            # צמצום עמודות כדי למנוע גלילה אופקית, הצגת המידע החשוב בלבד בראייה רחבה
            if "מספר הזמנה" in display_orders.columns:
                display_orders = display_orders.sort_values(by="מספר הזמנה", key=lambda x: pd.to_numeric(x, errors="coerce"), ascending=False)
            cols = ["מחיר", "סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "תאריך הזמנה", "פריט", "שם לקוחה"]
            cols = [c for c in cols if c in display_orders.columns]
            
            if st.session_state.delete_mode_orders:
                display_orders["בחרי"] = False
                cols = ["בחרי"] + cols

            display_orders = display_orders[cols]
            
            config = {
                "מספר הזמנה": st.column_config.TextColumn("מספר הזמנה", disabled=True, width="small"),
                "שם לקוחה": st.column_config.TextColumn("שם לקוחה", disabled=True),
                "פריט": st.column_config.TextColumn("פריט"),
                "תאריך הזמנה": st.column_config.DateColumn("תאריך הזמנה", format="DD/MM/YYYY", width="small"),
                "תאריך אספקה": st.column_config.DateColumn("תאריך אספקה", format="DD/MM/YYYY"),
                "התאמות": st.column_config.TextColumn("התאמות"),
                "סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה לייצור)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"]),
                "סטטוס תשלום": st.column_config.SelectboxColumn("תשלום", options=["🔴", "🟡", "🟢"], width="small"),
                "מחיר": st.column_config.NumberColumn("מחיר", format="₪%d", width="small"),
                "עליון": st.column_config.TextColumn("עליון"),
                "תחתון": st.column_config.TextColumn("תחתון")
            }
            if st.session_state.delete_mode_orders:
                config["בחרי"] = st.column_config.CheckboxColumn("בחרי", default=False)

            active_mask = display_orders["סטטוס"] != "✅ נמסרה ללקוחה"
            active_orders = display_orders[active_mask].copy()
            completed_orders = display_orders[~active_mask].copy()

            edited_active = active_orders
            edited_completed = completed_orders

            if search_scope in ["גם וגם", "הזמנות פעילות"]:
                st.markdown("### 📋 הזמנות פעילות")
                if not active_orders.empty:
                    edited_active = st.data_editor(active_orders, key="active_orders_editor", use_container_width=True, hide_index=True, column_config=config)
                else:
                    st.info("אין הזמנות פעילות שתואמות לחיפוש.")

            if search_scope in ["גם וגם", "הזמנות שהושלמו"]:
                st.markdown("### ✅ הזמנות שהושלמו (נמסרו)")
                if not completed_orders.empty:
                    edited_completed = st.data_editor(completed_orders, key="completed_orders_editor", use_container_width=True, hide_index=True, column_config=config)
                else:
                    st.info("אין הזמנות שהושלמו שתואמות לחיפוש.")

            col_space, col_btn_save, col_btn_select = st.columns([6, 2, 2])
            
            with col_btn_select:
                if not st.session_state.delete_mode_orders:
                    if st.button("בחרי", key="sel_ord", use_container_width=True):
                        st.session_state.delete_mode_orders = True; st.rerun()
                else:
                    if st.button("בטלי", key="canc_ord", use_container_width=True):
                        st.session_state.delete_mode_orders = False; st.rerun()
                        
            with col_btn_save:
                if st.session_state.delete_mode_orders:
                    orders_to_delete = pd.concat([
                        edited_active[edited_active["בחרי"] == True] if not edited_active.empty else pd.DataFrame(),
                        edited_completed[edited_completed["בחרי"] == True] if not edited_completed.empty else pd.DataFrame()
                    ])
                    if not orders_to_delete.empty:
                        if st.button("מחקי מסומנות 🗑️", type="primary", use_container_width=True):
                            with st.spinner("מעדכן מסד נתונים..."):
                                ids_to_delete = orders_to_delete["מספר הזמנה"].tolist()
                                st.session_state.orders_df = orders_df[~orders_df["Order ID"].isin(ids_to_delete)]
                                
                                orders_sheet.clear()
                                if st.session_state.orders_df.empty:
                                    orders_sheet.update([[
                                        "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                                        "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                                        "Swimsuit Type", "Pattern", "Order Notes",
                                        "Status", "Payment Status", "Supply Type", "Price", "Payment Date"
                                    ]])
                                else:
                                    orders_sheet.update([st.session_state.orders_df.columns.values.tolist()] + st.session_state.orders_df.values.tolist())
                                
                                st.session_state.delete_mode_orders = False
                                st.success("ההזמנות נמחקו!"); st.rerun()
                else:
                    has_changes = not edited_active.equals(active_orders) or not edited_completed.equals(completed_orders)
                    if has_changes:
                        if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                            with st.spinner("מעדכן שינויים..."):
                                save_orders = pd.concat([edited_active, edited_completed])
                                save_orders["תאריך הזמנה"] = save_orders["תאריך הזמנה"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
                                save_orders["תאריך אספקה"] = save_orders["תאריך אספקה"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
                                
                                save_orders = save_orders.rename(columns={
                                    "מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "שם לקוחה": "Customer Name", "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage"
                                })
                                
                                orders_indexed = orders_df.set_index("Order ID")
                                save_indexed = save_orders.set_index("Order ID")
                                
                                # Dynamic Payment Date calculation
                                if "Payment Date" not in orders_indexed.columns:
                                    orders_indexed["Payment Date"] = ""
                                if "Payment Date" not in save_indexed.columns:
                                    save_indexed["Payment Date"] = ""
                                
                                today_str = datetime.now().strftime("%d/%m/%Y")
                                for order_id, row in save_indexed.iterrows():
                                    if row["Payment Status"] == "🟢":
                                        old_status = orders_indexed.loc[order_id, "Payment Status"] if order_id in orders_indexed.index else ""
                                        old_date = orders_indexed.loc[order_id, "Payment Date"] if order_id in orders_indexed.index else ""
                                        
                                        if old_status != "🟢" or pd.isna(old_date) or str(old_date).strip() == "":
                                            save_indexed.at[order_id, "Payment Date"] = today_str
                                        else:
                                            save_indexed.at[order_id, "Payment Date"] = old_date
                                    else:
                                        save_indexed.at[order_id, "Payment Date"] = ""
                                
                                orders_indexed.update(save_indexed)
                                orders_indexed.reset_index(inplace=True)
                                
                                for col in ["Payment Date", "Swimsuit Type", "Pattern", "Order Notes", "Fabric 2", "Fabric Usage 2"]:
                                    if col not in orders_indexed.columns:
                                        orders_indexed[col] = ""
                                final_save = orders_indexed[[
                                    "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                                    "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                                    "Swimsuit Type", "Pattern", "Order Notes",
                                    "Status", "Payment Status", "Supply Type", "Price", "Payment Date"
                                ]]
                                
                                st.session_state.orders_df = final_save
                                orders_sheet.clear()
                                orders_sheet.update([final_save.columns.values.tolist()] + final_save.values.tolist())
                                st.success("נשמר בהצלחה!"); st.rerun()

        else:
            st.info("עדיין אין הזמנות במערכת. הוסיפי את ההזמנה הראשונה למטה!")
        

# ==========================================
#               מסך הלקוחות
# ==========================================
elif st.session_state.current_view == "לקוחות":
    st.title("👥 ניהול לקוחות")
    
    if not customers_df.empty:
        if "Notes" not in customers_df.columns:
            customers_df["Notes"] = ""

        df_display = customers_df.rename(columns={
            "First Name": "שם פרטי", "Last Name": "שם משפחה", "Phone Number": "מספר טלפון", "Address": "כתובת", "Notes": "הערות"
        })
        
        st.markdown("### 📇 כרטיס לקוחה")
        customer_options = ["בחרי לקוחה..."] + [f"{row['שם פרטי']} {row['שם משפחה']} ({row['מספר טלפון']})" for index, row in df_display.iterrows()]
        selected_option = st.selectbox("בחרי לקוחה להצגת כרטיס אישי והיסטוריית רכישות:", customer_options)
        
        if selected_option != "בחרי לקוחה...":
            phone_extracted = selected_option.split("(")[-1].replace(")", "")
            st.session_state.selected_customer_phone = phone_extracted
            st.session_state.current_view = "כרטיס_לקוחה"
            st.rerun()

        st.markdown("---")
        st.markdown("### 📋 רשימת הלקוחות")
        search_query = st.text_input("🔍 חפשי לקוחה (לפי שם, משפחה או טלפון):", "")

        if search_query:
            mask = (df_display["שם פרטי"].astype(str).str.contains(search_query, na=False) |
                    df_display["שם משפחה"].astype(str).str.contains(search_query, na=False) |
                    df_display["מספר טלפון"].astype(str).str.contains(search_query, na=False))
            filtered_df = df_display[mask].copy()
        else:
            filtered_df = df_display.copy()

        cols = ["הערות", "כתובת", "מספר טלפון", "שם משפחה", "שם פרטי"]
        
        if st.session_state.delete_mode:
            filtered_df["בחרי"] = False
            cols = ["בחרי"] + cols

        filtered_df = filtered_df[cols]
        
        column_config = {
            "מספר טלפון": st.column_config.TextColumn("מספר טלפון"),
            "שם פרטי": st.column_config.TextColumn("שם פרטי", width="medium"),
            "כתובת": st.column_config.TextColumn("כתובת", width="medium"),
            "הערות": st.column_config.TextColumn("הערות", width="large")
        }
        if st.session_state.delete_mode:
            column_config["בחרי"] = st.column_config.CheckboxColumn("בחרי", default=False)

        edited_df = st.data_editor(filtered_df, use_container_width=True, hide_index=True, column_config=column_config)

        col_space, col_btn_save, col_btn_select = st.columns([6, 2, 2])
        
        with col_btn_select: 
            if not st.session_state.delete_mode:
                if st.button("בחרי", use_container_width=True):
                    st.session_state.delete_mode = True; st.rerun()
            else:
                if st.button("בטלי", use_container_width=True):
                    st.session_state.delete_mode = False; st.rerun()
        
        with col_btn_save: 
            if st.session_state.delete_mode:
                customers_to_delete = edited_df[edited_df["בחרי"] == True]
                if not customers_to_delete.empty:
                    if st.button("מחקי מסומנות 🗑️", type="primary", use_container_width=True):
                        with st.spinner("מוחק..."):
                            phones_to_delete = customers_to_delete["מספר טלפון"].tolist()
                            st.session_state.customers_df = customers_df[~customers_df["Phone Number"].isin(phones_to_delete)]
                            
                            save_df = st.session_state.customers_df[["Phone Number", "First Name", "Last Name", "Address", "Notes"]]
                            customers_sheet.clear()
                            if save_df.empty: customers_sheet.update([save_df.columns.values.tolist()])
                            else: customers_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())
                            
                            st.session_state.delete_mode = False; st.success("נמחק!"); st.rerun()
            else:
                if not edited_df.equals(filtered_df):
                    if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                        with st.spinner("שומר מהר..."):
                            full_updated_df = df_display.copy()
                            full_updated_df.update(edited_df)

                            save_df = full_updated_df.rename(columns={
                                "שם פרטי": "First Name", "שם משפחה": "Last Name", "מספר טלפון": "Phone Number", "כתובת": "Address", "הערות": "Notes"
                            })
                            save_df = save_df[["Phone Number", "First Name", "Last Name", "Address", "Notes"]]
                            st.session_state.customers_df = save_df

                            customers_sheet.clear()
                            customers_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())
                            st.success("נשמר בהצלחה!"); st.rerun()
    else:
        st.info("עדיין אין לקוחות במערכת. הוסיפי את הלקוחה הראשונה למטה!")

    st.markdown("---")
    st.subheader("➕ הוספת לקוחה חדשה ישירות למאגר")
    with st.form("add_customer_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: 
            first_name = st.text_input("שם פרטי*")
            phone = st.text_input("מספר טלפון (מזהה ראשי)*")
        with c2: 
            last_name = st.text_input("שם משפחה")
            address = st.text_input("כתובת למשלוח")
            
        if st.form_submit_button("שמרי לקוחה במסד הנתונים"):
            if phone and first_name:
                new_cust = pd.DataFrame([{"Phone Number": phone, "First Name": first_name, "Last Name": last_name, "Address": address, "Notes": ""}])
                st.session_state.customers_df = pd.concat([st.session_state.customers_df, new_cust], ignore_index=True)
                customers_sheet.append_row([phone, first_name, last_name, address, ""])
                st.success(f"הלקוחה {first_name} {last_name} נוספה בהצלחה!"); st.rerun()
            else:
                st.warning("חובה להזין מספר טלפון ושם פרטי.")

# ==========================================
#               כרטיס לקוחה אישי
# ==========================================
elif st.session_state.current_view == "כרטיס_לקוחה":
    if st.button("🔙 חזרה לרשימת הלקוחות"):
        st.session_state.current_view = "לקוחות"
        st.session_state.selected_customer_phone = None
        st.rerun()
        
    if not customers_df.empty:
        customer_data = customers_df[customers_df["Phone Number"] == st.session_state.selected_customer_phone]
        
        if not customer_data.empty:
            customer = customer_data.iloc[0]
            st.title(f"✨ {customer['First Name']} {customer.get('Last Name', '')}")
            
            col_info, col_notes = st.columns(2)
            with col_info:
                st.markdown("### 👤 פרטים אישיים")
                st.write(f"**טלפון:** {customer['Phone Number']}")
                st.write(f"**כתובת:** {customer.get('Address', '')}")
            
            with col_notes:
                st.markdown("### 📝 הערות")
                current_notes = customer.get("Notes", "")
                new_notes = st.text_area("הוסיפי או ערכי הערות על הלקוחה:", value=current_notes, height=100)
                
                if st.button("💾 שמרי הערות", type="primary"):
                    with st.spinner("שומר..."):
                        st.session_state.customers_df.loc[st.session_state.customers_df["Phone Number"] == st.session_state.selected_customer_phone, "Notes"] = new_notes
                        save_df = st.session_state.customers_df[["Phone Number", "First Name", "Last Name", "Address", "Notes"]]
                        customers_sheet.clear()
                        customers_sheet.update([save_df.columns.values.tolist()] + save_df.values.tolist())
                        st.success("ההערות נשמרו!")
            
            st.markdown("---")
            st.markdown("### 🛍️ היסטוריית רכישות של הלקוחה")
            
            if not orders_df.empty:
                customer_orders = orders_df[orders_df["Phone Number"] == st.session_state.selected_customer_phone].copy()
                
                if not customer_orders.empty:
                    if "Order Date" in customer_orders.columns:
                        customer_orders["Order Date"] = pd.to_datetime(customer_orders["Order Date"], format="%d/%m/%Y", errors="coerce").dt.date
                    if "Delivery Date" in customer_orders.columns:
                        customer_orders["Delivery Date"] = pd.to_datetime(customer_orders["Delivery Date"], format="%d/%m/%Y", errors="coerce").dt.date
                    
                    display_cust_orders = customer_orders.rename(columns={
                        "Order ID": "מספר הזמנה", "Order Date": "תאריך הזמנה", "Delivery Date": "תאריך אספקה",
                        "Item": "פריט", "Status": "סטטוס", "Payment Status": "סטטוס תשלום",
                        "Top Size": "עליון", "Bottom Size": "תחתון", "Custom Size": "התאמות", "Fabric Usage": "צריכת בד (מ')"
                    })
                    
                    # צמצום והגדרת עמודות כדי למנוע גלילה הצידה
                    cols = ["מחיר", "סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "תאריך הזמנה", "פריט"]
                    cols = [c for c in cols if c in display_cust_orders.columns]
                    display_cust_orders = display_cust_orders[cols]
                    
                    config = {
                        "מספר הזמנה": st.column_config.TextColumn("מספר הזמנה", disabled=True, width="small"),
                        "פריט": st.column_config.TextColumn("פריט"),
                        "תאריך הזמנה": st.column_config.DateColumn("תאריך הזמנה", format="DD/MM/YYYY", width="small"),
                        "תאריך אספקה": st.column_config.DateColumn("תאריך אספקה", format="DD/MM/YYYY"),
                        "התאמות": st.column_config.TextColumn("התאמות"),
                        "סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה לייצור)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"]),
                        "סטטוס תשלום": st.column_config.SelectboxColumn("תשלום", options=["🔴", "🟡", "🟢"], width="small"),
                "מחיר": st.column_config.NumberColumn("מחיר", format="₪%d", width="small"),
                        "עליון": st.column_config.TextColumn("עליון"),
                        "תחתון": st.column_config.TextColumn("תחתון")
                    }

                    active_mask_cust = display_cust_orders["סטטוס"] != "✅ נמסרה ללקוחה"
                    active_cust_orders = display_cust_orders[active_mask_cust].copy()
                    completed_cust_orders = display_cust_orders[~active_mask_cust].copy()

                    st.markdown("#### 📋 הזמנות פעילות")
                    if not active_cust_orders.empty:
                        edited_active_cust = st.data_editor(active_cust_orders, key="active_cust_editor", use_container_width=True, hide_index=True, column_config=config)
                    else:
                        st.info("אין ללקוחה זו הזמנות פעילות כרגע.")

                    st.markdown("#### ✅ הזמנות שהושלמו")
                    if not completed_cust_orders.empty:
                        edited_completed_cust = st.data_editor(completed_cust_orders, key="completed_cust_editor", use_container_width=True, hide_index=True, column_config=config)
                    else:
                        st.info("אין ללקוחה זו הזמנות שהושלמו בעבר.")
                    
                    has_changes_cust = not edited_active_cust.equals(active_cust_orders) or not edited_completed_cust.equals(completed_cust_orders)
                    if has_changes_cust:
                        if st.button("💾 שמרי שינויים בהזמנות הלקוחה", type="primary", use_container_width=True):
                            with st.spinner("מעדכן מסד נתונים..."):
                                save_orders = pd.concat([edited_active_cust, edited_completed_cust])
                                save_orders["תאריך הזמנה"] = save_orders["תאריך הזמנה"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
                                save_orders["תאריך אספקה"] = save_orders["תאריך אספקה"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
                                
                                save_orders = save_orders.rename(columns={
                                    "מספר הזמנה": "Order ID", "תאריך הזמנה": "Order Date", "תאריך אספקה": "Delivery Date",
                                    "פריט": "Item", "סטטוס": "Status", "סטטוס תשלום": "Payment Status",
                                    "עליון": "Top Size", "תחתון": "Bottom Size", "התאמות": "Custom Size", "צריכת בד (מ')": "Fabric Usage"
                                })
                                
                                orders_indexed = orders_df.set_index("Order ID")
                                save_indexed = save_orders.set_index("Order ID")
                                orders_indexed.update(save_indexed)
                                orders_indexed.reset_index(inplace=True)
                                
                                for col in ["Payment Date", "Swimsuit Type", "Pattern", "Order Notes", "Fabric 2", "Fabric Usage 2"]:
                                    if col not in orders_indexed.columns:
                                        orders_indexed[col] = ""
                                final_save = orders_indexed[[
                                    "Order ID", "Order Date", "Delivery Date", "Phone Number", "Customer Name", "Item",
                                    "Top Size", "Bottom Size", "Custom Size", "Fabric", "Fabric Usage", "Fabric 2", "Fabric Usage 2",
                                    "Swimsuit Type", "Pattern", "Order Notes",
                                    "Status", "Payment Status", "Supply Type", "Price", "Payment Date"
                                ]]
                                
                                st.session_state.orders_df = final_save
                                orders_sheet.clear()
                                orders_sheet.update([final_save.columns.values.tolist()] + final_save.values.tolist())
                                st.success("ההזמנות עודכנו בהצלחה!"); st.rerun()
                else:
                    st.info("ללקוחה זו עדיין אין היסטוריית הזמנות במערכת.")
            else:
                st.info("לא קיימות הזמנות במערכת הכללית.")

# ==========================================
#               מסכים נוספים
# ==========================================
elif st.session_state.current_view == "פיננסי":
    st.title("💰 ניהול פיננסי ומאזן עסק")
    
    if finance_sheet is None:
        st.error("⚠️ לא מצאתי גיליון בשם 'Finance' ב-Google Sheets. אנא צרי אותו כדי להתחיל לשמור נתונים פיננסיים.")
    else:
        st.markdown("---")
        
        user_settings = finance_data.get("settings", {})
        currency = "₪"
        
        # Data Migration to Flat Transactions
        import uuid
        if "transactions" not in finance_data:
            finance_data["transactions"] = []
            english_months_mig = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            for m_key, m_items in finance_data.get("monthly_expenses", {}).items():
                try:
                    yr, mo_name = m_key.split("-")
                    mo_idx = english_months_mig.index(mo_name) + 1
                    mig_date = f"{yr}-{mo_idx:02d}-01"
                    for itm in m_items:
                        finance_data["transactions"].append({
                            "id": str(uuid.uuid4()),
                            "name": itm.get("name", ""),
                            "amount": float(itm.get("amount", 0)),
                            "Type": itm.get("Type", "Expense"),
                            "date": mig_date
                        })
                except:
                    pass
            save_finance_data(finance_data)
        
        # UI: Dashboard View Selectors
        st.markdown("### בחירת סקירה")
        view_mode = st.radio("סוג תצוגה:", ["סקירה חודשית", "טווח תאריכים מותאם אישית"], horizontal=True, label_visibility="collapsed")
        
        if view_mode == "סקירה חודשית":
            english_months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            hebrew_months = ["ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
            hebrew_to_english = dict(zip(hebrew_months, english_months))
            year_options = list(range(2025, 2035))
            current_dt = datetime.now()
            cur_year_idx = year_options.index(current_dt.year) if current_dt.year in year_options else 1
            cur_month_idx = current_dt.month - 1
            
            c_y, c_m = st.columns([1, 4])
            with c_y:
                selected_year = st.selectbox("שנה", options=year_options, index=cur_year_idx)
            with c_m:
                selected_month_heb = st.radio("חודש", options=hebrew_months, horizontal=True, label_visibility="collapsed", index=cur_month_idx)
                selected_month = hebrew_to_english[selected_month_heb]
            
            month_index = english_months.index(selected_month) + 1
            from calendar import monthrange
            _, last_day = monthrange(selected_year, month_index)
            range_start = date(selected_year, month_index, 1)
            range_end = date(selected_year, month_index, last_day)
            
            st.markdown(f"<h3 style='text-align: center; margin-bottom: 2rem;'>דו״ח פיננסי - {selected_month_heb} {selected_year}</h3>", unsafe_allow_html=True)
            
        else:
            curr_date = date.today()
            first_of_month = curr_date.replace(day=1)
            date_range = st.date_input("בחר טווח תאריכים לסקירה", value=(first_of_month, curr_date))
            
            if isinstance(date_range, tuple) and len(date_range) == 2:
                range_start, range_end = date_range
                st.markdown(f"<h3 style='text-align: center; margin-bottom: 2rem;'>דו״ח ביצועים ({range_start.strftime('%d/%m/%Y')} - {range_end.strftime('%d/%m/%Y')})</h3>", unsafe_allow_html=True)
            else:
                st.warning("אנא בחר טווח תאריכים מלא (התחלה וסיום) לבניית הדו״ח.")
                st.stop()
        
        # --- Aggregation Engine ---
        def get_standing_order_hits(order, rng_start, rng_end):
            try:
                so_start = pd.to_datetime(order["start_date"]).date()
                so_end = pd.to_datetime(order["end_date"]).date()
            except:
                return 0
                
            actual_end = min(rng_end, so_end)
            if rng_start > actual_end: return 0
            if so_start > rng_end: return 0
            
            curr = pd.to_datetime(so_start)
            actual_end_dt = pd.to_datetime(actual_end)
            rng_start_dt = pd.to_datetime(rng_start)
            
            hits = 0
            freq = order.get("frequency", "Monthly")
            if freq == "Monthly":
                offset = pd.DateOffset(months=1)
            elif freq == "Yearly":
                offset = pd.DateOffset(years=1)
            elif freq == "Custom":
                val = int(order.get("custom_interval", 1))
                unit = order.get("custom_unit", "Months")
                if unit == "Days": offset = pd.DateOffset(days=val)
                elif unit == "Weeks": offset = pd.DateOffset(weeks=val)
                elif unit == "Months": offset = pd.DateOffset(months=val)
                elif unit == "Years": offset = pd.DateOffset(years=val)
                else: offset = pd.DateOffset(months=1)
            else:
                offset = pd.DateOffset(months=1)
                
            if freq == "Custom" and val <= 0: offset = pd.DateOffset(months=1)
            
            while curr <= actual_end_dt:
                if curr >= rng_start_dt:
                    hits += 1
                curr += offset
                
            return hits

        # 1. Gather Automated Incomes
        automated_incomes = []
        if not orders_df.empty and "Payment Status" in orders_df.columns:
            if "Payment Date" not in orders_df.columns:
                orders_df["Payment Date"] = orders_df["Order Date"]
            
            paid_orders = orders_df[orders_df["Payment Status"] == "🟢"].copy()
            if not paid_orders.empty:
                paid_orders["Parsed Date"] = paid_orders.apply(
                    lambda r: pd.to_datetime(r["Payment Date"], format="%d/%m/%Y", errors="coerce").date() if pd.notnull(r.get("Payment Date")) and str(r.get("Payment Date")).strip() != "" 
                    else pd.to_datetime(r["Order Date"], format="%d/%m/%Y", errors="coerce").date(),
                    axis=1
                )
                paid_orders = paid_orders.dropna(subset=["Parsed Date"])
                
                paid_in_range = paid_orders[
                    (paid_orders["Parsed Date"] >= range_start) & 
                    (paid_orders["Parsed Date"] <= range_end)
                ]
                
                for _, ro in paid_in_range.iterrows():
                    price_val = pd.to_numeric(ro.get("Price", 0), errors='coerce')
                    if pd.notnull(price_val) and price_val > 0:
                        automated_incomes.append({
                            "name": f"הזמנה #{ro.get('Order ID', '?')} - {ro.get('Customer Name', '')}",
                            "amount": float(price_val),
                            "Type": "Income",
                            "Item": str(ro.get("Item", "כללי")),
                            "date": ro["Parsed Date"].strftime("%Y-%m-%d"),
                            "is_automated": True
                        })
                        
        # 2. Gather Manual Transactions
        manual_in_range = []
        for txn in finance_data.get("transactions", []):
            try:
                txn_date = datetime.strptime(txn.get("date", "2000-01-01"), "%Y-%m-%d").date()
                if range_start <= txn_date <= range_end:
                    manual_in_range.append(txn)
            except:
                pass
                
        # 3. Gather Standing Orders 
        so_in_range = []
        standing_orders_total = 0
        for o in finance_data.get("standing_orders", []):
            hits = get_standing_order_hits(o, range_start, range_end)
            if hits > 0:
                amount_hit = float(o.get("amount", 0)) * hits
                standing_orders_total += amount_hit
                o_clone = o.copy()
                o_clone["amount"] = amount_hit
                so_in_range.append(o_clone)

        # Totals
        extra_income = sum(float(x.get("amount", 0)) for x in manual_in_range if x.get("Type") == "Income") + sum(float(x["amount"]) for x in automated_incomes)
        manual_expenses_total = sum(float(x.get("amount", 0)) for x in manual_in_range if x.get("Type") == "Expense")
        total_expenses = manual_expenses_total + standing_orders_total
        net_balance = extra_income - total_expenses
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-around; background-color: rgba(245,245,245,0.7); padding: 20px; border-radius: 10px; margin-bottom: 2rem; border: 1px solid #ddd;">
            <div style="text-align: center;">
                <h4 style="margin:0; color: #555;">הוצאות</h4>
                <h2 style="margin:0; color: #ef4444;">{total_expenses:,.0f} {currency}</h2>
            </div>
            <div style="text-align: center; border-right: 2px solid #ddd; padding-right: 30px;">
                <h4 style="margin:0; color: #555;">הכנסות</h4>
                <h2 style="margin:0; color: #22c55e;">{extra_income:,.0f} {currency}</h2>
            </div>
            <div style="text-align: center; border-right: 2px solid #ddd; padding-right: 30px;">
                <h4 style="margin:0; color: #555;">מאזן נטו</h4>
                <h2 style="margin:0; color: {'#22c55e' if net_balance >= 0 else '#ef4444'};">{net_balance:,.0f} {currency}</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- Analytics Charts ---
        if extra_income > 0 or total_expenses > 0:
            c_main, c_exp, c_inc = st.columns(3)
            
            with c_main:
                st.markdown("<h4 style='text-align: center;'>מאזן כללי</h4>", unsafe_allow_html=True)
                main_df = pd.DataFrame([
                    {"Category": "הכנסות", "Value": extra_income},
                    {"Category": "הוצאות", "Value": total_expenses}
                ])
                fig_main = px.pie(main_df, names="Category", values="Value", hole=0.4, color="Category", 
                                color_discrete_map={"הכנסות": "#22c55e", "הוצאות": "#ef4444"})
                fig_main.update_traces(textinfo="label+percent", textposition="inside", hovertemplate="%{label}: %{value} " + currency + "<extra></extra>")
                fig_main.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
                st.plotly_chart(fig_main, use_container_width=True)
                
            with c_exp:
                st.markdown("<h4 style='text-align: center;'>פילוח תצרוכת הוצאות</h4>", unsafe_allow_html=True)
                exp_rows = [{"Category": item.get("name", "כללי"), "Value": float(item.get("amount", 0))} for item in manual_in_range if item.get("Type") == "Expense"]
                exp_rows.extend([{"Category": o.get("name", "הוראת קבע"), "Value": float(o.get("amount", 0))} for o in so_in_range])
                
                if exp_rows:
                    exp_df = pd.DataFrame(exp_rows).groupby("Category", as_index=False).sum()
                    fig_exp = px.pie(exp_df, names="Category", values="Value", hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
                    fig_exp.update_traces(textinfo="label+percent", textposition="inside", hovertemplate="%{label}: %{value} " + currency + "<extra></extra>")
                    fig_exp.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
                    st.plotly_chart(fig_exp, use_container_width=True)
                else:
                    st.info("אין הוצאות להצגה.")
                    
            with c_inc:
                st.markdown("<h4 style='text-align: center;'>פילוח דגמים והכנסות</h4>", unsafe_allow_html=True)
                inc_rows = [{"Category": item.get("name", "הכנסה ידנית"), "Value": float(item.get("amount", 0))} for item in manual_in_range if item.get("Type") == "Income"]
                for a in automated_incomes:
                    cat_name = a.get("Item", "כללי")
                    if str(cat_name).strip() == "": cat_name = "כללי"
                    inc_rows.append({"Category": cat_name, "Value": float(a.get("amount", 0))})
                    
                if inc_rows:
                    inc_df = pd.DataFrame(inc_rows).groupby("Category", as_index=False).sum()
                    fig_inc = px.pie(inc_df, names="Category", values="Value", hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
                    fig_inc.update_traces(textinfo="label+percent", textposition="inside", hovertemplate="%{label}: %{value} " + currency + "<extra></extra>")
                    fig_inc.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
                    st.plotly_chart(fig_inc, use_container_width=True)
                else:
                    st.info("אין הכנסות להצגה.")
        
        st.markdown("---")
        
        expenses_tab, standing_orders_tab = st.tabs(["💸 תנועות ידניות", "🔄 הוצאות שוטפות"])
        
        with expenses_tab:
            st.subheader("הוספת תנועה חדשה")
            with st.form("add_txn_form", clear_on_submit=True):
                col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
                with col_f1: transaction_name = st.text_input("שם התנועה/קטגוריה (למשל: בדים / משלוח)")
                with col_f2: transaction_type = st.selectbox("סוג", ["Expense", "Income"], format_func=lambda x: "הוצאה" if x=="Expense" else "הכנסה")
                with col_f3: transaction_amount = st.number_input(f"סכום ({currency})", min_value=0.0, step=1.0)
                with col_f4: transaction_date = st.date_input("תאריך", value=date.today())
                
                if st.form_submit_button("➕ הוסיפי תנועה", use_container_width=True):
                    if transaction_name.strip() and transaction_amount > 0:
                        finance_data["transactions"].append({
                            "id": str(uuid.uuid4()),
                            "name": transaction_name.strip(),
                            "amount": float(transaction_amount),
                            "Type": transaction_type,
                            "date": transaction_date.strftime("%Y-%m-%d")
                        })
                        save_finance_data(finance_data)
                        st.success("התנועה נוספה!")
                        st.rerun()
                    else:
                        st.warning("נא להזין שם תקין וסכום.")

            st.markdown("### 📋 טבלת תנועות")
            if finance_data.get("transactions", []):
                txn_df = pd.DataFrame(finance_data.get("transactions", []))
                
                if st.session_state.get("delete_mode_txn", False) == True:
                    txn_df["בחרי"] = False
                
                txn_df["date_ts"] = pd.to_datetime(txn_df["date"], errors="coerce")
                txn_df = txn_df.sort_values(by="date_ts", ascending=False)
                
                txn_display = txn_df[["id"]].copy()
                txn_display["סכום"] = txn_df["amount"]
                txn_display["סוג"] = txn_df["Type"].map({"Expense": "הוצאה", "Income": "הכנסה"})
                txn_display["תאריך"] = txn_df["date_ts"].dt.date
                txn_display["שם התנועה"] = txn_df["name"]
                if "בחרי" in txn_df.columns: txn_display["בחרי"] = txn_df["בחרי"]
                
                conf = {
                    "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "שם התנועה": st.column_config.TextColumn("שם התנועה"),
                    "תאריך": st.column_config.DateColumn("תאריך", format="DD/MM/YYYY"),
                    "סוג": st.column_config.SelectboxColumn("סוג", options=["הוצאה", "הכנסה"]),
                    "סכום": st.column_config.NumberColumn("סכום", format="₪%d")
                }
                
                edited_txn = st.data_editor(txn_display.drop("id", axis=1), use_container_width=True, hide_index=True, column_config=conf, key="txn_editor")
                edited_txn["id"] = txn_display["id"]
                
                c_del, c_save, c_sel = st.columns([6, 2, 2])
                with c_sel:
                    if not st.session_state.get("delete_mode_txn", False):
                        if st.button("בחרי למחיקה", key="sel_t", use_container_width=True):
                            st.session_state.delete_mode_txn = True; st.rerun()
                    else:
                        if st.button("בטלי בחירה", key="canc_t", use_container_width=True):
                            st.session_state.delete_mode_txn = False; st.rerun()
                
                with c_save:
                    if st.session_state.get("delete_mode_txn", False):
                        to_del = edited_txn[edited_txn["בחרי"] == True]
                        if not to_del.empty:
                            if st.button("מחקי מסומנות 🗑️", type="primary", use_container_width=True):
                                ids_to_del = to_del["id"].tolist()
                                finance_data["transactions"] = [x for x in finance_data["transactions"] if x["id"] not in ids_to_del]
                                save_finance_data(finance_data)
                                st.session_state.delete_mode_txn = False
                                st.rerun()
                    else:
                        if st.button("💾 שמרי שינויים", type="primary", use_container_width=True):
                            for _, r in edited_txn.iterrows():
                                for t in finance_data["transactions"]:
                                    if t["id"] == r["id"]:
                                        t["name"] = str(r["שם התנועה"])
                                        t["amount"] = float(r["סכום"])
                                        t["Type"] = "Expense" if r["סוג"] == "הוצאה" else "Income"
                                        if pd.notnull(r["תאריך"]):
                                            t["date"] = r["תאריך"].strftime("%Y-%m-%d") 
                            save_finance_data(finance_data)
                            st.success("המידע התעדכן במערכת!")
                            st.rerun()
                            
            else:
                st.info("אין תנועות במערכת ברשימה ההסטורית.")

        with standing_orders_tab:
            st.subheader("ניהול הוצאות קבועות")
            with st.form("add_so_form", clear_on_submit=True):
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1: order_name = st.text_input("שם ההוצאה הקבועה")
                with col_s2: order_amount = st.number_input(f"סכום חיוב ({currency})", min_value=0.0, step=1.0)
                with col_s3: order_frequency = st.selectbox("תדירות חיוב", ["Monthly", "Yearly", "Custom"], format_func=lambda x: {"Monthly": "חודשית", "Yearly": "שנתית", "Custom": "מותאם אישית"}[x])
                
                st.caption("אם בחרת 'מותאם אישית', נא למלא (למשל כל 3 חודשים):")
                col_s4, col_s5 = st.columns(2)
                with col_s4: val_c = st.number_input("מספר", min_value=1, step=1)
                with col_s5: unit_c = st.selectbox("תקופה", ["Days", "Weeks", "Months", "Years"], format_func=lambda x: {"Days": "ימים", "Weeks": "שבועות", "Months": "חודשים", "Years": "שנים"}[x])
                
                c_d1, c_d2 = st.columns(2)
                with c_d1: order_start_date = st.date_input("תאריך התחלה", value=date.today())
                with c_d2: order_end_date = st.date_input("תאריך סיום", value=date(2035, 12, 31))
                
                if st.form_submit_button("הוסיפי הוראת קבע", use_container_width=True):
                    if order_name.strip() and order_amount > 0:
                        finance_data["standing_orders"].append({
                            "id": str(uuid.uuid4()),
                            "name": order_name.strip(),
                            "amount": float(order_amount),
                            "frequency": order_frequency,
                            "custom_interval": val_c,
                            "custom_unit": unit_c,
                            "start_date": order_start_date.strftime("%Y-%m-%d"),
                            "end_date": order_end_date.strftime("%Y-%m-%d"),
                        })
                        save_finance_data(finance_data)
                        st.success("הוראת הקבע נוספה!")
                        st.rerun()
                    else:
                        st.warning("נא להזין שם תקני וסכום.")
            
            st.markdown("### 📋 עריכת הוראות קבע")
            if finance_data.get("standing_orders", []):
                for so in finance_data["standing_orders"]:
                    if "id" not in so: so["id"] = str(uuid.uuid4())
                
                so_df = pd.DataFrame(finance_data.get("standing_orders", []))
                
                if st.session_state.get("delete_mode_so", False) == True:
                    so_df["בחרי"] = False
                    
                so_disp = so_df[["id"]].copy()
                
                def render_freq(row):
                    freq = row.get("frequency", "Monthly")
                    if freq == "Monthly": return "חודשית"
                    if freq == "Yearly": return "שנתית"
                    val = row.get("custom_interval", 1)
                    unit = row.get("custom_unit", "Months")
                    map_u = {"Days":"ימים", "Weeks":"שבועות", "Months":"חודשים", "Years":"שנים"}
                    return f"כל {val} {map_u.get(unit, unit)}"
                
                so_disp["סיום"] = pd.to_datetime(so_df["end_date"], errors="coerce").dt.date
                so_disp["התחלה"] = pd.to_datetime(so_df["start_date"], errors="coerce").dt.date
                so_disp["סכום"] = so_df["amount"]
                so_disp["תדירות"] = so_df.apply(render_freq, axis=1)
                so_disp["שם ההוצאה"] = so_df["name"]
                if "בחרי" in so_df.columns: so_disp["בחרי"] = so_df["בחרי"]
                
                conf = {
                    "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "שם ההוצאה": st.column_config.TextColumn("שם ההוצאה", disabled=True),
                    "תדירות": st.column_config.TextColumn("תדירות", disabled=True),
                    "סכום": st.column_config.NumberColumn("סכום (₪)", disabled=True),
                    "התחלה": st.column_config.DateColumn("התחלה", format="DD/MM/YYYY", disabled=True),
                    "סיום": st.column_config.DateColumn("סיום", format="DD/MM/YYYY", disabled=True)
                }
                
                edited_so = st.data_editor(so_disp.drop("id", axis=1), use_container_width=True, hide_index=True, column_config=conf, key="so_editor")
                edited_so["id"] = so_disp["id"]
                
                c_del_s, c_emp_s, c_sel_s = st.columns([6, 2, 2])
                with c_sel_s:
                    if not st.session_state.get("delete_mode_so", False):
                        if st.button("בחרי למחיקה", key="so_sel", use_container_width=True):
                            st.session_state.delete_mode_so = True; st.rerun()
                    else:
                        if st.button("בטלי בחירה", key="canc_so", use_container_width=True):
                            st.session_state.delete_mode_so = False; st.rerun()
                            
                with c_emp_s:
                    if st.session_state.get("delete_mode_so", False):
                        to_del = edited_so[edited_so["בחרי"] == True]
                        if not to_del.empty:
                            if st.button("מחקים 🗑️", type="primary", use_container_width=True):
                                ids_to_del = to_del["id"].tolist()
                                finance_data["standing_orders"] = [x for x in finance_data["standing_orders"] if x["id"] not in ids_to_del]
                                save_finance_data(finance_data)
                                st.session_state.delete_mode_so = False
                                st.rerun()
            else:
                st.info("אין הוראות קבע פעילות.")

