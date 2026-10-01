#!/usr/bin/env python3
"""Keep the organisation README's plugin tables in sync with the org.

For every repository in the Omarchy-plugin org that carries a valid
Omarchy plugin manifest.json, it rewrites the "The suite" table in README.md:

  * existing rows keep their hand-curated description/replaces text, but get
    the live version from the repo's manifest.json on the published default
    branch (so a released bump shows up automatically);
  * plugins that exist in the org but not in the table are appended, built
    from their manifest (version, omarchy.clonedFrom -> Replaces, description);
  * rows whose repo no longer exists in the org are removed.

Plugins missing from the "What these plugins reach out to" table get one row
with a neutral note ("Documented in the plugin README"); curate that cell by
hand afterwards - later runs preserve it.

Idempotent: README.md is left untouched when nothing changed.
Stdlib only (urllib/json/re), so it runs anywhere with Python 3 - no gh, no
node, no action helpers.
"""

import json
import os
import sys
import urllib.request

ORG = os.environ.get("ORG", "Omarchy-plugin")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
# Non-plugin repos in the org. Anything else without a manifest.json is
# skipped too, so this list rarely needs to grow.
EXCLUDE = {".github", "myles-omarchy-plugins"}
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
NEW_NETWORK_NOTE = "Documented in the plugin README"


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def gh_json(path):
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{ORG}-readme-sync",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def raw_text(owner, repo, branch, path):
    with urllib.request.urlopen(
        f"{RAW}/{owner}/{repo}/{branch}/{path}", timeout=30
    ) as r:
        return r.read().decode("utf-8")


def collect_plugins():
    """repo name -> manifest info for every plugin repo in the org."""
    plugins = {}
    repos = gh_json(f"/orgs/{ORG}/repos?per_page=100")
    for repo in repos:
        name = repo["name"]
        if name in EXCLUDE:
            continue
        try:
            manifest = json.loads(
                raw_text(ORG, name, repo["default_branch"], "manifest.json")
            )
        except Exception:
            continue  # no manifest.json -> not a plugin repo
        # Discover plugins by manifest shape rather than author-specific id
        # prefix. This keeps newly added plugins from other contributors in
        # the org visible in the README too, while skipping repos with
        # unrelated JSON manifests.
        if not (
            str(manifest.get("id", "")).strip()
            and str(manifest.get("version", "")).strip()
            and isinstance(manifest.get("entryPoints"), dict)
        ):
            continue
        plugins[name] = {
            "version": str(manifest.get("version", "")).strip(),
            "replaces": (manifest.get("omarchy") or {}).get("clonedFrom") or "",
            "description": (manifest.get("description") or "").strip(),
        }
    return plugins


def split_row(row):
    """'| a | b | c |' -> ['a', 'b', 'c'] (outer pipes ignored)."""
    return [c.strip() for c in row.strip().strip("|").split("|")]


def suite_rows(plugins, body):
    rows = []
    seen = set()
    for row in body:
        cells = split_row(row)
        if len(cells) != 4 or "](./" not in cells[0]:
            continue
        repo = cells[0].split("](./", 1)[1].rstrip(")")
        info = plugins.get(repo)
        if not info:
            continue  # repo vanished from the org -> drop the row
        cols = cells[:]
        cols[1] = info["version"]
        rows.append("| " + " | ".join(cols) + " |")
        seen.add(repo)
    for repo in sorted(set(plugins) - seen):
        info = plugins[repo]
        replaces = f"`{info['replaces']}`" if info["replaces"] else "\u2014"
        rows.append(
            f"| [{repo}](./{repo}) | {info['version']} | {replaces} | {info['description']} |"
        )
    return rows


def network_rows(plugins, body, covered):
    rows = [r for r in body if r.strip()]
    new = sorted(set(plugins) - {r for r in covered if r})
    for repo in new:
        rows.append(f"| `{repo}` | {NEW_NETWORK_NOTE} |")
    return rows


def find_table(lines, header):
    """Return (header_idx, rows_start, rows_end) for a markdown table."""
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith(header):
            header_idx = i
            break
    if header_idx is None:
        fail(f"cannot find table header: {header}")
    sep = header_idx + 1
    if sep >= len(lines) or not lines[sep].lstrip().startswith("| ---"):
        fail(f"table after {header} has no separator row")
    rows_end = sep + 1
    while rows_end < len(lines) and lines[rows_end].strip():
        rows_end += 1
    return header_idx, sep + 1, rows_end


def main():
    plugins = collect_plugins()
    if not plugins:
        fail("no plugin repos found; refusing to edit the README")

    with open(README, encoding="utf-8") as f:
        lines = f.read().splitlines()

    # --- The suite table -------------------------------------------------
    h_idx, r_start, r_end = find_table(lines, "| Plugin | Version | Replaces | What it does |")
    new_rows = suite_rows(plugins, lines[r_start:r_end])
    lines[r_start:r_end] = new_rows

    # --- "What these plugins reach out to" table -------------------------
    n_idx, n_start, n_end = find_table(lines, "| Plugin | Network |")
    covered = set()
    for row in lines[n_start:n_end]:
        cells = split_row(row)
        if cells:
            for name in cells[0].replace("`", "").split(","):
                covered.add(name.strip())
    new_net = network_rows(plugins, lines[n_start:n_end], covered)
    lines[n_start:n_end] = new_net

    out = "\n".join(lines) + "\n"
    if out == open(README, encoding="utf-8").read():
        print("README is up to date.")
        return

    old_text = open(README, encoding="utf-8").read()
    old_lines = old_text.splitlines()

    # Summarise what changed (before writing).
    old_suite = {}
    for line in old_lines:
        if "](./" in line and line.strip().startswith("| ["):
            cells = split_row(line)
            if len(cells) == 4:
                old_suite[cells[0].split("](./", 1)[1].rstrip(")")] = cells[1]
    print("README changes: ")
    for repo, info in sorted(plugins.items()):
        if repo in old_suite:
            if old_suite[repo] != info["version"]:
                print(f"  {repo}: {old_suite[repo]} -> {info['version']}")
        else:
            print(f"  added plugin: {repo} {info['version']}")
    for repo in sorted(set(old_suite) - set(plugins)):
        print(f"  removed plugin: {repo}")

    with open(README, "w", encoding="utf-8") as f:
        f.write(out)
    print("README.md updated.")


if __name__ == "__main__":
    main()
