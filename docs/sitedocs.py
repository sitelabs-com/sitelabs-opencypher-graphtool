# Copyright 2026 Sitelabs.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""The documentation layout: its sections and the menu at the top of every page, and the
documentation site's sidebar (mkdocs.yml's nav), so the site and the menus always match.

* SECTIONS is the menu: each section and its overview page.
* The docs generator (`python tools/docs.py`) says which pages go in which section (its GROUPS), and
  calls with_menu() for each page and with_nav() for mkdocs.yml.
* mkdocs_hooks.py calls strip_menu(): on the site, the sidebar is the menu.
"""
from __future__ import annotations

import re

SECTIONS = [("Overview", "overview.md"), ("Using it", "extending.md"), ("Development", "development.md"),
            ("References", "index.md")]
START, END = "<!-- menu -->", "<!-- /menu -->"
MENU_BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n*", re.S)

Groups = dict[str, list[tuple[str, str]]]          # section -> [(file, title)], its overview first


def check_groups(groups: Groups) -> None:
    """The sections must be SECTIONS, in order, each starting with its overview page."""
    if list(groups) != [s for s, _ in SECTIONS]:
        raise SystemExit(f"the sections must be, in order: {', '.join(s for s, _ in SECTIONS)}")
    for section, overview in SECTIONS:
        if not groups[section] or groups[section][0][0] != overview:
            raise SystemExit(f"the {section} section must start with {overview}")


def menu(groups: Groups, current: str | None, prefix: str = "") -> str:
    """The menu at the top of docs/<current>: every section, its own one bold, then the pages of its
    own section (when it has more than one). prefix "docs/": as seen from the repository root."""
    check_groups(groups)
    here = next((s for s, pages in groups.items() if current in dict(pages)), None)
    lines = [" · ".join(f"**{s}**" if s == here else f"[{s}]({prefix}{page})" for s, page in SECTIONS)]
    if here and len(groups[here]) > 1:
        items = " · ".join(f"**{t}**" if f == current else f"[{t}]({prefix}{f})" for f, t in groups[here])
        lines.append(f"**{here}:** {items}")
    return f"{START}\n" + "\n\n".join(lines) + f"\n{END}\n\n"


def strip_menu(text: str) -> str:
    return MENU_BLOCK.sub("", text, count=1).lstrip("\n")


def with_menu(text: str, groups: Groups, current: str, prefix: str = "") -> str:
    return menu(groups, current, prefix) + strip_menu(text)


def pages(groups: Groups) -> list[str]:
    return [f for ps in groups.values() for f, _ in ps]


# -- the documentation site (mkdocs.yml) ------------------------------------------------------ #
NAV = "\nnav:\n"                                   # mkdocs.yml's nav: the last key, the generator's


def _yaml_key(title: str) -> str:
    """A title as a YAML key: quoted when it holds ": " or " #", or starts with a YAML indicator."""
    return f'"{title}"' if ": " in title or " #" in title or title[:1] in "-?:,[]{}#&*!|>'\"%@`" else title


def nav(groups: Groups) -> str:
    """The site's sidebar: the menu's sections and pages, in its order, as mkdocs.yml's nav."""
    check_groups(groups)
    return NAV.lstrip("\n") + "".join(
        f"  - {_yaml_key(section)}:\n" + "".join(f"      - {_yaml_key(t)}: {f}\n" for f, t in ps)
        for section, ps in groups.items())


def with_nav(config: str, groups: Groups) -> str:
    """mkdocs.yml with its nav (its last key, everything after `nav:`) written from the menu."""
    if NAV not in config:
        raise SystemExit("mkdocs.yml must end with its nav: a line `nav:`, last")
    return config[:config.index(NAV)] + "\n" + nav(groups)
