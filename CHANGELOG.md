# Changelog

Every release of opencypher-graphtool: a tag `v<version>`, and an entry here, newest first.
Versions follow [semantic versioning](https://semver.org/). Before 1.0, a minor release (0.1 to
0.2) may change the public API, said so under **Changed** with what to do under **Upgrading**; a
patch release only fixes or adds without changing it.

The public API is what `opencypher_graphtool` exports (`OpenCypher`, the models and fields,
`Schema`, the stores, the errors), the openCypher the engine accepts, and the tables and ids it
writes (what a stored graph or keyspace needs to keep working).

## [Unreleased]

### Added

- A documentation site, https://sitelabs-com.github.io/sitelabs-opencypher-graphtool/, one per
  release, as the other sitelabs projects have: `docs/` (overview, modules, extension points, the
  query catalogue, development), `mkdocs.yml`, and `.github/workflows/mkdocs.yml`, which publishes
  it to GitHub Pages with mike. `python tools/docs.py` writes each page's menu and the site's
  sidebar. The query catalogue gets no menu, so the projects' copies of it don't change.

### Changed

- The docs name the graph database's repository as `sitelabs-graph-database`.

## [0.2.0] - 2026-11-15

### Changed

- **Nodes and relationships,** as openCypher names them, everywhere in the API, the docs and the
  tests (graph-tool's own API underneath keeps its names): `VertexModel` / `EdgeModel` are
  `NodeModel` / `RelationshipModel`; `Schema` takes `node_labels`, `node_types` and
  `relationship_types`; the kinds are `"node"` and `"relationship"`.
- The project's links name the `sitelabs-com` GitHub account.

### Upgrading

- Rename the classes and `Schema`'s arguments in your code. What is stored keeps working: graphs
  saved with the old schema keys load, a keyspace with `reverse_vertex_ids` keeps using it (new
  ones get `reverse_node_ids`), and `MERGE` and the file import make the same ids as before
  (`tests/test_compatibility.py`).

## [0.1.7] - 2026-11-11

### Changed

- The query catalogue and the README call it the UI query console.

## [0.1.6] - 2026-11-09

### Changed

- The query catalogue (`docs/query-catalogue.md`) names no project that copies it, and a test
  checks it.

## [0.1.5] - 2026-11-08

### Added

- `scripts/install_catalogue.py` writes the query catalogue into a project, as it is at the tag the
  project pins, under a marker with the tag and the copy's sha256, which the projects' tests check.
- `tests/test_query_catalogue.py`: every query parses, the console's sections hold only reads and
  the writes section only writes, every parameter block is JSON.

### Changed

- The catalogue's code blocks are tagged `opencypher`.

## [0.1.4] - 2026-11-08

### Added

- `docs/query-catalogue.md`: 118 queries covering what the engine supports, against the karate
  club and citations sample graphs.

### Fixed

- `gt.shortestPath` with a config (`relationshipTypes`, `IN`, `BOTH`) returned the filtered view's
  edges, so returning the path, or `startNode()` / `endNode()` of its relationships, failed with
  "invalid edge descriptor". Each edge is now found again in the graph.

## [0.1.3] - 2026-11-04

### Added

- `OpenCypher.runner`, the class that runs a query, so a subclass can override its matching steps
  (`seed`, `filter_nodes`, `choose_start`).
- The `neighbourhood()` hook, called with the whole frontier before incident edges are read (once
  per hop, per level of a variable-length pattern, per BFS layer of `shortestPath()`, and in
  `degree()`), for a graph that is a cache of a remote one. It does nothing on a local graph.

### Changed

- Variable-length expansion is level-synchronous across all rows (one hook call per level); its
  results are unchanged.

## [0.1.2] - 2026-11-03

### Fixed

- Concurrent writes report each failure (`raise_on_first_error=False`), so the vector write
  back-off runs: the first refused write used to raise, which is why vector writes failed on
  Cassandra nodes with few cores. The CI workaround (`-XX:ActiveProcessorCount=8`) is gone; the
  integration tests take `CASSANDRA_PORT`.

## [0.1.1] - 2026-11-03

### Fixed

- Vector writes back off until the server's vector index accepts them: each retry halves the
  concurrency, down to one write at a time, and the log suggests a lower `vector_write_concurrency`
  (Cassandra 5.0's vector indexes refuse more simultaneous writes than about one per CPU core).

## [0.1.0] - 2026-11-03

### Added

- The openCypher engine as its own project, split out of sitelabs-graph-database into a package of
  modules (lexer, parser, planner and execution, models and schema, stores including Cassandra,
  graph functions, procedures), with its 103 tests. Gremlin's leftovers removed.

[Unreleased]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.1.7...v0.2.0
[0.1.7]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/sitelabs-com/sitelabs-opencypher-graphtool/releases/tag/v0.1.0
