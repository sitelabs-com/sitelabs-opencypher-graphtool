# sitelabs-opencypher-graphtool

**opencypher_graphtool**: an openCypher query engine for [graph-tool](https://graph-tool.skewed.de/)
graphs. The topology lives in graph-tool (in memory); node and relationship properties live in a
pluggable property store: in memory, or Apache Cassandra (one table per type). A pydantic data
model is the single source of truth for types, labels, tables and validation.

It is the engine shared by:

* **sitelabs-graph-database**: the graph database (write server, read replicas, failover,
  Cassandra), and
* **sitelabs-partitioned-graph**: an in-memory graph partitioned over many servers.

**Documentation:** [sitelabs-com.github.io/sitelabs-opencypher-graphtool](https://sitelabs-com.github.io/sitelabs-opencypher-graphtool/),
a site per release (`/0.2/`, ..., `/latest/`): the engine, its modules, its extension points, the
query catalogue and development. Its pages are in [`docs/`](docs) ([all documents](docs/index.md)).

## Install

graph-tool is not on PyPI: it comes from conda-forge, so the engine is installed into a conda
environment that already has it.

```bash
conda env create -f environment.yml          # python, graph-tool, then this package (editable)
conda activate opencypher-graphtool
python -m pytest                             # the tests (Cassandra ones skip without it)
```

In another project, with graph-tool in its environment:

```bash
pip install -e ../sitelabs-opencypher-graphtool[cassandra]        # while developing both side by side
pip install "opencypher-graphtool[cassandra] @ git+https://github.com/sitelabs-com/sitelabs-opencypher-graphtool.git@v0.2.1"
```

The `cassandra` extra adds the Cassandra driver (for `CassandraStore`); without it the engine runs
on `InMemoryStore` or a store of your own.

## Use

```python
from graph_tool import Graph
from opencypher_graphtool import RelationshipModel, Field, InMemoryStore, Models, NodeModel, opencypher


class Person(NodeModel):
    class Meta:
        type = "Person"
    name: str = Field(index=True)


class Knows(RelationshipModel):
    class Meta:
        type = "KNOWS"
        source, target = "Person", "Person"     # descriptive
    since: int | None = None


cy = opencypher(Graph(), InMemoryStore({}), models=Models([Person, Knows]))
cy.run("CREATE (:Person {name: 'Ann'})-[:KNOWS {since: 2020}]->(:Person {name: 'Bob'})")
print(cy.run("MATCH (a:Person)-[k:KNOWS]->(b) RETURN a.name AS a, b.name AS b, k.since AS s").data())
```

With Cassandra: `CassandraStore(session, "keyspace")` instead of `InMemoryStore({})`. More in
[`examples/`](examples).

**The language, by example:** [`docs/query-catalogue.md`](docs/query-catalogue.md) has a query for
each part of openCypher the engine supports, written against sitelabs-graph-database's sample graphs,
to paste into the UI query console (sitelabs-graph-ui). sitelabs-graph-database and
sitelabs-partitioned-graph keep a copy in their docs, as it is at the tag they pin; their tests fail
if it is edited there or left behind when the pin moves. Change it here, release a tag, move a
project's pin, then refresh its copy:

```bash
python scripts/install_catalogue.py ../sitelabs-graph-database                 # writes its docs/query-catalogue.md
python scripts/install_catalogue.py --check ../sitelabs-partitioned-graph      # is its copy current?
```

## The modules

The engine was one 6,400-line module (`opencypher_gt`); it is now a package of modules, in the
order they load:

| Module | What |
|---|---|
| `errors` | The exceptions (`OpenCypherError`, `ConstraintError`, lock errors, ...) |
| `locking` | One fair readers-writer lock per graph (`GraphLock`, `lock_of`) |
| `common` | The write transaction record, sentinels, core keys |
| `ids` | Element ids: UUIDs, natural-key ids (`bulk_node_id`, `stable_id`) |
| `lexer`, `ast_nodes`, `parser` | openCypher text to a syntax tree (`parse`) |
| `values` | Values, null logic, ordering, the built-in functions |
| `results` | `Node`, `Rel`, `Path`, `Result` |
| `models` | The data model: `Models`, `NodeModel`, `RelationshipModel`, `Field`, `Vector`, migrations |
| `schema` | Labels and types as bitmasks, UUID ids, attached to a graph-tool `Graph` |
| `elements` | Creating, changing and deleting nodes and relationships, with undo for transactions |
| `stores` | The property store interface (`PropertyStore`) and `InMemoryStore` |
| `cassandra_store` | `CassandraStore` (the `cassandra` extra) |
| `execution`, `graph_functions`, `matching`, `clauses` | The query runner, built up module by module: core, graph functions, `MATCH` (pattern expansion), the clauses |
| `procedures` | `CALL` procedures (PageRank, components, shortest paths, `vector.search`, ...) |
| `engine` | `OpenCypher`, `opencypher()`, `VerifyReport` |

**How the modules import each other.** Each module imports what it needs from the modules before it
at the top. The few names it needs from modules after it are bound by its `_link()` function, which
the package's `__init__` calls once every module is loaded. Import the public API from the package
(`from opencypher_graphtool import ...`); importing a module directly works too, since the package
loads first.

## Extension points

* **Property stores:** subclass `PropertyStore` (see `InMemoryStore` and `CassandraStore`): the
  columns of a type, fetching rows by id, writing them, and optional index search.
* **The runner and pattern expansion:** `OpenCypher.runner` is the class that runs a query (the
  `_Run` of `clauses`). A subclass can override its matching steps: `seed` (a pattern's start
  nodes), `filter_nodes`, `choose_start`, and `neighbourhood(nodes, direction, types, labels)`,
  which the matcher calls before it reads incident relationships (once per hop with the whole frontier, once
  per level of a variable-length pattern, once per BFS layer of shortestPath(), and in degree()). It
  does nothing on a local graph; sitelabs-partitioned-graph uses it to fetch each hop from the
  partitions that own the nodes.

## Tests

```bash
python -m pytest                              # everything
REQUIRE_CASSANDRA=1 python -m pytest          # fail instead of skipping without Cassandra (CI)
```

The Cassandra tests (`tests/integration/`) need Cassandra on `127.0.0.1:9042`, e.g.
`docker run -d -p 127.0.0.1:9042:9042 cassandra:5.0.9`. Another port: `CASSANDRA_PORT=19042`.

## Versions

Releases are git tags (`v0.1.0`, ...), each with an entry in [CHANGELOG.md](CHANGELOG.md): what
changed, and under **Upgrading** what to do. Before 1.0, a minor release (0.1 to 0.2) may change
the public API; a patch release doesn't. The projects using the engine pin a tag in their
requirements, and move to a new one deliberately.

To release: add the entry (move **Unreleased** under the new version), set `version` in
`pyproject.toml`, commit, `git tag -a v<version> -m "opencypher-graphtool <version>"`, push the tag,
and make a GitHub release for it with the entry as its notes.

**0.2.0** names graph elements nodes and relationships everywhere, as openCypher does, not
vertices and edges (graph-tool's own API, underneath, keeps its names). It changes the API:

| Was | Now |
|---|---|
| `VertexModel`, `EdgeModel` | `NodeModel`, `RelationshipModel` |
| `Schema(vertex_labels=, vertex_types=, edge_types=)`, `reg("vertex", ...)` | `Schema(node_labels=, node_types=, relationship_types=)`, `reg("node", ...)` |
| The kinds `"vertex"`, `"edge"` (`table_namer(kind, type)`, stores, models) | `"node"`, `"relationship"` |
| `reverse_vertex_ids` (the default reverse id table) | `reverse_node_ids` |

What was stored before still works: graphs saved with the old schema keys load, a keyspace that
already has `reverse_vertex_ids` keeps using it, and a MERGE or a file import makes the same ids
as before (`tests/test_compatibility.py`).

## Licence

Apache License 2.0 ([LICENSE.txt](LICENSE.txt)); third-party names in [NOTICES.txt](NOTICES.txt).
