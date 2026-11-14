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

"""What 0.2.0 (node and relationship, not vertex and edge) must still read and make as before:
the same ids for a MERGE and a file import, graphs saved with the old schema keys, and a
Cassandra keyspace that already has the old reverse id table."""
from types import SimpleNamespace as NS

from graph_tool import Graph

from opencypher_graphtool import InMemoryStore, Schema, opencypher
from opencypher_graphtool.cassandra_store import LEGACY_REVERSE_ID_TABLE, REVERSE_ID_TABLE, CassandraStore
from opencypher_graphtool.ids import bulk_node_id

# made by v0.1.7 (vertex and edge in the ids' derivation), for the same statements
ANN_IMPORTED = "0b560b31-3163-53a4-97d0-44dd76fbdc90"
ANN_MERGED = "66df0bab-67d0-5287-8655-f48c77785b5c"
KNOWS_MERGED = "2f220c03-39d2-5747-89d1-0aab5b961bad"


def test_ids_are_the_same_as_before_the_rename():
    tables = {("node", "Person"): {}, ("relationship", "KNOWS"): {}}
    st = InMemoryStore(tables, indexed={k: set() for k in tables})
    cy = opencypher(Graph(), st, Schema(node_labels=["Person"], node_types=["Person"], relationship_types=["KNOWS"]))
    assert bulk_node_id("Person", "name", "Ann") == ANN_IMPORTED
    assert cy.run("MERGE (p:Person {name: 'Ann'}) RETURN id(p) AS i").value() == ANN_MERGED
    assert cy.run("MATCH (p:Person {name: 'Ann'}) MERGE (p)-[k:KNOWS {since: 2001}]->(q:Person {name: 'Bo'}) "
                  "RETURN id(k) AS i").value() == KNOWS_MERGED


def test_a_schema_saved_with_the_old_keys_loads():
    old = {"bits": 64, "vertex_labels": {"Person": 0}, "vertex_types": {"Person": 0}, "edge_types": {"KNOWS": 0},
           "edge_labels": {}}
    sc = Schema.from_dict(old)
    assert sc.reg("node", "label").all_names() == ["Person"] and sc.reg("node", "type").all_names() == ["Person"]
    assert sc.reg("relationship", "type").all_names() == ["KNOWS"]
    assert set(Schema.from_dict(sc.to_dict()).to_dict()) == set(sc.to_dict())      # and saves the new ones


def _session(*tables):
    return NS(cluster=NS(metadata=NS(keyspaces={"ks": NS(tables={t: None for t in tables})})))


def test_a_keyspace_with_the_old_reverse_table_keeps_it():
    assert CassandraStore(_session(LEGACY_REVERSE_ID_TABLE), "ks").reverse_table == LEGACY_REVERSE_ID_TABLE
    assert CassandraStore(_session(), "ks").reverse_table == REVERSE_ID_TABLE == "reverse_node_ids"
    assert CassandraStore(_session(LEGACY_REVERSE_ID_TABLE, REVERSE_ID_TABLE), "ks").reverse_table == REVERSE_ID_TABLE
    assert CassandraStore(_session(), "nope").reverse_table == REVERSE_ID_TABLE            # no keyspace yet
    assert CassandraStore(_session(LEGACY_REVERSE_ID_TABLE), "ks", reverse_table="mine").reverse_table == "mine"
