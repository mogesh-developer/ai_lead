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
    if ch=='(': 
        stack.append((ch,line,i))
        # print('PUSH ( at line',line,'idx',i)
    elif ch==')':
        if not stack:
            print('Unmatched closing ) at line', line, 'idx', i)
            # print context
            start=max(0,i-60); end=min(len(s),i+60)
            print(s[start:end])
            break
        open_ch, oline, oi = stack.pop()
        # print('POP ) matching ( opened at line',oline)

else:
    if stack:
        print('Remaining unclosed parens:')
        for ch,ln,idx in stack:
            print(ch, 'open at line', ln, 'idx', idx)
    else:
        print('All parens matched')
