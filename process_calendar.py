#!/usr/bin/env python3
"""Fetch and process the FIFA World Cup 2026 ICS calendar.

Applies these fixes to the source calendar:
- Renames "Ivory Coast" → "Côte d'Ivoire"
- Renames "Curacao" → "Curaçao"
- Adds missing flag emojis to match summaries
- Normalizes extra whitespace
"""

import re
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://calendar.kubeia.io/"
    "world-cup-no-alarm-with-score-tv-united-states-of-america-the.ics"
)
OUTPUT_FILE = Path("calendar.ics")

COUNTRY_RENAMES = {
    "Ivory Coast": "Côte d'Ivoire",
    "Curacao": "Curaçao",
}

# Sorted by name length descending at build time to avoid substring collisions
# (e.g. "D.R. Congo" must match before a hypothetical shorter "Congo")
_FLAGS_RAW: dict[str, str] = {
    "Democratic Republic of the Congo": "🇨🇩",
    "Bosnia and Herzegovina": "🇧🇦",
    "Trinidad and Tobago": "🇹🇹",
    "Antigua and Barbuda": "🇦🇬",
    "United Arab Emirates": "🇦🇪",
    "Dominican Republic": "🇩🇴",
    "Czech Republic": "🇨🇿",
    "United States": "🇺🇸",
    "North Macedonia": "🇲🇰",
    "Côte d'Ivoire": "🇨🇮",
    "Sierra Leone": "🇸🇱",
    "Burkina Faso": "🇧🇫",
    "South Africa": "🇿🇦",
    "South Korea": "🇰🇷",
    "Saudi Arabia": "🇸🇦",
    "New Zealand": "🇳🇿",
    "North Korea": "🇰🇵",
    "El Salvador": "🇸🇻",
    "D.R. Congo": "🇨🇩",
    "Costa Rica": "🇨🇷",
    "Cape Verde": "🇨🇻",
    "Netherlands": "🇳🇱",
    "Switzerland": "🇨🇭",
    "Afghanistan": "🇦🇫",
    "Philippines": "🇵🇭",
    "Uzbekistan": "🇺🇿",
    "Mozambique": "🇲🇿",
    "Kazakhstan": "🇰🇿",
    "Azerbaijan": "🇦🇿",
    "Bangladesh": "🇧🇩",
    "Mauritania": "🇲🇷",
    "Montenegro": "🇲🇪",
    "Luxembourg": "🇱🇺",
    "Nicaragua": "🇳🇮",
    "Argentina": "🇦🇷",
    "Australia": "🇦🇺",
    "Lithuania": "🇱🇹",
    "Venezuela": "🇻🇪",
    "Palestine": "🇵🇸",
    "Indonesia": "🇮🇩",
    "Guatemala": "🇬🇹",
    "Djibouti": "🇩🇯",
    "Colombia": "🇨🇴",
    "Tanzania": "🇹🇿",
    "Slovakia": "🇸🇰",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Slovenia": "🇸🇮",
    "Portugal": "🇵🇹",
    "Paraguay": "🇵🇾",
    "Pakistan": "🇵🇰",
    "Curaçao": "🇨🇼",
    "Honduras": "🇭🇳",
    "Botswana": "🇧🇼",
    "Cameroon": "🇨🇲",
    "Malaysia": "🇲🇾",
    "Bulgaria": "🇧🇬",
    "Cambodia": "🇰🇭",
    "Ethiopia": "🇪🇹",
    "Zimbabwe": "🇿🇼",
    "Romania": "🇷🇴",
    "Morocco": "🇲🇦",
    "Moldova": "🇲🇩",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Ecuador": "🇪🇨",
    "Denmark": "🇩🇰",
    "Croatia": "🇭🇷",
    "Comoros": "🇰🇲",
    "Belgium": "🇧🇪",
    "Belarus": "🇧🇾",
    "Armenia": "🇦🇲",
    "Algeria": "🇩🇿",
    "Albania": "🇦🇱",
    "Ukraine": "🇺🇦",
    "Uruguay": "🇺🇾",
    "Tunisia": "🇹🇳",
    "Türkiye": "🇹🇷",
    "Turkey": "🇹🇷",
    "Thailand": "🇹🇭",
    "Vietnam": "🇻🇳",
    "Bolivia": "🇧🇴",
    "Namibia": "🇳🇦",
    "Georgia": "🇬🇪",
    "Germany": "🇩🇪",
    "Finland": "🇫🇮",
    "Iceland": "🇮🇸",
    "Hungary": "🇭🇺",
    "Lebanon": "🇱🇧",
    "Austria": "🇦🇹",
    "Andorra": "🇦🇩",
    "Bahrain": "🇧🇭",
    "Bahamas": "🇧🇸",
    "Somalia": "🇸🇴",
    "Nigeria": "🇳🇬",
    "Jamaica": "🇯🇲",
    "Estonia": "🇪🇪",
    "Ireland": "🇮🇪",
    "Senegal": "🇸🇳",
    "Burundi": "🇧🇮",
    "Brunei": "🇧🇳",
    "Rwanda": "🇷🇼",
    "Poland": "🇵🇱",
    "Panama": "🇵🇦",
    "Norway": "🇳🇴",
    "Mexico": "🇲🇽",
    "Kuwait": "🇰🇼",
    "Jordan": "🇯🇴",
    "Israel": "🇮🇱",
    "Greece": "🇬🇷",
    "Guinea": "🇬🇳",
    "France": "🇫🇷",
    "Gambia": "🇬🇲",
    "Russia": "🇷🇺",
    "Uganda": "🇺🇬",
    "Sweden": "🇸🇪",
    "Serbia": "🇷🇸",
    "Cyprus": "🇨🇾",
    "Brazil": "🇧🇷",
    "Canada": "🇨🇦",
    "Kuwait": "🇰🇼",
    "Zambia": "🇿🇲",
    "Spain": "🇪🇸",
    "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Sudan": "🇸🇩",
    "Syria": "🇸🇾",
    "Qatar": "🇶🇦",
    "Chile": "🇨🇱",
    "China": "🇨🇳",
    "Egypt": "🇪🇬",
    "Ghana": "🇬🇭",
    "Haiti": "🇭🇹",
    "India": "🇮🇳",
    "Italy": "🇮🇹",
    "Japan": "🇯🇵",
    "Kenya": "🇰🇪",
    "Libya": "🇱🇾",
    "Malta": "🇲🇹",
    "Gabon": "🇬🇦",
    "Cuba": "🇨🇺",
    "Mali": "🇲🇱",
    "Oman": "🇴🇲",
    "Peru": "🇵🇪",
    "Togo": "🇹🇬",
    "Fiji": "🇫🇯",
    "Iran": "🇮🇷",
    "Iraq": "🇮🇶",
    "USA": "🇺🇸",
    "Yemen": "🇾🇪",
}

COUNTRY_FLAGS: list[tuple[str, str]] = sorted(
    _FLAGS_RAW.items(), key=lambda x: -len(x[0])
)


def fetch_calendar(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "WorldCupCalBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def unfold(content: str) -> list[str]:
    """Undo RFC 5545 line folding."""
    unfolded = re.sub(r"\r?\n[ \t]", "", content)
    return unfolded.splitlines()


def fold(line: str) -> str:
    """Fold a line to ≤75 UTF-8 octets per RFC 5545."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    parts: list[str] = []
    current = ""
    for ch in line:
        candidate = current + ch
        if len(candidate.encode("utf-8")) > 75:
            parts.append(current)
            current = " " + ch  # continuation lines start with a space
        else:
            current = candidate
    if current:
        parts.append(current)
    return "\r\n".join(parts)


def apply_renames(text: str) -> str:
    for old, new in COUNTRY_RENAMES.items():
        text = text.replace(old, new)
    return text


def add_emoji_left(text: str) -> str:
    """Add flag emoji after the country name on the left side of the summary."""
    for country, emoji in COUNTRY_FLAGS:
        if country in text and emoji not in text:
            return text.replace(country, f"{country} {emoji}", 1)
    return text


def add_emoji_right(text: str) -> str:
    """Add flag emoji before the country name on the right side of the summary."""
    for country, emoji in COUNTRY_FLAGS:
        if country in text and emoji not in text:
            return text.replace(country, f"{emoji} {country}", 1)
    return text


def process_summary(value: str) -> str:
    value = apply_renames(value)

    # Split into left / right halves on the central " - " separator.
    # Format: "TeamA [🏳] [N] - [M] [🏳] TeamB"
    # Using non-greedy match so we split at the *first* " - " (the score separator).
    m = re.match(r"^(.*?)\s+-\s+(.*)$", value)
    if m:
        left, right = add_emoji_left(m.group(1)), add_emoji_right(m.group(2))
        value = f"{left} - {right}"

    # Collapse any runs of multiple spaces
    return re.sub(r" {2,}", " ", value).strip()


def process_line(line: str) -> str:
    if line.startswith("SUMMARY:"):
        return "SUMMARY:" + process_summary(line[len("SUMMARY:"):])

    if line.startswith("DESCRIPTION:"):
        value = apply_renames(line[len("DESCRIPTION:"):])
        value = re.sub(r" {2,}", " ", value)
        return "DESCRIPTION:" + value

    if line.startswith("LOCATION:"):
        return "LOCATION:" + apply_renames(line[len("LOCATION:"):])

    return line


def process_calendar(content: str) -> str:
    lines = unfold(content)
    processed = [fold(process_line(ln)) for ln in lines]
    return "\r\n".join(processed)


def main() -> int:
    print(f"Fetching {SOURCE_URL} …")
    try:
        raw = fetch_calendar(SOURCE_URL)
    except Exception as exc:
        print(f"ERROR fetching calendar: {exc}", file=sys.stderr)
        return 1

    processed = process_calendar(raw)

    existing = OUTPUT_FILE.read_text("utf-8") if OUTPUT_FILE.exists() else ""
    if processed == existing:
        print("No changes — calendar is already up to date.")
        return 0

    OUTPUT_FILE.write_text(processed, encoding="utf-8")
    print(f"Written {OUTPUT_FILE} ({len(processed):,} bytes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
