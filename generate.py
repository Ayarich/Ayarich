#!/usr/bin/env python3
"""Create self-hosted public/private GitHub contribution SVGs from authenticated GraphQL."""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
USER = os.getenv('GITHUB_PROFILE_USER', 'Ayarich')
TOKEN = os.getenv('GH_PROFILE_TOKEN', '').strip()


def query_github():
    if not TOKEN:
        raise RuntimeError('GH_PROFILE_TOKEN missing. Add a GitHub Actions repository secret with a classic token (read:user scope).')
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=365)
    query = '''query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount contributionLevel } }
          }
        }
      }
    }'''
    payload = json.dumps({'query': query, 'variables': {'login': USER, 'from': start.isoformat(), 'to': now.isoformat()}}).encode('utf-8')
    request = urllib.request.Request('https://api.github.com/graphql', data=payload,
        headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json',
                 'Accept': 'application/vnd.github+json', 'User-Agent': 'ayarich-profile-calendar'})
    with urllib.request.urlopen(request, timeout=30) as response:
        output = json.loads(response.read())
    if output.get('errors'):
        raise RuntimeError('GraphQL errors: ' + json.dumps(output['errors']))
    user = (output.get('data') or {}).get('user')
    if not user:
        raise RuntimeError('User not found or GitHub returned no user data.')
    return user['contributionsCollection']['contributionCalendar']


def render(calendar):
    weeks = calendar['weeks']
    days = [d for w in weeks for d in w['contributionDays']]
    if not days:
        raise RuntimeError('No calendar days returned by GitHub.')
    scores = [int(d['contributionCount']) for d in days]
    total = int(calendar['totalContributions'])
    active = sum(x > 0 for x in scores)
    longest = current = 0
    for x in scores:
        current = current + 1 if x > 0 else 0
        longest = max(longest, current)
    max_count = max(scores)
    x0, y0, step, size = 78, 80, 15, 12
    width = max(910, x0 + len(weeks) * step + 28)
    height = 248
    colors = {'NONE':'#ebedf0', 'FIRST_QUARTILE':'#9be9a8', 'SECOND_QUARTILE':'#40c463',
              'THIRD_QUARTILE':'#30a14e', 'FOURTH_QUARTILE':'#216e39'}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            '<title id="title">GitHub contribution calendar for ' + escape(USER) + '</title>',
            '<desc id="desc">Eligible public and private contributions from the last year. ' + str(total) + ' total contributions.</desc>',
            '<rect width="100%" height="100%" rx="16" fill="#ffffff"/>',
            '<text x="24" y="32" font-family="Arial,sans-serif" font-size="20" font-weight="700" fill="#24292f">Contribution Calendar</text>',
            f'<text x="24" y="54" font-family="Arial,sans-serif" font-size="13" fill="#57606a">{total:,} contributions in the last year · Public + eligible private</text>']
    for day, label in ((1,'Mon'),(3,'Wed'),(5,'Fri')):
        parts.append(f'<text x="28" y="{y0 + day*step+10}" font-family="Arial,sans-serif" font-size="12" fill="#57606a">{label}</text>')
    last_month = None
    for wi, week in enumerate(weeks):
        for d in week['contributionDays']:
            dt = datetime.strptime(d['date'], '%Y-%m-%d')
            if dt.month != last_month and dt.day <= 7:
                parts.append(f'<text x="{x0+wi*step}" y="73" font-family="Arial,sans-serif" font-size="12" fill="#57606a">{dt.strftime("%b")}</text>')
                last_month = dt.month
            row = (dt.weekday() + 1) % 7
            color = colors.get(d['contributionLevel'], '#ebedf0')
            parts.append(f'<rect x="{x0+wi*step}" y="{y0+row*step}" width="{size}" height="{size}" rx="2" fill="{color}"><title>{escape(d["date"])}: {int(d["contributionCount"])} contributions</title></rect>')
    parts.extend([f'<text x="{width-220}" y="225" font-family="Arial,sans-serif" font-size="12" fill="#57606a">Less</text>'])
    for i, color in enumerate(colors.values()):
        parts.append(f'<rect x="{width-185+i*18}" y="215" width="12" height="12" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{width-88}" y="225" font-family="Arial,sans-serif" font-size="12" fill="#57606a">More</text></svg>')
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / 'contributions.svg').write_text(''.join(parts), encoding='utf-8')

    cards = [('TOTAL CONTRIBUTIONS', f'{total:,}'), ('ACTIVE DAYS', str(active)),
             ('LONGEST STREAK', f'{longest} days'), ('BUSIEST DAY', str(max_count))]
    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 175" role="img" aria-labelledby="title">',
         '<title id="title">GitHub contribution summary</title>', '<rect width="900" height="175" rx="16" fill="#0d1117"/>']
    for i, (label, value) in enumerate(cards):
        x = 24+i*222
        p.extend([f'<rect x="{x}" y="25" width="208" height="125" rx="10" fill="#161b22" stroke="#30363d"/>',
                  f'<text x="{x+15}" y="60" font-family="Arial,sans-serif" font-size="12" fill="#8b949e">{label}</text>',
                  f'<text x="{x+15}" y="111" font-family="Arial,sans-serif" font-size="34" font-weight="700" fill="#58a6ff">{escape(value)}</text>'])
    p.append('</svg>')
    (ASSETS / 'summary.svg').write_text(''.join(p), encoding='utf-8')
    print(f'Created SVGs: {total} contributions, {active} active days, {longest} longest streak')


if __name__ == '__main__':
    try:
        # Test fixture is only used locally; the workflow never supplies it.
        fixture = os.getenv('PROFILE_TEST_FIXTURE')
        data = json.loads(Path(fixture).read_text()) if fixture else query_github()
        render(data)
    except Exception as exc:
        print('Contribution generation failed: ' + str(exc), file=sys.stderr)
        sys.exit(1)
