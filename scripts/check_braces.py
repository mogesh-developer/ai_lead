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
    # toggle quotes
    if ch in quotes and not any(quotes[q] for q in quotes if q != ch):
        quotes[ch] = not quotes[ch]
        continue
    if any(quotes.values()):
        continue
    if ch in '{([':
        stack.append((ch,line,i))
    elif ch in '})]':
        if not stack:
            print(f'Unmatched {ch} at line {line} index {i}')
            break
        open_ch, oline, oi = stack.pop()
        pairs = { '{':'}','(':')','[':']' }
        if pairs[open_ch] != ch:
            print(f'Mismatch: opened {open_ch} at line {oline} idx {oi} but closed with {ch} at line {line} idx {i}')
            break
else:
    if stack:
        open_ch, oline, oi = stack[-1]
        print(f'Unclosed {open_ch} opened at line {oline} index {oi}')
    else:
        print('All balanced')
