from pathlib import Path
s = Path('frontend/src/pages/SearchLeads.jsx').read_text()
lines = s.splitlines()
cum = 0
for i, line in enumerate(lines, start=1):
    # naive counts, acceptable for quick diagnosis
    # ignore braces inside strings roughly by skipping lines containing '//' or '/*' might not be perfect
    openb = line.count('{')
    closeb = line.count('}')
    cum += openb - closeb
    if cum != 0:
        print(i, cum, line)
# print final cum
print('final cum', cum)
