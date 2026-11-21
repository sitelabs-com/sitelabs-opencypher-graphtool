<!-- menu -->
**Overview** · [Using it](extending.md) · [Development](development.md) · [References](index.md)

**Overview:** **Overview** · [The modules](modules.md)
<!-- /menu -->

# Overview

> **For:** developers using the engine in a project, and developers of it. **You'll find:** what
> the engine is, who uses it, installing it, a first query, and its versions.

**opencypher_graphtool** is an openCypher query engine for [graph-tool](https://graph-tool.skewed.de/)
graphs. The topology lives in graph-tool, in memory. Node and relationship properties live in a
pluggable property store: in memory, or Apache Cassandra (one table per type). A pydantic data
model is the single source of truth for types, labels, tables and validation.

It is the engine shared by:

* [sitelabs-graph-database](https://github.com/sitelabs-com/sitelabs-graph-database): the graph
  database (write server, read replicas, failover, Cassandra), and
* [sitelabs-partitioned-graph](https://github.com/sitelabs-com/sitelabs-partitioned-graph): an
  in-memory graph partitioned over many servers.

This site describes the engine itself. Each project's own documentation says how it serves the
engine: its endpoints, its console, its deployment, and what of openCypher it doesn't support.

## What's where

| Part | In short | Page |
|---|---|---|
| **The modules** | The package, module by module, and how they import each other | [The modules](modules.md) |
| **Extension points** | Property stores of your own, and the runner's matching steps | [Extension points](extending.md) |
| **The language, by example** | A query for each part of openCypher the engine supports | [Query catalogue](query-catalogue.md) |
| **Development** | The tests, the catalogue's copies, releasing, this site | [Development](development.md) |

## Installing

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

The `cassandra` extra adds the Cassandra driver (for `CassandraStore`). Without it the engine runs
on `InMemoryStore` or a store of your own.

## A first query

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

With Cassandra, use `CassandraStore(session, "keyspace")` instead of `InMemoryStore({})`. There are
more examples in [`examples/`](../examples).

## A query's limits

Two limits keep one query from taking a server's time or memory. Both are off by default; an
application that runs other people's queries sets them:

```python
cy.timeout = 30            # seconds: past it, QueryTimeout
cy.max_rows = 10_000_000   # rows the query may make in all: past it, QueryTooLarge
```

* **`timeout`** is checked as the query goes, in every loop that can run long: matching and
  expanding, UNWIND, aggregation, sorting, and every expression. A query stops close to its
  timeout, not when it is done.
* **`max_rows`** counts the rows the query's clauses make (MATCH, UNWIND and CALL), and refuses
  `range()` lists longer than it. A query's memory is mostly its rows, so this bounds it:
  `UNWIND range(1, 3000) AS a UNWIND range(1, 30000) AS b RETURN count(*)` stops at the limit
  instead of filling the memory. A query that needs more rows can count in parts, or narrow its
  MATCH.

Both are `OpenCypherError`s, so an application refusing bad queries refuses these too, and a
write that hits either is rolled back.

## Versions

Releases are git tags (`v0.1.0`, ...), each with an entry in [CHANGELOG.md](../CHANGELOG.md): what
changed, and under **Upgrading** what to do. Before 1.0, a minor release (0.1 to 0.2) may change
the public API; a patch release doesn't. The projects using the engine pin a tag in their
requirements, and move to a new one deliberately.

This site has one version per release (`/0.2/`, ...), and `/latest/`: a project links to the
release it pins.

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
