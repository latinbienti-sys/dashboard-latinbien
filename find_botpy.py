import requests, json, sys, subprocess, os
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Find the acrux chatbot bot.py file on the server
# Try common Odoo paths
paths_to_check = [
    '/odoo/odoo-server/addons/acrux_chatbot/models/bot.py',
    '/odoo/odoo-server/addons/acrux_chatbot/models/acrux_chat_bot.py',
    '/home/odoo/odoo-server/addons/acrux_chatbot/models/bot.py',
    '/home/odoo/odoo-server/addons/acrux_chatbot/models/acrux_chat_bot.py',
    '/usr/lib/python3/dist-packages/odoo/addons/acrux_chatbot/models/bot.py',
    '/usr/lib/python3/dist-packages/odoo/addons/acrux_chatbot/models/acrux_chat_bot.py',
]

# Try SSH to server and find the file
if os.name == 'nt':  # Windows
    cmds = []
    for p in paths_to_check:
        cmds.append(f'if exist {p} echo {p}')
    full_cmd = ' & '.join(cmds)
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=15)
    print("Local results:", result.stdout[:500])
else:
    print("Not on Windows, skipping local check")
