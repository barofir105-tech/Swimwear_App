import traceback

try:
    with open('swimwear_app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == 'elif st.session_state.current_view == "הזמנות":':
            for j in range(i, len(lines)):
                if lines[j].strip() == 'if orders_sheet is None:':
                    start_idx = j + 2 # index of `else:` is j+1, inside else is j+2
                    break
            break

    # The line at start_idx should be `if not orders_df.empty:`
    
    # We need to find the form. The user reverted it so the form is at the bottom.
    form_start = -1
    end_idx = -1
    for i in range(start_idx, len(lines)):
        if 'st.subheader("➕ יצירת הזמנה חדשה")' in lines[i]:
            form_start = i - 2 # including 'st.markdown("---")'
        if 'מסך הלקוחות' in lines[i]:
            end_idx = i - 2
            break

    if form_start == -1:
        print("Could not find form")
        sys.exit()

    extracted_form = lines[form_start:end_idx]
    
    # remove the form from its old place
    lines = lines[:form_start] + lines[end_idx:]
    
    # insert form at the top (start_idx)
    lines.insert(start_idx, ''.join(extracted_form))
    # lines is a list of strings. If we join extracted_form, we inserted a single big string. 
    # Let's cleanly convert extracted_form to string and insert.
    # Actually better:
    
    header = lines[:start_idx]
    middle_table_part = lines[start_idx:form_start]
    tail = lines[end_idx:]
    
    # reverse columns in table logic
    for i, line in enumerate(middle_table_part):
        if line.strip().startswith('cols = [') and 'סטטוס' in line:
            # We want 'שם לקוחה' on the right-most, which means LAST in the list visually:
            # wait, if cols = [0, 1, 2] renders [0 | 1 | 2]
            # then Rightmost is 2! So 'שם לקוחה' should be at index -1.
            middle_table_part[i] = '            cols = ["סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "תאריך הזמנה", "פריט", "שם לקוחה"]\n'
            
        if line.strip().startswith('config = {'):
            config_end = -1
            for j in range(i, len(middle_table_part)):
                if middle_table_part[j].strip() == '}':
                    config_end = j
                    break
            config_text = """            config = {
                "שם לקוחה": st.column_config.TextColumn("שם לקוחה", disabled=True),
                "פריט": st.column_config.TextColumn("פריט"),
                "תאריך הזמנה": st.column_config.DateColumn("תאריך הזמנה", format="DD/MM/YYYY", width="small"),
                "תאריך אספקה": st.column_config.DateColumn("תאריך אספקה", format="DD/MM/YYYY"),
                "עליון": st.column_config.TextColumn("עליון"),
                "תחתון": st.column_config.TextColumn("תחתון"),
                "התאמות": st.column_config.TextColumn("התאמות"),
                "מספר הזמנה": st.column_config.TextColumn("מספר הזמנה", disabled=True, width="small"),
                "סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה לייצור)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"]),
                "סטטוס תשלום": st.column_config.SelectboxColumn("תשלום", options=["🔴", "🟡", "🟢"], width="small"),
            }\n"""
            middle_table_part[i:config_end+1] = [config_text]
            break

    # do customer table cols too (around line 850 in new file)
    # wait, tail contains customer table!
    for i, line in enumerate(tail):
        if line.strip().startswith('cols = [') and 'סטטוס' in line:
            tail[i] = '                    cols = ["סטטוס תשלום", "סטטוס", "מספר הזמנה", "התאמות", "תחתון", "עליון", "תאריך אספקה", "פריט"]\n'
        if line.strip().startswith('config = {'):
            config_end = -1
            for j in range(i, len(tail)):
                if tail[j].strip() == '}':
                    config_end = j
                    break
            config_text = """                    config = {
                        "מספר הזמנה": st.column_config.TextColumn("מספר הזמנה", disabled=True, width="small"),
                        "פריט": st.column_config.TextColumn("פריט"),
                        "התאמות": st.column_config.TextColumn("התאמות"),
                        "תאריך אספקה": st.column_config.DateColumn("תאריך אספקה", format="DD/MM/YYYY", width="small"),
                        "סטטוס": st.column_config.SelectboxColumn("סטטוס", options=["🆕 התקבלה (ממתינה לייצור)", "✂️ בגזירה/תפירה", "📦 מוכנה לאיסוף/משלוח", "✅ נמסרה ללקוחה"]),
                        "סטטוס תשלום": st.column_config.SelectboxColumn("סטטוס תשלום", options=["🔴", "🟡", "🟢"], width="small"),
                        "עליון": st.column_config.TextColumn("עליון"),
                        "תחתון": st.column_config.TextColumn("תחתון")
                    }\n"""
            tail[i:config_end+1] = [config_text]
            break

    new_lines = header + extracted_form + ["        st.markdown('---')\n"] + middle_table_part + tail

    with open('swimwear_app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print('success')

except Exception as e:
    print('Error:', e)
    traceback.print_exc()
