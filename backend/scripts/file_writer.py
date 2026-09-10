import sys
target = sys.argv[1]
data = sys.stdin.read()
with open(target, 'w', encoding='utf-8') as f:
    f.write(data)
print(f'Wrote {len(data)} chars to {target}')
