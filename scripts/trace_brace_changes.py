from pathlib import Path
s=Path('frontend/src/pages/SearchLeads.jsx').read_text()
quotes={'"':False,"'":False,'`':False}
esc=False
cum=0
line=1
for i,ch in enumerate(s):
    if ch=='\n':
        line+=1
        continue
    if ch=='\\' and not esc:
        esc=True; continue
    if esc:
        esc=False; continue
    # toggle quotes
    if ch in quotes and not any(quotes[q] for q in quotes if q!=ch):
        quotes[ch]=not quotes[ch]; continue
    if any(quotes.values()): continue
    if ch=='{':
        cum+=1
        print(f'INC {cum} at line {line} idx {i} (char {{)')
    elif ch=='}':
        print('DEC', cum, 'at line', line, 'idx', i, '(char } )')
        cum-=1
print('Final cum', cum)
