#!/usr/bin/env python3
"""Generate GitHub stats SVG cards using the GitHub REST API.

This script fetches user statistics and repository language data
directly from the GitHub API and generates SVG stat cards,
eliminating the need for external Vercel-hosted services.
"""

import json
import os
import sys
import urllib.request
import urllib.error

GITHUB_API = "https://api.github.com"
USERNAME = os.environ.get("GITHUB_USERNAME", "Himeth777")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# TokyoNight-inspired color palette (matches original theme)
THEME = {
    "bg": "#0D1117",
    "title": "#70a5fd",
    "text": "#a9b1d6",
    "icon": "#bf91f3",
    "ring": "#70a5fd",
    "border": "#1a1b27",
    "lang_colors": [
        "#f1e05a",  # JavaScript / Yellow
        "#3178c6",  # TypeScript / Blue
        "#3572A5",  # Python / Deep Blue
        "#b07219",  # Java / Brown
        "#e34c26",  # HTML / Red-Orange
        "#563d7c",  # CSS / Purple
        "#00ADD8",  # Go / Cyan
        "#dea584",  # Rust / Peach
        "#178600",  # Shell / Green
        "#dc3545",  # Ruby / Red
    ],
}

# Well-known GitHub language colors
LANG_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Java": "#b07219",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Dart": "#00B4AB",
    "Lua": "#000080",
    "Haskell": "#5e5086",
    "Jupyter Notebook": "#DA5B0B",
    "SCSS": "#c6538c",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
    "SQL": "#e38c00",
}


def api_request(url):
    """Make authenticated GitHub API request."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API error {e.code} for {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_user_stats():
    """Fetch user profile stats."""
    user = api_request(f"{GITHUB_API}/users/{USERNAME}")
    return {
        "name": user.get("name") or USERNAME,
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
    }


def fetch_repo_stats():
    """Fetch all repos and compute aggregate stats."""
    repos = []
    page = 1
    while True:
        url = f"{GITHUB_API}/users/{USERNAME}/repos?per_page=100&page={page}"
        batch = api_request(url)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    total_issues = sum(r.get("open_issues_count", 0) for r in repos)

    return {
        "total_stars": total_stars,
        "total_forks": total_forks,
        "total_issues": total_issues,
        "repos": repos,
    }


def fetch_language_stats(repos):
    """Compute language usage across all repos."""
    lang_bytes = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        langs_url = repo.get("languages_url")
        if not langs_url:
            continue
        langs = api_request(langs_url)
        for lang, byte_count in langs.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + byte_count

    total = sum(lang_bytes.values()) or 1
    lang_pcts = [
        (lang, count / total * 100)
        for lang, count in sorted(lang_bytes.items(), key=lambda x: -x[1])
    ]
    return lang_pcts


def escape_xml(text):
    """Escape special XML characters."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_stats_svg(user_stats, repo_stats):
    """Generate the main GitHub stats SVG card."""
    name = escape_xml(user_stats["name"])
    items = [
        ("⭐", "Total Stars", str(repo_stats["total_stars"])),
        ("🔀", "Total Forks", str(repo_stats["total_forks"])),
        ("📁", "Public Repos", str(user_stats["public_repos"])),
        ("🐛", "Open Issues", str(repo_stats["total_issues"])),
        ("👥", "Followers", str(user_stats["followers"])),
    ]

    row_height = 30
    card_height = 120 + len(items) * row_height

    rows_svg = ""
    for i, (icon, label, value) in enumerate(items):
        y = 80 + i * row_height
        rows_svg += f"""
    <g transform="translate(25, {y})">
      <text x="0" y="0" class="icon">{icon}</text>
      <text x="28" y="0" class="stat-label">{escape_xml(label)}:</text>
      <text x="260" y="0" class="stat-value">{escape_xml(value)}</text>
    </g>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{card_height}" viewBox="0 0 400 {card_height}">
  <defs>
    <style>
      .card-bg {{ fill: {THEME["bg"]}; stroke: {THEME["ring"]}; stroke-width: 1; rx: 10; }}
      .title {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {THEME["title"]}; }}
      .stat-label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {THEME["text"]}; }}
      .stat-value {{ font: 700 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {THEME["title"]}; text-anchor: end; }}
      .icon {{ font-size: 16px; }}
    </style>
  </defs>
  <rect class="card-bg" x="0.5" y="0.5" width="399" height="{card_height - 1}" rx="10"/>
  <text x="25" y="40" class="title">{name}'s GitHub Stats</text>
  <line x1="25" y1="55" x2="375" y2="55" stroke="{THEME["ring"]}" stroke-width="0.5" opacity="0.5"/>
  {rows_svg}
</svg>"""
    return svg


def generate_langs_svg(lang_pcts, max_langs=8):
    """Generate the top languages SVG card."""
    langs = lang_pcts[:max_langs]
    if not langs:
        langs = [("No data", 100)]

    bar_width = 350
    card_height = 120 + len(langs) * 28

    # Progress bar segments
    bar_segments = ""
    x_offset = 0
    for i, (lang, pct) in enumerate(langs):
        width = pct / 100 * bar_width
        color = LANG_COLORS.get(lang, THEME["lang_colors"][i % len(THEME["lang_colors"])])
        bar_segments += f'<rect x="{25 + x_offset}" y="55" width="{width}" height="8" rx="2" fill="{color}"/>\n    '
        x_offset += width

    # Legend items
    legend_svg = ""
    for i, (lang, pct) in enumerate(langs):
        y = 85 + i * 25
        color = LANG_COLORS.get(lang, THEME["lang_colors"][i % len(THEME["lang_colors"])])
        legend_svg += f"""
    <g transform="translate(25, {y})">
      <circle cx="6" cy="-4" r="6" fill="{color}"/>
      <text x="18" y="0" class="lang-name">{escape_xml(lang)}</text>
      <text x="355" y="0" class="lang-pct">{pct:.1f}%</text>
    </g>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{card_height}" viewBox="0 0 400 {card_height}">
  <defs>
    <style>
      .card-bg {{ fill: {THEME["bg"]}; stroke: {THEME["ring"]}; stroke-width: 1; rx: 10; }}
      .title {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {THEME["title"]}; }}
      .lang-name {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: {THEME["text"]}; }}
      .lang-pct {{ font: 600 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: {THEME["text"]}; text-anchor: end; }}
    </style>
  </defs>
  <rect class="card-bg" x="0.5" y="0.5" width="399" height="{card_height - 1}" rx="10"/>
  <text x="25" y="38" class="title">Most Used Languages</text>
    {bar_segments}
  {legend_svg}
</svg>"""
    return svg


def main():
    output_dir = os.environ.get("OUTPUT_DIR", "stats")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Fetching stats for {USERNAME}...")
    user_stats = fetch_user_stats()
    print(f"  Name: {user_stats['name']}, Repos: {user_stats['public_repos']}")

    repo_stats = fetch_repo_stats()
    print(f"  Stars: {repo_stats['total_stars']}, Forks: {repo_stats['total_forks']}")

    print("Fetching language stats...")
    lang_pcts = fetch_language_stats(repo_stats["repos"])
    for lang, pct in lang_pcts[:8]:
        print(f"  {lang}: {pct:.1f}%")

    stats_svg = generate_stats_svg(user_stats, repo_stats)
    stats_path = os.path.join(output_dir, "github-stats.svg")
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(stats_svg)
    print(f"Generated {stats_path}")

    langs_svg = generate_langs_svg(lang_pcts)
    langs_path = os.path.join(output_dir, "top-langs.svg")
    with open(langs_path, "w", encoding="utf-8") as f:
        f.write(langs_svg)
    print(f"Generated {langs_path}")

    print("Done!")


if __name__ == "__main__":
    main()
