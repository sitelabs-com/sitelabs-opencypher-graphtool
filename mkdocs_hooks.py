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

"""MkDocs hooks (mkdocs.yml: hooks).

* Each page in docs/ starts with its own menu block, which `python tools/docs.py` writes for reading
  the docs on GitHub. On the MkDocs site the sidebar is the menu, so the block is left out.
* Links from the docs into the code (`../examples/`, `../README.md`) work on GitHub but aren't
  in the site, so they are pointed at the file on GitHub instead.
"""
import importlib.util
import posixpath
import re
from pathlib import Path

ROOT = Path(__file__).parent
REPO = "https://github.com/sitelabs-com/sitelabs-opencypher-graphtool"
BRANCH = "main"

_spec = importlib.util.spec_from_file_location("sitedocs", ROOT / "docs" / "sitedocs.py")
sitedocs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sitedocs)

_FENCE = re.compile(r"^(```|~~~).*?^\1[ \t]*$", re.S | re.M)   # fenced code blocks
_CODE = re.compile(r"`[^`\n]+`")                               # inline code
_LINK = re.compile(r"(\]\()([^)\s]+)(\))")                     # ](target)


def code_url(page: str, target: str) -> str | None:
    """The GitHub URL for a link from docs/<page> to a file outside docs/, else None."""
    if re.match(r"[a-z][a-z0-9+.-]*:|#|/", target, re.I):
        return None                                            # absolute, an anchor, or rooted
    path, _, anchor = target.partition("#")
    full = posixpath.normpath(posixpath.join("docs", posixpath.dirname(page), path))
    if full == "docs" or full.startswith("docs/") or full.startswith(".."):
        return None                                            # in the site, or outside the repo
    kind = "tree" if (ROOT / full).is_dir() else "blob"
    return f"{REPO}/{kind}/{BRANCH}/{full}" + (f"#{anchor}" if anchor else "")


def _rewrite(text: str, page: str) -> str:
    def link(m):
        url = code_url(page, m.group(2))
        return m.group(1) + url + m.group(3) if url else m.group(0)

    out, last = [], 0
    for m in re.finditer(f"{_FENCE.pattern}|{_CODE.pattern}", text, re.S | re.M):
        out += [_LINK.sub(link, text[last:m.start()]), m.group(0)]
        last = m.end()
    return "".join(out + [_LINK.sub(link, text[last:])])


def on_page_markdown(markdown, page, **kwargs):
    return _rewrite(sitedocs.strip_menu(markdown), page.file.src_uri)
