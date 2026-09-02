#!/usr/bin/env python3
"""Extract and validate the full tooltip expression."""
import json, re

with open('C:\\Users\\yarleyc\\Documents\\New OpenCode Project\\index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the segKeys.reduce expression
idx = c.find('segKeys.reduce((a,s)')
if idx < 0:
    print("Not found!")
    exit(1)

print(f"Found at position {idx}")
print()

# Extract from the beginning of the arrow function
# Find the start: '=>' before the expression
arrow_start = c.rfind('=>', idx-200, idx)
print(f"Arrow at {arrow_start}")

# Extract from there to the end of the tooltip callback
# The callback ends at ',' or '}'
start = arrow_start - 5  # include 'label'
# Find the end by tracking balanced braces and parens
depth_paren = 0
depth_brace = 0
end = idx
while end < len(c):
    ch = c[end]
    if ch == '(':
        depth_paren += 1
    elif ch == ')':
        depth_paren -= 1
    elif ch == '{':
        depth_brace += 1
    elif ch == '}':
        depth_brace -= 1
        if depth_paren <= 0 and depth_brace <= 0:
            end += 1
            break
    elif ch == ',' and depth_paren == 0 and depth_brace == 0:
        break
    end += 1

full_expr = c[start:end]
print(f"Full tooltip expression ({len(full_expr)} chars):")
print(full_expr)
print()

# Count parens
opens = full_expr.count('(')
closes = full_expr.count(')')
print(f"Parentheses: {opens} open, {closes} close")
if opens != closes:
    print(f"UNBALANCED! Missing {opens - closes} closing parens")
else:
    print("BALANCED!")

# Also count braces
opens_b = full_expr.count('{')
closes_b = full_expr.count('}')
print(f"Braces: {opens_b} open, {closes_b} close")
if opens_b != closes_b:
    print(f"UNBALANCED braces! Missing {opens_b - closes_b}")
