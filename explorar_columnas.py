import csv, os
from collections import Counter

# Try to read raw lines and see total columns per row
temp_dir = os.environ['TEMP']
path = os.path.join(temp_dir, 'latinbien_raw.csv')

with open(path, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')
header = lines[0].strip()
header_cols = header.split(',')
print(f'Header columns count: {len(header_cols)}')

# Check a few data rows for column count
for i in range(1, min(6, len(lines))):
    cols = lines[i].strip().split(',')
    print(f'Row {i}: {len(cols)} columns')

# The problem might be that the CSV export only goes to a certain column
# Let's try fetching with a different approach - use the Sheets API export with range

# Try to export with explicitly defined range
import urllib.request
import json

# Try the default sheet (gid=0) to see if it has more columns
url_default = 'https://docs.google.com/spreadsheets/d/1kKq4y9ZtjmdacmEgQtMX64_puRNClibBOUd0in5TB6I/export?format=csv'
try:
    with urllib.request.urlopen(url_default) as response:
        content = response.read().decode('utf-8-sig')
        lines_def = content.split('\n')
        header_def = lines_def[0].strip().split(',')
        print(f'\nDefault sheet (gid=0): {len(header_def)} columns')
        for i, c in enumerate(header_def):
            print(f'  [{i}] {c}')
except Exception as e:
    print(f'Error fetching default: {e}')

# The current gid sheet
print(f'\nCurrent sheet (gid=1961588350): {len(header_cols)} columns')
for i, c in enumerate(header_cols):
    print(f'  [{i}] {c}')
