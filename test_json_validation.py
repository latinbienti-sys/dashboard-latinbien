#!/usr/bin/env python3
"""Validate the JSON embedded in index.html."""
import re
import json

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find JSON.parse position
idx = content.find("JSON.parse(")
if idx < 0:
    print("No JSON.parse found!")
    exit(1)

# Find the opening quote after JSON.parse('
start = content.find("'", idx)
if start < 0:
    print("No opening quote found!")
    exit(1)

# The JSON string starts after the opening quote
# We need to find the matching closing quote that is NOT escaped
# Since the JSON string contains JS-escaped characters,
# we need to find the ' that is preceded by an odd number of backslashes
# or just find the pattern: '); } catch(e)

end_marker = "'); } catch(e)"
end = content.find(end_marker, start)
if end < 0:
    print("No closing marker found!")
    exit(1)

# Extract the JSON string
raw_js_str = content[start+1:end]  # skip the opening '
print(f"Extracted JS-escaped JSON string: {len(raw_js_str)} chars")

# Unescape: \\ -> \, \' -> ', \<\/ -> <\/
# This reverses the Python escaping done in generar_html.py
# The escaping was: json_escaped = json_str.replace('\\', '\\\\').replace("'", "\\'").replace('</', '<\\/')
# So unescape: \\\\ -> \\ (handle first to not interfere), then \' -> ', then <\/ -> </

# Step 1: Replace double-escaped backslashes with a placeholder
# Then handle single-escaped sequences, then restore backslashes
unescaped = raw_js_str.replace("\\\\", "\x00\x00")  # double backslash -> placeholder
unescaped = unescaped.replace("\\'", "'")  # escaped quote -> quote
unescaped = unescaped.replace("\\/", "/")  # escaped forward slash -> forward slash
unescaped = unescaped.replace("\x00\x00", "\\")  # placeholder -> single backslash

# Now try to parse as JSON
try:
    data = json.loads(unescaped)
    print(f"JSON VALID! {len(data.get('clients', []))} clients found")
    print(f"Keys: {list(data.keys())[:10]}")
    print(f"Total facturado: {data.get('total_facturado', 'N/A')}")
    print(f"Client count: {data.get('client_count', 'N/A')}")
except json.JSONDecodeError as e:
    print(f"JSON INVALID: {e}")
    # Show context around the error
    err_pos = e.pos
    print(f"Context: ...{unescaped[max(0,err_pos-200):err_pos+200]}...")
