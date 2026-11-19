<!-- menu -->
[Overview](overview.md) · **Using it** · [Development](development.md) · [References](index.md)

**Using it:** **Extension points** · [Query catalogue](query-catalogue.md)
<!-- /menu -->

# Extension points

> **For:** developers building on the engine. **You'll find:** writing a property store of your
> own, and changing how the runner matches patterns.

## Property stores

The topology is in graph-tool; the properties of nodes and relationships are in a property store.
The engine comes with two:

| Store | Where the properties are |
|---|---|
| `InMemoryStore({})` | In memory, in a dict |
| `CassandraStore(session, "keyspace")` | Apache Cassandra, one table per type (the `cassandra` extra) |

For another, subclass `PropertyStore`, from [`stores`](../src/opencypher_graphtool/stores.py). A
store provides the columns of a type, fetching rows by id, writing them, and, optionally, index
search. `InMemoryStore` ([`stores.py`](../src/opencypher_graphtool/stores.py)) and `CassandraStore`
([`cassandra_store.py`](../src/opencypher_graphtool/cassandra_store.py)) are the examples to follow.

## The runner and pattern expansion

`OpenCypher.runner` is the class that runs a query: the `_Run` of
[`clauses`](../src/opencypher_graphtool/clauses.py). A subclass can override its matching steps,
defined in [`matching`](../src/opencypher_graphtool/matching.py):

| Step | What it does |
|---|---|
| `seed(labels, eqs)` | A pattern's start nodes: the candidates for an unbound node, by id, store index, label mask or scan |
| `filter_nodes(cands, labels, eqs)` | Keeps the candidates having all `labels` and every equality, batching store reads |
| `choose_start(part, bound, hints)` | Which node of a pattern part to start matching from |
| `neighbourhood(nodes, direction, types, labels)` | The hook before the matcher reads incident relationships |

The matcher calls `neighbourhood`:

* once per hop, with the whole frontier;
* once per level of a variable-length pattern;
* once per BFS layer of `shortestPath()`;
* in `degree()`.

On a local graph it does nothing. sitelabs-partitioned-graph uses it to fetch each hop from the
partitions that own the nodes.
