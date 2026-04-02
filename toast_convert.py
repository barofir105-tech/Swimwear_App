import re, os

view_files = ['views/orders.py', 'views/inventory.py', 'views/customers.py',
              'views/financial.py', 'views/patterns.py']

for vf in view_files:
    text = open(vf, encoding='utf-8').read()
    orig = text
    # st.success(...); st.rerun() --> st.toast(..., icon="checkmark"); st.rerun()
    text = re.sub(
        r'st\.success\(([^)]+)\); st\.rerun\(\)',
        lambda m: f'st.toast({m.group(1)}, icon="\u2705"); st.rerun()',
        text
    )
    # standalone st.success(...)
    text = re.sub(
        r'st\.success\(([^)]+)\)',
        lambda m: f'st.toast({m.group(1)}, icon="\u2705")',
        text
    )
    if text != orig:
        open(vf, 'w', encoding='utf-8').write(text)
        n = text.count('st.toast')
        print(f'  {vf}: converted, now has {n} toast calls')
    else:
        print(f'  {vf}: nothing converted')
