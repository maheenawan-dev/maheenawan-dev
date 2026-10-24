"""Fetch REAL public contribution data and draw assets/heatmap.svg.
Usage: python scripts/update_heatmap.py [github-username]"""
import re, sys, datetime, urllib.request, html

USER = sys.argv[1] if len(sys.argv) > 1 else "maheenawan-dev"
req = urllib.request.Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "Mozilla/5.0"})
page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

cells = re.findall(r'<td[^>]*?data-date="([\d-]+)"[^>]*?id="([^"]+)"[^>]*?data-level="(\d)"', page)
tips = dict(re.findall(r'for="(contribution-day-component[^"]+)"[^>]*>([^<]*)</tool-tip>', page))
assert cells, "no contribution cells found"

days = []
for d, cid, lvl in cells:
    m = re.match(r"(\d+) contribution", tips.get(cid, ""))
    days.append((datetime.date.fromisoformat(d), int(lvl), int(m.group(1)) if m else 0))
days.sort()

total = sum(c for _, _, c in days)
active = sum(1 for _, _, c in days if c > 0)
longest = run = 0
prev = None
for d, _, c in days:
    if c > 0:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        longest = max(longest, run)
        prev = d
    else:
        run = 0
        prev = None

COL = ["#2B1521", "#701A3D", "#A23B66", "#C77B9B", "#F8D3E0"]
S, G, X0, Y0 = 12, 3, 46, 112
first = days[0][0]
start = first - datetime.timedelta(days=(first.weekday() + 1) % 7)
cols = ((days[-1][0] - start).days // 7) + 1
W = X0 + cols * (S + G) + 24
H = Y0 + 7 * (S + G) + 44
F = "Segoe UI,Arial,sans-serif"
b = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub contributions: {total} in the last year, {active} active days, longest streak {longest} days">',
     '<defs><linearGradient id="hm-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#190B12"/><stop offset="1" stop-color="#451126"/></linearGradient></defs>',
     f'<rect width="{W}" height="{H}" rx="14" fill="#10070C"/><rect width="{W}" height="{H}" rx="14" fill="url(#hm-bg)" opacity=".75"/>',
     f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="13" fill="none" stroke="#C77B9B" stroke-opacity=".3"/>',
     '<text x="24" y="34" font-family="Consolas,monospace" font-size="12" fill="#C77B9B" letter-spacing="2">COMMIT LOG · REAL GITHUB ACTIVITY</text>',
     '<text x="24" y="72" font-family="Georgia,serif" font-size="20" fill="#F8F0F3">A year of building, one square at a time.</text>']
# stat boxes (all computed from real data)
for i, (n, l) in enumerate(((total, "CONTRIBUTIONS"), (active, "ACTIVE DAYS"), (longest, "LONGEST STREAK"))):
    bw = 104
    x = W - 24 - (3 - i) * (bw + 8) + 8
    b.append(f'<rect x="{x}" y="20" width="{bw}" height="58" rx="10" fill="#10070C" fill-opacity=".6" stroke="#C77B9B" stroke-opacity=".35"/>')
    b.append(f'<text x="{x+14}" y="50" font-family="Georgia,serif" font-size="26" fill="#F8F0F3">{n}</text>')
    b.append(f'<text x="{x+14}" y="68" font-family="Consolas,monospace" font-size="9" fill="#C77B9B" letter-spacing="1.5">{l}</text>')

last_month = None; last_label_col = None
CYCLE = 7.0
for date, lvl, cnt in days:
    c = (date - start).days // 7
    r = (date.weekday() + 1) % 7
    x, y = X0 + c * (S + G), Y0 + r * (S + G)
    if date.month != last_month:
        if last_label_col is None or c - last_label_col >= 3:
            last_label_col = c
            b.append(f'<text x="{x}" y="{Y0-10}" font-family="{F}" font-size="10" fill="#E5B5C7" opacity=".8">{date.strftime("%b")}</text>')
        last_month = date.month
    # 1) squares appear one column at a time, 2) active squares breathe
    reveal = f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{round(c*0.045,3)}s" fill="freeze"/>'
    pulse = f'<animate attributeName="fill-opacity" values="1;.6;1" dur="2.8s" begin="{round(c*0.09,2)}s" repeatCount="indefinite"/>' if lvl else ""
    b.append(f'<rect x="{x}" y="{y}" width="{S}" height="{S}" rx="3" fill="{COL[lvl]}" opacity="0">{reveal}{pulse}<title>{cnt} contributions on {date.isoformat()}</title></rect>')
    # 3) a light sweeps left to right across the grid, then repeats
    t = 0.08 + 0.78 * c / (cols - 1)
    peak = .85 if lvl else .30
    kt = f"0;{max(t-0.05,0.001):.3f};{t:.3f};{min(t+0.08,0.999):.3f};1"
    b.append(f'<rect x="{x}" y="{y}" width="{S}" height="{S}" rx="3" fill="#F8D3E0" opacity="0" pointer-events="none"><animate attributeName="opacity" values="0;0;{peak};0;0" keyTimes="{kt}" dur="{CYCLE}s" begin="1.5s" repeatCount="indefinite"/></rect>')
for i, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    b.append(f'<text x="24" y="{Y0 + i*(S+G) + 10}" font-family="{F}" font-size="10" fill="#E5B5C7" opacity=".7">{name}</text>')
lx = W - 24 - 5 * 15 - 60
b.append(f'<text x="{lx}" y="{H-16}" text-anchor="end" font-family="{F}" font-size="10" fill="#E5B5C7" opacity=".8">Less</text>')
for i, col in enumerate(COL):
    b.append(f'<rect x="{lx + 8 + i*15}" y="{H-26}" width="{S}" height="{S}" rx="3" fill="{col}"/>')
b.append(f'<text x="{lx + 8 + 5*15 + 4}" y="{H-16}" font-family="{F}" font-size="10" fill="#E5B5C7" opacity=".8">More</text>')
b.append('</svg>')
inner = "\n".join(b)
PW, PAD, HEAD = 940, 20, 86
PH = PAD + HEAD + 16 + H + PAD
nest_open = f'<svg x="{(PW - W)//2}" y="{PAD + HEAD + 16}" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
inner = re.sub(r"<svg[^>]*>", nest_open, inner, count=1)
panel = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {PW} {PH}" width="{PW}" height="{PH}" role="img" aria-label="GitHub contributions: {total} in the last year, {active} active days, longest streak {longest} days">'
  '<defs><linearGradient id="ha-ln" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#701A3D"/><stop offset=".5" stop-color="#E5B5C7"/><stop offset="1" stop-color="#701A3D"/></linearGradient></defs>'
  f'<rect width="{PW}" height="{PH}" rx="18" fill="#0B0509"/><rect x="1" y="1" width="{PW-2}" height="{PH-2}" rx="17" fill="none" stroke="#C77B9B" stroke-opacity=".25"/>'
  f'<rect x="{PAD}" y="{PAD}" width="900" height="{HEAD}" rx="12" fill="#10070C"/>'
  f'<text x="{PAD+20}" y="{PAD+26}" font-family="Consolas,monospace" font-size="12" fill="#C77B9B" letter-spacing="3">05 / ACTIVITY</text>'
  f'<text x="{PAD+20}" y="{PAD+64}" font-family="Georgia,serif" font-size="32" fill="#F8F0F3">A year of building.</text>'
  f'<rect x="{PAD+20}" y="{PAD+76}" width="860" height="2" fill="url(#ha-ln)" opacity=".7"/>'
  f'<rect x="{PAD+20}" y="{PAD+75}" width="80" height="4" rx="2" fill="#E5B5C7"><animate attributeName="x" values="{PAD+20};{PAD+800};{PAD+20}" dur="9s" repeatCount="indefinite"/></rect>'
  + inner + '</svg>')
open("assets/heatmap.svg", "w", encoding="utf-8").write(panel)
print(f"heatmap.svg: {len(days)} days, {total} contributions, {active} active days, longest streak {longest}")
