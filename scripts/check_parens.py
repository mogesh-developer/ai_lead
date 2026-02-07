from pathlib import Path
s = Path('frontend/src/pages/SearchLeads.jsx').read_text()
for i, l in enumerate(s.splitlines(), start=1):
    open_p = l.count('(')
    close_p = l.count(')')
    if open_p != close_p:
        print(f"{i}: (={open_p}, )={close_p} --> {l}")
