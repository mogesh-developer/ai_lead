from pathlib import Path
s = Path('frontend/src/pages/SearchLeads.jsx').read_text()
# find the specific indices reported earlier
open_idx = 4045
close_idx = 15754
print('Open context (around index', open_idx, '):')
start = max(0, open_idx-120)
end = min(len(s), open_idx+120)
print(s[start:end])
print('\nClose context (around index', close_idx, '):')
start = max(0, close_idx-120)
end = min(len(s), close_idx+120)
print(s[start:end])
print('\nOpen line number:', s.count('\n',0,open_idx)+1)
print('Close line number:', s.count('\n',0,close_idx)+1)
