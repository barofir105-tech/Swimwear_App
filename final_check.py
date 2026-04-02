import subprocess, sys

files = [
    'main.py', 'utils.py',
    'views/dashboard.py', 'views/inventory.py', 'views/patterns.py',
    'views/orders.py', 'views/customers.py', 'views/financial.py'
]
all_ok = True
for f in files:
    r = subprocess.run([sys.executable, '-m', 'py_compile', f], capture_output=True, text=True)
    ok = r.returncode == 0
    if not ok:
        all_ok = False
    n = len(open(f, encoding='utf-8').readlines())
    status = 'OK ' if ok else 'ERR'
    print(status + ' ' + f.ljust(35) + ' (' + str(n) + ' lines)')
    if not ok:
        print('     ' + r.stderr.strip()[:120])
print()
print('ALL CLEAN' if all_ok else 'ERRORS FOUND')
