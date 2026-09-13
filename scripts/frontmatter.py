"""Tiny YAML-front-matter reader/writer for RegTrac editorial posts.

Deliberately dependency-free: the GitHub editorial workflow must run on a bare
ubuntu-latest runner without pip installs. Supports scalars, inline `[a, b]`
lists, and block lists (`key:` followed by `- item` lines).
"""
import re

_KEY = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")


def parse(path):
    """Return (meta, body) for a markdown file with optional front matter."""
    with open(path, encoding="utf-8") as f:
        return parse_text(f.read())


def parse_text(text):
    if not text.startswith("---"):
        return {}, text.strip() + "\n"
    lines = text.splitlines()
    end = None
    for i, ln in enumerate(lines[1:], start=1):
        if ln.strip() == "---":
            end = i
            break
    if end is None:
        return {}, text.strip() + "\n"
    meta, key = {}, None
    for raw in lines[1:end]:
        ln = raw.rstrip()
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        m = _KEY.match(ln.strip())
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                meta[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                meta[key] = []
            else:
                meta[key] = val.strip("\"'")
        elif ln.strip().startswith("- ") and key:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(ln.strip()[2:].strip().strip("\"'"))
    return meta, "\n".join(lines[end + 1:]).strip() + "\n"


def render(meta, body):
    """Serialise meta + body back to markdown with front matter."""
    out = ["---"]
    for k, v in meta.items():
        if isinstance(v, (list, tuple)):
            out.append(f"{k}:")
            out += [f"  - {item}" for item in v]
        else:
            out.append(f"{k}: {v}")
    out.append("---")
    out.append("")
    return "\n".join(out) + "\n" + body.strip() + "\n"
