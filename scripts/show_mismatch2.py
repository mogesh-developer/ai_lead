from pathlib import Path
s = Path('frontend/src/pages/SearchLeads.jsx').read_text()
stack = []
quotes = {'"':False, "'":False, '`':False}
escaped = False
line = 1
for i,ch in enumerate(s):
    if ch == '\n':
        line += 1
    if ch == '\\' and not escaped:
        escaped = True
        continue
    if escaped:
        escaped = False
        continue
    if ch in quotes and not any(quotes[q] for q in quotes if q != ch):
        quotes[ch] = not quotes[ch]
        continue
    if any(quotes.values()):
        continue
    if ch in '{([':
        stack.append((ch,line,i))
    elif ch in '})]':
        if not stack:
            print(f'Unmatched closing {ch} at line {line} index {i}')
            break
        open_ch, oline, oi = stack.pop()
        pairs = { '{':'}','(':')','[':']' }
        if pairs[open_ch] != ch:
            print(f'Mismatch: opened {open_ch} at line {oline} idx {oi} but closed with {ch} at line {line} idx {i}')
            print('\nOpen context around line', oline, ':')
            start = max(0, oi - 120)
            end = min(len(s), oi + 120)
            print(s[start:end])
            print('\nClose context around line', line, ':')
            start = max(0, i - 120)
            end = min(len(s), i + 120)
            print(s[start:end])
            break
else:
    if stack:
        print('Remaining stack entries:')
        for ch,ln,idx in stack[-10:]:
            print(ch,'opened at line',ln,'idx',idx)
            start=max(0,idx-60)
            end=min(len(s), idx+60)
            print('\nContext:\n', s[start:end])
    else:
        print('All balanced')
