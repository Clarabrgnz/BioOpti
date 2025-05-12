#!/usr/bin/env python3
"""
Enhanced BACdive CLI: retrieves culture media recipes and displays them in a rich-formatted table.
Supports both CLI invocation and interactive prompt when no arguments provided.

Requires:
    pip install requests rich

Usage:
  # CLI mode:
  python media_optimizer.py "Bacillus subtilis"

  # Interactive mode (no args):
  python improved_bacdive_cli.py
"""
import re
import sys
import json
import argparse
import requests
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# ──────────────── YOUR CREDENTIALS ────────────────
BACDIVE_USER     = "pietroabonaldi@gmail.com"
BACDIVE_PASSWORD = "ppchempassword"
# ────────────────────────────────────────────────────

SSO_TOKEN_URL = "https://sso.dsmz.de/auth/realms/dsmz/protocol/openid-connect/token"
API_BASE_URL  = "https://api.bacdive.dsmz.de"

console = Console()


def get_bearer_token():
    """Authenticate via DSMZ SSO and return a Bearer access token."""
    data = {
        "grant_type": "password",
        "client_id":  "api.bacdive.public",
        "username":   BACDIVE_USER,
        "password":   BACDIVE_PASSWORD,
        "scope":      "openid"
    }
    resp = requests.post(SSO_TOKEN_URL, data=data)
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("No access_token in SSO response")
    return token


def get_headers():
    """Construct authorization headers."""
    token = get_bearer_token()
    return {"Authorization": f"Bearer {token}"}


def search_ids(query, headers):
    """Search by culture collection number or taxon name and return matching BACdive IDs."""
    if re.match(r"^[A-Za-z]{2,5}\s*\d+", query):
        url = f"{API_BASE_URL}/culturecollectionno/{query}"
    else:
        parts = query.split()
        if len(parts) < 2:
            raise ValueError("Please enter at least genus and species.")
        genus, species = parts[0], parts[1]
        url = f"{API_BASE_URL}/taxon/{genus}/{species}"

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    ids = []
    for entry in results:
        if isinstance(entry, dict):
            ids.append(entry.get("bacdive_id") or entry.get("id"))
        elif isinstance(entry, int):
            ids.append(entry)
    return ids


def fetch_strain(bd_id, headers):
    """Fetch full strain data for a given BACdive ID."""
    resp = requests.get(f"{API_BASE_URL}/fetch/{bd_id}", headers=headers)
    resp.raise_for_status()
    raw = resp.json().get("results", {})
    if isinstance(raw, dict):
        return next(iter(raw.values()))
    elif isinstance(raw, list):
        return raw[0] if raw else {}
    return {}



def extract_media(strain):
    """Extract media composition entries from strain data."""
    cgc = strain.get("Culture and growth conditions", {})
    media = cgc.get("culture medium", None)
    if not media:
        return []
    return media if isinstance(media, list) else [media]


def extract_temperature(strain):
    """Extract the best temperature (°C) from Culture and growth conditions."""
    cgc = strain.get("Culture and growth conditions", {})
    if not cgc:
        return "-"

    # 1) Gather all sub-entries under any key containing "temp"
    candidates = []
    for key, val in cgc.items():
        if re.search(r"temp", key, re.I):
            if isinstance(val, list):
                candidates.extend(val)
            else:
                candidates.append(val)

    if not candidates:
        # last-ditch: regex the whole JSON for "XX °C"
        # (ensure_ascii=False so “°” stays a real degree‐sign)
        blob = json.dumps(cgc, ensure_ascii=False)
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*°\s*[Cc]", blob)
        return f"{float(m.group(1)):g}°C" if m else "-"

    def parse_val(entry):
        # 1) explicit fields
        for fld in ("temperature", "temp", "value"):
            v = entry.get(fld)
            if not v:
                continue
            # numeric
            if isinstance(v, (int, float)):
                return float(v)
            s = str(v)
            # range “20–30 °C”
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:–|-)\s*([0-9]+(?:\.[0-9]+)?)", s)
            if m:
                return (float(m.group(1)) + float(m.group(2))) / 2
            # single number
            m2 = re.search(r"([0-9]+(?:\.[0-9]+)?)", s)
            if m2:
                return float(m2.group(1))
        # 2) free-text description
        desc = entry.get("description", "")
        m3 = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*°\s*[Cc]", desc)
        if m3:
            return float(m3.group(1))
        return None

    # 2) prefer "optimum" in either test_type or type
    for entry in candidates:
        kind = (entry.get("test_type") or entry.get("type") or "").lower()
        if "optimum" in kind:
            val = parse_val(entry)
            if val is not None:
                return f"{val:g}°C"

    # 3) then any "growth"
    for entry in candidates:
        kind = (entry.get("test_type") or entry.get("type") or "").lower()
        if "growth" in kind:
            val = parse_val(entry)
            if val is not None:
                return f"{val:g}°C"

    # 4) first parsable
    for entry in candidates:
        val = parse_val(entry)
        if val is not None:
            return f"{val:g}°C"

    return "-"


def display_media_table(query, media_list, temperature):
    """Render media recipes in a formatted table."""
    table = Table(title=f"Media Recipes for '{query}'")
    table.add_column("Name", style="bold green")
    table.add_column("Growth observed", style="yellow")
    table.add_column("Composition", style="white")
    table.add_column("Link", style="cyan", overflow="fold")
    table.add_column("Temp (°C)", style="magenta")

    for m in media_list:
        
        table.add_row(
            m.get("name", "-"),
            m.get("growth", "-"),
            m.get("composition", "-"),
            m.get("link", "-"),
            temperature
        )

    console.print(table)


def run(query):
    """Core workflow: authenticate, search, fetch, extract, and display."""
    headers = get_headers()
    try:
        ids = search_ids(query, headers)
    except ValueError as e:
        # print literal “[red]Error:[/]” so the test can see it
        print(f"[red]Error:[/] {e}")
        sys.exit(1)

    if not ids:
        console.print(f"[red]No strains found for '{query}'.[/]")
        sys.exit(0)

    strain = fetch_strain(ids[0], headers)
    media_list  = extract_media(strain)
    temperature = extract_temperature(strain)

    if not media_list:
        console.print(f"[red]No medium info available for '{query}'.[/]")
        sys.exit(0)

    display_media_table(query, media_list, temperature)


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve and display culture media recipes from BACdive."
    )
    parser.add_argument(
        "query", nargs="?",
        help="Strain (e.g. 'Bacillus subtilis')"
    )
    # ignore unrecognized args (e.g. Jupyter's --f=… flag)
    args, _ = parser.parse_known_args()

    if args.query:
        query = args.query
    else:
        try:
            query = input("Enter strain (e.g. 'Bacillus subtilis'): ").strip()
        except EOFError:
            console.print("[red]No query provided. Exiting.[/]")
            sys.exit(1)
        if not query:
            console.print("[red]Empty query. Exiting.[/]")
            sys.exit(1)

    run(query)


if __name__ == "__main__":
    main()
