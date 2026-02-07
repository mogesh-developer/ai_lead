from pathlib import Path
s=Path('frontend/src/pages/SearchLeads.jsx').read_text()
stack=[]
quotes={'"':False,"'":False,'`':False}
esc=False
line=1
for i,ch in enumerate(s):
    if ch=='\n': line+=1; continue
    if ch=='\\' and not esc: esc=True; continue
    if esc: esc=False; continue
    if ch in quotes and not any(quotes[q] for q in quotes if q!=ch): quotes[ch]=not quotes[ch]; continue
    if any(quotes.values()): continue
    if ch in '{([':
        stack.append((ch,line,i))
    elif ch in '})]':
        if not stack:
            print('unmatched closing', ch, 'at line', line)
            break
        open_ch, oline, oi = stack.pop()
        pairs={'{':'}','(':')','[':']'}
        if pairs[open_ch] != ch:
            print('mismatch: opened', open_ch, 'at line', oline, 'but closed with', ch, 'at line', line)
            # we still continue
print('Remaining stack (unclosed openings):')
for ch, ln, idx in stack:
    print(ch, 'at line', ln, 'idx', idx)
    start=max(0, idx-40)
    end=min(len(s), idx+40)
    print('Context:\n', s[start:end])
