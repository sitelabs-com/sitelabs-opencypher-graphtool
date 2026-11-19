<!-- menu -->
[Overview](overview.md) · [Using it](extending.md) · **Development** · [References](index.md)
<!-- /menu -->

# Development

> **For:** developers of the engine. **You'll find:** the tests, the query catalogue and its copies,
> releasing, and the documentation site.

## The tests

```bash
python -m pytest                              # everything
REQUIRE_CASSANDRA=1 python -m pytest          # fail instead of skipping without Cassandra (CI)
```

The Cassandra tests (`tests/integration/`) need Cassandra on `127.0.0.1:9042`, for example
`docker run -d -p 127.0.0.1:9042:9042 cassandra:5.0.9`. For another port, set
`CASSANDRA_PORT=19042`. CI (`.github/workflows/ci.yml`) runs them against a real Cassandra on every
push and pull request.

## The query catalogue and its copies

[The query catalogue](query-catalogue.md) has a query for each part of openCypher the engine
supports, written against sitelabs-graph-database's sample graphs, to paste into the UI query
console (sitelabs-graph-ui). `tests/test_query_catalogue.py` checks that every query parses, that
the console's sections hold only reads, and that every parameter block is JSON.

sitelabs-graph-database and sitelabs-partitioned-graph keep a copy in their docs, as it is at the
tag they pin. Their tests fail if the copy is edited there, or left behind when the pin moves.
Change it here, release a tag, move a project's pin, then refresh its copy:

```bash
python scripts/install_catalogue.py ../sitelabs-graph-database                 # writes its docs/query-catalogue.md
python scripts/install_catalogue.py --check ../sitelabs-partitioned-graph      # is its copy current?
```

The copy is word for word, so `docs/query-catalogue.md` has no menu at the top, unlike the other
pages (`NO_MENU` in `tools/docs.py`). It names none of the projects that copy it.

## Releasing

1. Add the release's entry to [CHANGELOG.md](../CHANGELOG.md) (move **Unreleased** under the new
   version), and set `version` in `pyproject.toml` (`0.3.0`).
2. Commit, then `git tag -a v0.3.0 -m "opencypher-graphtool 0.3.0"`, and push both. The tag
   publishes the release's documentation site.
3. Make a GitHub release for the tag, with the entry as its notes.
4. In each project, pin the new tag, refresh its copy of the query catalogue, and change its links
   to this site to the new release (`/sitelabs-opencypher-graphtool/0.3/`).

## The documentation site

`docs/` is published at https://sitelabs-com.github.io/sitelabs-opencypher-graphtool/, one site per
release, with [mike](https://github.com/jimporter/mike):

* `/0.2/`, `/0.3/` ...: each release's site, for the engine a project pins. Projects link to
  these.
* `/latest/`: the newest. The site's root sends browsers there.

`.github/workflows/mkdocs.yml` publishes the release in `pyproject.toml` on every push to `main` that
changes the docs, and on every tag. The menu at the top of each page and the sidebar come from
`GROUPS` in `tools/docs.py`:

```bash
python tools/docs.py                     # write the menus and mkdocs.yml's nav
python tools/docs.py --check             # change nothing; fail if a file is out of date
pip install -r requirements-docs.txt
mkdocs serve                             # the site at http://127.0.0.1:8000, as you edit
mkdocs build --strict                    # what the workflow builds, failing on a broken link
```
