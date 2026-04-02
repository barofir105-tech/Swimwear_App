"""
views/dashboard.py — Home dashboard view.
Shows live KPIs, recent orders, and low-inventory alerts.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date


def render_dashboard():
    orders_df    = st.session_state.orders_df
    inventory_df = st.session_state.inventory_df
    customers_df = st.session_state.customers_df
    finance_data = st.session_state.finance_data

    st.title("🏠 לוח בקרה — Kalimi Manager")
    st.caption(f"עדכון אחרון: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.markdown("---")

    # ── KPI Row ──────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)

    total_orders  = len(orders_df) if not orders_df.empty else 0
    active_orders = len(orders_df[orders_df["Status"] != "✅ נמסרה ללקוחה"]) if not orders_df.empty else 0
    ready_pickup  = len(orders_df[orders_df["Status"] == "📦 מוכנה לאיסוף/משלוח"]) if not orders_df.empty else 0
    total_customers = len(customers_df) if not customers_df.empty else 0

    # Monthly revenue (current month, paid orders)
    monthly_rev = 0.0
    if not orders_df.empty and "Payment Status" in orders_df.columns:
        now = datetime.now()
        paid = orders_df[orders_df["Payment Status"] == "🟢"].copy()
        if not paid.empty and "Payment Date" in paid.columns:
            paid["_pd"] = pd.to_datetime(paid["Payment Date"], format="%d/%m/%Y", errors="coerce")
            this_month = paid[(paid["_pd"].dt.month == now.month) & (paid["_pd"].dt.year == now.year)]
            monthly_rev = pd.to_numeric(this_month.get("Price", 0), errors="coerce").fillna(0).sum()

    with k1:
        st.markdown("""<div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:12px;padding:18px 14px;text-align:center;color:white;">
            <div style="font-size:2rem;font-weight:800;">{}</div>
            <div style="font-size:0.85rem;opacity:0.9;">📦 הזמנות פעילות</div>
        </div>""".format(active_orders), unsafe_allow_html=True)
    with k2:
        st.markdown("""<div style="background:linear-gradient(135deg,#f59e0b,#f97316);border-radius:12px;padding:18px 14px;text-align:center;color:white;">
            <div style="font-size:2rem;font-weight:800;">{}</div>
            <div style="font-size:0.85rem;opacity:0.9;">🚚 מוכנות לאיסוף</div>
        </div>""".format(ready_pickup), unsafe_allow_html=True)
    with k3:
        st.markdown("""<div style="background:linear-gradient(135deg,#22c55e,#16a34a);border-radius:12px;padding:18px 14px;text-align:center;color:white;">
            <div style="font-size:2rem;font-weight:800;">₪{:,.0f}</div>
            <div style="font-size:0.85rem;opacity:0.9;">💰 הכנסות החודש</div>
        </div>""".format(monthly_rev), unsafe_allow_html=True)
    with k4:
        st.markdown("""<div style="background:linear-gradient(135deg,#0ea5e9,#2563eb);border-radius:12px;padding:18px 14px;text-align:center;color:white;">
            <div style="font-size:2rem;font-weight:800;">{}</div>
            <div style="font-size:0.85rem;opacity:0.9;">👥 לקוחות רשומות</div>
        </div>""".format(total_customers), unsafe_allow_html=True)
    with k5:
        st.markdown("""<div style="background:linear-gradient(135deg,#ec4899,#be185d);border-radius:12px;padding:18px 14px;text-align:center;color:white;">
            <div style="font-size:2rem;font-weight:800;">{}</div>
            <div style="font-size:0.85rem;opacity:0.9;">🧺 סה"כ הזמנות</div>
        </div>""".format(total_orders), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two columns: Recent orders + Low inventory ────────────────────────
    col_orders, col_inv = st.columns([3, 2])

    with col_orders:
        st.markdown("### 📋 הזמנות פעילות אחרונות")
        if not orders_df.empty:
            active = orders_df[orders_df["Status"] != "✅ נמסרה ללקוחה"].copy()
            if not active.empty:
                active["_sort"] = pd.to_numeric(active["Order ID"], errors="coerce")
                active = active.sort_values("_sort", ascending=False).head(8)
                for _, row in active.iterrows():
                    status = str(row.get("Status", ""))
                    pay    = str(row.get("Payment Status", "🔴"))
                    name   = str(row.get("Customer Name", ""))
                    oid    = str(row.get("Order ID", ""))
                    price  = row.get("Price", 0)
                    delivery = str(row.get("Delivery Date", ""))

                    status_color = {"🆕": "#6366f1", "✂": "#f59e0b", "📦": "#22c55e"}.get(status[:1], "#94a3b8")
                    pay_emoji = {"🟢": "💚", "🟡": "💛", "🔴": "❤️"}.get(pay, "❓")

                    st.markdown(f"""
                    <div style="border-right:3px solid {status_color};padding:8px 12px;margin-bottom:6px;
                                background:rgba(0,0,0,0.02);border-radius:0 6px 6px 0;display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <strong>#{oid}</strong> — {name}<br>
                            <small style="color:#888;">{status}</small>
                        </div>
                        <div style="text-align:left;">
                            {pay_emoji} ₪{price:g}<br>
                            <small style="color:#888;">📅 {delivery}</small>
                        </div>
                    </div>""", unsafe_allow_html=True)

                if st.button("➡️ ראי את כל ההזמנות", use_container_width=True):
                    st.session_state.current_view = "הזמנות"
                    st.rerun()
            else:
                st.info("אין הזמנות פעילות כרגע 🎉")
        else:
            st.info("אין הזמנות במערכת עדיין.")

    with col_inv:
        st.markdown("### ⚠️ בדים עם מלאי נמוך")
        if not inventory_df.empty:
            inv = inventory_df.copy()
            inv["Initial Meters"] = pd.to_numeric(inv["Initial Meters"], errors="coerce").fillna(0)
            low = inv[inv["Initial Meters"] < 3].sort_values("Initial Meters")
            if not low.empty:
                for _, row in low.iterrows():
                    meters = float(row["Initial Meters"])
                    name   = str(row.get("Fabric Name", ""))
                    sku    = str(row.get("Fabric ID", ""))
                    bar_color = "#ef4444" if meters < 1 else "#f59e0b"
                    bar_pct   = max(int(meters / 3 * 100), 4)
                    st.markdown(f"""
                    <div style="margin-bottom:10px;padding:8px 12px;background:#fff8f8;border-radius:8px;border:1px solid #fecaca;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                            <strong>{name}</strong>
                            <span style="color:{bar_color};font-weight:700;">{meters:.1f} מ'</span>
                        </div>
                        <small style="color:#888;">מק"ט: {sku}</small>
                        <div style="background:#f1f5f9;border-radius:4px;height:6px;margin-top:4px;">
                            <div style="background:{bar_color};width:{bar_pct}%;height:6px;border-radius:4px;"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                if st.button("➡️ נהלי את המלאי", use_container_width=True):
                    st.session_state.current_view = "מלאי"
                    st.rerun()
            else:
                st.success("כל הבדים במלאי תקין ✅")

            # Summary mini-table
            st.markdown("#### 📊 סיכום מלאי")
            total_fabrics = len(inv)
            total_meters  = inv["Initial Meters"].sum()
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-top:8px;">
                <div style="flex:1;background:linear-gradient(135deg,#f8f9ff,#eef0ff);padding:10px;border-radius:8px;text-align:center;">
                    <div style="font-size:1.5rem;font-weight:700;color:#6366f1;">{total_fabrics}</div>
                    <div style="font-size:0.75rem;color:#888;">סוגי בד</div>
                </div>
                <div style="flex:1;background:linear-gradient(135deg,#f0fdf4,#dcfce7);padding:10px;border-radius:8px;text-align:center;">
                    <div style="font-size:1.5rem;font-weight:700;color:#22c55e;">{total_meters:.0f}</div>
                    <div style="font-size:0.75rem;color:#888;">מטרים כולל</div>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("אין מלאי במערכת עדיין.")

    st.markdown("---")

    # ── Quick actions ─────────────────────────────────────────────────────
    st.markdown("### ⚡ פעולות מהירות")
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("➕ הזמנה חדשה", use_container_width=True, type="primary"):
            st.session_state.current_view = "הזמנות"; st.rerun()
    with qa2:
        if st.button("👤 לקוחה חדשה", use_container_width=True):
            st.session_state.current_view = "לקוחות"; st.rerun()
    with qa3:
        if st.button("🧵 הוסיפי בד", use_container_width=True):
            st.session_state.current_view = "מלאי"; st.rerun()
    with qa4:
        if st.button("💰 נהלי פיננסים", use_container_width=True):
            st.session_state.current_view = "פיננסי"; st.rerun()
