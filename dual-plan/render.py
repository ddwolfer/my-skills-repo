#!/usr/bin/env python3
"""dual-plan render.py

Turn plan.md into plan.html using the skill's render template.

Usage:
    python render.py path/to/plan.md

Behavior:
    - Reads YAML-ish frontmatter from plan.md (title, version, status, slug, ...)
    - Strips frontmatter from the body that gets injected into the HTML
    - Substitutes <title>, masthead path, timestamp, and the embedded
      <script type="text/markdown"> block in the template
    - Writes plan.html next to plan.md
    - Auto-snapshot: if a prior plan.html exists with a different `version`
      in its embedded MD, the prior MD is copied to history/v<old>.md
      before this render overwrites it

Stdlib only — no external deps.
"""
from __future__ import annotations

import sys
import re
import html
from pathlib import Path
from datetime import datetime

# Make stdout UTF-8 so non-ASCII chars (e.g. middle dot, CJK) print cleanly
# on Windows consoles that default to cp950 / cp936.
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

SKILL_DIR = Path(__file__).parent.resolve()
TEMPLATE = SKILL_DIR / "templates" / "plan-render.html"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Pull `key: value` frontmatter (between --- markers) from MD.

    Returns (metadata_dict, body_without_frontmatter).
    Tiny YAML subset only: simple `key: value` lines, no nested structures.
    """
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', text, re.DOTALL)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if ':' in line:
            k, v = line.split(':', 1)
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            meta[k.strip()] = v
    return meta, body


def extract_embedded_md(html_text: str) -> str | None:
    """Pull the MD source out of an existing plan.html's script block."""
    m = re.search(
        r'<script type="text/markdown" id="plan-source">\s*\n(.*?)\n</script>',
        html_text, re.DOTALL
    )
    return m.group(1) if m else None


def safe_inject(body: str) -> str:
    """Escape only the sequences that would break the <script> tag.

    `</script>` inside a script body terminates it; replace with `<\\/script>`
    which still reads as `</script>` to markdown but doesn't end the tag.
    """
    return body.replace('</script>', '<\\/script>')


def render(plan_md_path_str: str) -> int:
    plan_md_path = Path(plan_md_path_str).resolve()
    plan_dir = plan_md_path.parent
    plan_html_path = plan_dir / 'plan.html'
    history_dir = plan_dir / 'history'

    if not TEMPLATE.exists():
        print(f"ERROR: template not found at {TEMPLATE}", file=sys.stderr)
        return 1
    if not plan_md_path.exists():
        print(f"ERROR: plan.md not found at {plan_md_path}", file=sys.stderr)
        return 1

    new_md = plan_md_path.read_text(encoding='utf-8')
    new_meta, new_body = parse_frontmatter(new_md)
    new_version = new_meta.get('version', '?')
    title = new_meta.get('title') or plan_md_path.stem
    slug = new_meta.get('slug') or plan_dir.name

    # ---- Auto-snapshot prior version ----
    snapshot_msg = ''
    if plan_html_path.exists():
        try:
            old_html = plan_html_path.read_text(encoding='utf-8')
            old_md = extract_embedded_md(old_html)
            if old_md:
                old_meta, _ = parse_frontmatter(old_md)
                old_version = old_meta.get('version')
                if (old_version and new_version != '?'
                        and old_version != new_version):
                    history_dir.mkdir(exist_ok=True)
                    snap = history_dir / f'v{old_version}.md'
                    if not snap.exists():
                        snap.write_text(old_md, encoding='utf-8')
                        snapshot_msg = f"  · snapshotted v{old_version} → history/v{old_version}.md"
        except Exception as e:
            print(f"  warn: snapshot skipped ({e})", file=sys.stderr)

    # ---- Render ----
    template = TEMPLATE.read_text(encoding='utf-8')
    now = datetime.now().strftime('%Y-%m-%d · %H:%M')
    rel_path_display = f"plans/{slug}/plan.md · v{new_version}"
    title_display = f"{title} — plan.md (v{new_version})"

    rendered = template

    # 1) <title>
    rendered = re.sub(
        r'<title>.*?</title>',
        '<title>' + html.escape(title_display) + '</title>',
        rendered
    )

    # 2) masthead path span (the one right after the dot)
    rendered = re.sub(
        r'(<div class="masthead-left">\s*<span class="dot"></span>\s*<span>)[^<]*(</span>)',
        lambda m: m.group(1) + html.escape(rel_path_display) + m.group(2),
        rendered, count=1
    )

    # 3) timestamp span
    rendered = re.sub(
        r'(<span class="stamp">)[^<]*(</span>)',
        lambda m: m.group(1) + now + m.group(2),
        rendered, count=1
    )

    # 4) embedded MD script block — inject body (frontmatter stripped)
    body_for_script = safe_inject(new_body).strip('\n')
    rendered = re.sub(
        r'(<script type="text/markdown" id="plan-source">\s*\n).*?(\n</script>)',
        lambda m: m.group(1) + body_for_script + m.group(2),
        rendered, flags=re.DOTALL, count=1
    )

    # 5) Top-of-file generation comment
    gen_comment = (
        f"<!--\n"
        f"  Generated by dual-plan render.py from plan.md\n"
        f"  Source: {plan_md_path}\n"
        f"  Rendered: {now} (v{new_version})\n"
        f"  Do not edit this file directly — re-render from plan.md.\n"
        f"-->\n"
    )
    if rendered.lstrip().startswith('<!--'):
        rendered = re.sub(
            r'^<!--.*?-->\n?',
            lambda _m: gen_comment,
            rendered, count=1, flags=re.DOTALL
        )
    else:
        rendered = gen_comment + rendered

    plan_html_path.write_text(rendered, encoding='utf-8')

    print(f"Rendered: {plan_html_path}")
    print(f"  v{new_version} · {now}{snapshot_msg}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1
    return render(sys.argv[1])


if __name__ == '__main__':
    sys.exit(main())
