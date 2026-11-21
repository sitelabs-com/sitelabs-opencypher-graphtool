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

"""OpenCypher.on_commit / apply_redo: the topology journal used for crash recovery and read replicas."""
import pytest
from graph_tool import Graph

from opencypher_graphtool import opencypher, Schema, InMemoryStore

VT = ["Person", "City"]
ET = ["KNOWS", "LIVES_IN"]


def make(graph=None, store=None):
    g = graph if graph is not None else Graph()
    store = store if store is not None else InMemoryStore(
        {("node", "Person"): {}, ("node", "City"): {}, ("relationship", "KNOWS"): {}, ("relationship", "LIVES_IN"): {}})
    cy = opencypher(g, store, Schema(node_types=VT, relationship_types=ET))
    return cy, store


def topology(cy):
    """Everything graph-tool holds, keyed by id (indices are not compared)."""
    rows = cy.run("MATCH (n) RETURN id(n) AS id, labels(n) AS labels").data()
    nodes = {r["id"]: sorted(r["labels"]) for r in rows}
    rels = cy.run("MATCH (a)-[r]->(b) RETURN id(r) AS id, type(r) AS t, id(a) AS a, id(b) AS b").data()
    return nodes, {r["id"]: (r["t"], r["a"], r["b"]) for r in rels}


def test_replaying_the_journal_rebuilds_the_same_topology():
    cy, store = make()
    snapshot = cy.graph.copy()                       # the "last saved graph file": empty
    journal = []
    cy.on_commit = lambda ops: journal.append(list(ops))

    cy.run("CREATE (:Person {name: 'Ann'})-[:KNOWS]->(:Person {name: 'Bob'})")
    cy.run("CREATE (:City {name: 'Oslo'})")
    cy.run("MATCH (p:Person {name: 'Ann'}), (c:City) CREATE (p)-[:LIVES_IN]->(c)")
    cy.run("MATCH (p:Person {name: 'Bob'}) SET p:Admin")
    cy.run("MATCH (:Person {name: 'Ann'})-[r:KNOWS]->() DELETE r")
    cy.run("MATCH (p:Person {name: 'Bob'}) DETACH DELETE p")
    cy.run("MATCH (n) RETURN count(n)")              # reads are not journaled
    assert len(journal) == 6

    replica, _ = make(snapshot, store)
    applied = replica.apply_redo([op for entry in journal for op in entry])
    assert applied == sum(len(e) for e in journal)
    assert topology(replica) == topology(cy)
    # the store was not touched by the replay, and properties still resolve through it
    assert replica.run("MATCH (p:Person)-[:LIVES_IN]->(c) RETURN p.name, c.name").data() == [
        {"p.name": "Ann", "c.name": "Oslo"}]


def test_a_failing_on_commit_rolls_the_query_back():
    cy, store = make()

    def boom(ops):
        raise RuntimeError("journal down")
    cy.on_commit = boom
    with pytest.raises(RuntimeError, match="journal down"):
        cy.run("CREATE (:Person {name: 'Ann'})")
    cy.on_commit = None
    assert cy.run("MATCH (n) RETURN count(n) AS c").value() == 0
    assert store.tables[("node", "Person")] == {}


def test_replay_is_idempotent():
    cy, store = make()
    snapshot = cy.graph.copy()
    ops = []
    cy.on_commit = ops.extend
    cy.run("CREATE (:Person {name: 'Ann'})-[:KNOWS]->(:Person {name: 'Bob'})")
    replica, _ = make(snapshot, store)
    assert replica.apply_redo(ops) == 3
    assert replica.apply_redo(ops) == 0
    assert topology(replica) == topology(cy)


def test_label_change_on_an_existing_node_is_journaled():
    cy, store = make()
    cy.run("CREATE (:Person {name: 'Ann'})")
    snapshot = cy.graph.copy()
    ops = []
    cy.on_commit = ops.extend
    cy.run("MATCH (p:Person) SET p:Admin:Owner REMOVE p:Owner")
    assert [op[0] for op in ops] == ["vl", "vl"]
    replica, _ = make(snapshot, store)
    replica.apply_redo(ops)
    assert topology(replica) == topology(cy)


def test_timeout_stops_a_runaway_query_and_rolls_back_a_write():
    from opencypher_graphtool import QueryTimeout
    cy, store = make()
    cy.run("UNWIND range(1, 12) AS i CREATE (:Person {name: toString(i)})")
    cy.run("MATCH (a:Person), (b:Person) WHERE a <> b CREATE (a)-[:KNOWS]->(b)")   # complete graph
    cy.timeout = 0.2
    with pytest.raises(QueryTimeout):
        cy.run("MATCH p = (:Person)-[:KNOWS*]->(:Person) RETURN count(p)")       # exponential
    before = cy.run("MATCH (n) RETURN count(n) AS c").value()
    with pytest.raises(QueryTimeout):
        cy.run("MATCH p = (a:Person)-[:KNOWS*]->(:Person) CREATE (:City {name: 'x'})")
    assert cy.run("MATCH (n) RETURN count(n) AS c").value() == before
    cy.timeout = None


def test_timeout_stops_a_query_that_only_unwinds():
    """UNWIND makes rows without evaluating anything per row: it checks the deadline itself, so a
    query of nested UNWINDs stops near its timeout, not when it is done (or out of memory)."""
    import time

    from opencypher_graphtool import QueryTimeout
    cy, _ = make()
    cy.timeout = 0.5
    t0 = time.monotonic()
    with pytest.raises(QueryTimeout):
        cy.run("UNWIND range(1, 3000) AS a UNWIND range(1, 30000) AS b RETURN count(*)")
    assert time.monotonic() - t0 < 5, "stopped long after its timeout"
    cy.timeout = None


def test_max_rows_stops_a_query_that_makes_too_many_rows_and_rolls_back_a_write():
    from opencypher_graphtool import OpenCypherError, QueryTooLarge
    cy, _ = make()
    cy.run("UNWIND range(1, 50) AS i CREATE (:Person {name: toString(i)})")
    cy.max_rows = 1000
    assert cy.run("UNWIND range(1, 500) AS i RETURN count(i) AS c").value() == 500        # under it
    assert cy.run("MATCH (p:Person) RETURN count(p) AS c").value() == 50
    with pytest.raises(QueryTooLarge, match="more than 1,000 rows"):
        cy.run("UNWIND range(1, 100) AS a UNWIND range(1, 100) AS b RETURN count(*)")    # 10,000 rows
    with pytest.raises(QueryTooLarge, match="more than 1,000 rows"):
        cy.run("MATCH (a:Person), (b:Person) RETURN count(*)")                           # 2,500 rows
    with pytest.raises(QueryTooLarge, match=r"range\(\) of 1,000,000 values"):
        cy.run("RETURN size(range(1, 1000000)) AS n")
    with pytest.raises(QueryTooLarge):
        cy.run("UNWIND range(1, 40) AS a UNWIND range(1, 40) AS b CREATE (:City {name: toString(a * 100 + b)})")
    assert cy.run("MATCH (c:City) RETURN count(c) AS c").value() == 0                      # rolled back
    assert issubclass(QueryTooLarge, OpenCypherError)
    cy.max_rows = None
    assert cy.run("UNWIND range(1, 100) AS a UNWIND range(1, 100) AS b RETURN count(*) AS c").value() == 10_000
