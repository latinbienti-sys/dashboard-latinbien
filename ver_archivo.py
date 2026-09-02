#!/usr/bin/env python3
"""Check the current state of the generated HTML."""
import os

path = 'C:\\Users\\yarleyc\\Documents\\New OpenCode Project\\index.html'
print(f'File exists: {os.path.exists(path)}')
print(f'File size: {os.path.getsize(path)} bytes')

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print(f'Total chars: {len(c)}')
print(f'Has DOCTYPE: {c[:20]}')
print(f'Has Chart.js CDN: {"chart.js" in c}')
print(f'Has script tag: {"<script>" in c}')
print(f'Has DATA: {"const DATA = " in c}')
print(f'Has safeChart: {"safeChart" in c}')
print(f'Has try: {"try {" in c}')
print(f'Has catch: {"catch(e)" in c}')
print(f'Has body: {"<body>" in c}')
print(f'Has closing html: {"</html>" in c}')
print(f'\nFirst 100 chars:')
print(c[:100])
print(f'\nLast 100 chars:')
print(c[-100:])

# Check for any null bytes
null_pos = c.find('\x00')
if null_pos >= 0:
    print(f'\nWARNING: null byte at position {null_pos}!')
else:
    print('\nNo null bytes found')
