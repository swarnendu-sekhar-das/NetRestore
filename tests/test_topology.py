import json
import tempfile
import unittest

from src.llm.topology import NetworkTopologyService


class NetworkTopologyServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(
            {
                "network_topology": {
                    "nodes": [
                        {"node_id": "A", "vendor": "Cisco", "role": "Core", "connected_to": ["B", "MISSING"]},
                        {"node_id": "B", "vendor": "Cisco", "role": "PE", "connected_to": ["A", "C"]},
                        {"node_id": "C", "vendor": "Cisco", "role": "Access", "connected_to": ["A"]},
                    ],
                    "rules": ["Static data is advisory."],
                }
            },
            self.temp_file,
        )
        self.temp_file.close()
        self.service = NetworkTopologyService(self.temp_file.name)

    def tearDown(self):
        import os
        os.unlink(self.temp_file.name)

    def test_bfs_returns_direct_indirect_paths_and_handles_cycles(self):
        traversal = self.service.get_impact_paths("A", max_hops=2)
        impacts = {item["node_id"]: item for item in traversal["impacted_nodes"]}

        self.assertEqual(impacts["B"]["hop_distance"], 1)
        self.assertEqual(impacts["B"]["path"], ["A", "B"])
        self.assertEqual(impacts["C"]["hop_distance"], 2)
        self.assertEqual(impacts["C"]["path"], ["A", "B", "C"])
        self.assertNotIn("A", impacts)

    def test_bfs_reports_missing_references_without_expanding_them(self):
        traversal = self.service.get_impact_paths("A", max_hops=2)
        missing = next(item for item in traversal["impacted_nodes"] if item["node_id"] == "MISSING")

        self.assertFalse(missing["resolved"])
        self.assertEqual(missing["hop_distance"], 1)
        self.assertEqual(missing["path"], ["A", "MISSING"])

    def test_unknown_node_returns_no_traversal(self):
        traversal = self.service.get_impact_paths("does-not-exist")
        self.assertIsNone(traversal["affected_node"])
        self.assertEqual(traversal["impacted_nodes"], [])

    def test_context_distinguishes_direct_and_indirect_reachability(self):
        context = self.service.get_topology_context("What is affected by A?", max_hops=2)

        self.assertIn("Direct dependencies (1 hop):", context)
        self.assertIn("Indirect/reachable dependencies (2..2 hops):", context)
        self.assertIn("Unresolved topology references: 1", context)
        self.assertIn("Static topology reachability (advisory", context)
