import os
import re

with open('swimwear_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the Order ID fetch logic to perform one time migration
migration_logic = """        if not df.empty and "Phone Number" in df.columns:
            df["Phone Number"] = df["Phone Number"].astype(str).apply(lambda x: '0' + x if len(x) == 9 and not x.startswith('0') else x)
            if "Payment Date" not in df.columns:
                df["Payment Date"] = ""
            
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
"""

# Text replacement
old_fetch = """        if not df.empty and "Phone Number" in df.columns:
            df["Phone Number"] = df["Phone Number"].astype(str).apply(lambda x: '0' + x if len(x) == 9 and not x.startswith('0') else x)
            if "Payment Date" not in df.columns:
                df["Payment Date"] = ""
"""
text = text.replace(old_fetch, migration_logic)

with open('swimwear_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Migration injected")
