import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("app.js", "r", encoding="utf-8") as f:
    js = f.read()

print("--- MODALS IN HTML ---")
modals = re.findall(r'id="([^"]*[Mm]odal[^"]*)"', html)
for m in set(modals):
    print(f"Modal: {m}")

print("\n--- ONCLICK HANDLERS IN HTML ---")
onclicks = re.findall(r'onclick="([^"(]+)\(', html)
unique_clicks = sorted(set(onclicks))
for fn in unique_clicks:
    exists_in_js = f"function {fn}" in js or f"{fn} =" in js or f"async function {fn}" in js or fn in js
    print(f"Handler: {fn}() -> Defined in app.js? {exists_in_js}")

print("\n--- HEADER BUTTONS ---")
header_chunk = html[html.find('<header'):html.find('</header>')]
for m in re.finditer(r'<(button|a)[^>]*>(.*?)</\1>', header_chunk, re.S):
    tag = m.group(1)
    content = re.sub(r'\s+', ' ', m.group(2)).strip()
    full = m.group(0)
    onclick_match = re.search(r'onclick="([^"]*)"', full)
    href_match = re.search(r'href="([^"]*)"', full)
    action = onclick_match.group(1) if onclick_match else (href_match.group(1) if href_match else 'None')
    print(f"[{tag.upper()}] '{content}' -> Action: {action}")
