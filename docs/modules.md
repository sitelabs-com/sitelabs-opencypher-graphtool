<!-- menu -->
**Overview** · [Using it](extending.md) · [Development](development.md) · [References](index.md)

**Overview:** [Overview](overview.md) · **The modules**
<!-- /menu -->

# The modules

> **For:** developers of the engine, and anyone reading its code. **You'll find:** each module of
> the package, in the order they load, and how they import each other.

The engine was one 6,400-line module (`opencypher_gt`). It is now a package of modules,
[`src/opencypher_graphtool/`](../src/opencypher_graphtool), listed here in the order they load:

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

## How the modules import each other

Each module imports what it needs from the modules before it, at the top. The few names it needs
from the modules after it are bound by its `_link()` function, which the package's `__init__`
calls once every module is loaded.

Import the public API from the package (`from opencypher_graphtool import ...`). Importing a
module directly works too, since the package loads first.

## The public API

The public API is what `opencypher_graphtool` exports (`OpenCypher`, the models and fields,
`Schema`, the stores, the errors), the openCypher the engine accepts, and the tables and ids it
writes: what a stored graph or keyspace needs to keep working. A change to any of these is a
**Changed** entry in [CHANGELOG.md](../CHANGELOG.md).
