from pathlib import Path
s=Path('frontend/src/pages/SearchLeads.jsx').read_text().splitlines()
stack=[]
for i,line in enumerate(s,1):
    # naive: count occurrences
    opens = line.count('<div')
    closes = line.count('</div>')
    for _ in range(opens): stack.append((i,line.strip()))
    for _ in range(closes):
        if stack: stack.pop()
        else: print('Extra close at',i,line)
print('Remaining unclosed divs:', len(stack))
if stack:
    print('Top unclosed at line',stack[-1][0], stack[-1][1])
    # print context around it
    start=max(1,stack[-1][0]-6)
    end=min(len(s),stack[-1][0]+6)
    print('\nContext:')
    print('\n'.join(f"{j}: {s[j-1]}" for j in range(start,end+1)))
