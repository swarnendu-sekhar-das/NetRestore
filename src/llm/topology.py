import json
import os
from collections import deque
from typing import Any
import logging

logger = logging.getLogger("netrestore")


class NetworkTopologyService:
    """Load static topology data and provide bounded reachability context."""

    DEFAULT_MAX_HOPS = 2

    def __init__(self, topology_path: str = None):
        if not topology_path:
            topology_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data", "network_topology.json")
            )
        self.topology = self._load_topology(topology_path)
        self._nodes_by_id = {
            node["node_id"]: node
            for node in self.topology.get("nodes", [])
            if node.get("node_id")
        }
        self._nodes_by_id_lower = {
            node_id.lower(): node for node_id, node in self._nodes_by_id.items()
        }
        self._adjacency = {
            node_id: list(node.get("connected_to", []))
            for node_id, node in self._nodes_by_id.items()
        }

    def _load_topology(self, topology_path: str) -> dict:
        """Load the static topology JSON file."""
        if os.path.exists(topology_path):
            with open(topology_path, "r") as f:
                data = json.load(f)
            topology = data.get("network_topology", {})
            logger.info(f"Network topology loaded: {len(topology.get('nodes', []))} nodes.")
            return topology

        logger.warning("Warning: network_topology.json was not found. Topology context is disabled.")
        return {}

    def get_impact_paths(self, node_id: str, max_hops: int = DEFAULT_MAX_HOPS) -> dict[str, Any]:
        """Return bounded BFS reachability for an exact topology node."""
        if max_hops < 0:
            raise ValueError("max_hops must be zero or greater")

        start = self._nodes_by_id_lower.get(node_id.lower())
        if not start:
            return {
                "affected_node": None,
                "max_hops": max_hops,
                "impacted_nodes": [],
            }

        start_id = start["node_id"]
        visited = {start_id}
        queue = deque([(start_id, 0, [start_id])])
        impacted_nodes = []

        while queue:
            current_id, current_hops, path = queue.popleft()
            if current_hops >= max_hops:
                continue

            for neighbor_id in self._adjacency.get(current_id, []):
                if neighbor_id in visited:
                    continue

                visited.add(neighbor_id)
                hop_distance = current_hops + 1
                neighbor_path = path + [neighbor_id]
                neighbor = self._nodes_by_id.get(neighbor_id)
                impacted_nodes.append(
                    {
                        "node_id": neighbor_id,
                        "hop_distance": hop_distance,
                        "path": neighbor_path,
                        "resolved": neighbor is not None,
                        "role": neighbor.get("role") if neighbor else None,
                        "vendor": neighbor.get("vendor") if neighbor else None,
                    }
                )

                # Missing nodes cannot be expanded because their edges are unknown.
                if neighbor is not None and hop_distance < max_hops:
                    queue.append((neighbor_id, hop_distance, neighbor_path))

        return {
            "affected_node": start,
            "max_hops": max_hops,
            "impacted_nodes": impacted_nodes,
        }

    @staticmethod
    def _format_reachable_node(item: dict[str, Any]) -> str:
        if not item["resolved"]:
            return f"  • {item['node_id']} (unresolved topology reference)"

        role = item["role"] or "Unknown"
        vendor = item["vendor"] or "Unknown"
        path = " → ".join(item["path"])
        return f"  • {item['node_id']} | Role: {role} | Vendor: {vendor} | Path: {path}"

    def get_topology_context(
        self,
        query: str,
        filters: dict = None,
        max_hops: int = DEFAULT_MAX_HOPS,
    ) -> str:
        """Build static, bounded topology reachability context for a query."""
        if not self.topology:
            return ""

        query_lower = query.lower()
        specific_node = next(
            (
                node
                for node_id, node in self._nodes_by_id.items()
                if node_id.lower() in query_lower
            ),
            None,
        )

        if specific_node:
            traversal = self.get_impact_paths(specific_node["node_id"], max_hops=max_hops)
            direct = [item for item in traversal["impacted_nodes"] if item["hop_distance"] == 1]
            indirect = [item for item in traversal["impacted_nodes"] if item["hop_distance"] > 1]
            unresolved = [item for item in traversal["impacted_nodes"] if not item["resolved"]]

            parts = [
                "Static topology reachability (advisory; not confirmed live outage impact):",
                f"Affected Node: {specific_node['node_id']} | Role: {specific_node.get('role', 'Unknown')} | "
                f"Vendor: {specific_node.get('vendor', 'Unknown')}",
                f"Traversal depth: {traversal['max_hops']} hop(s)",
                "Direct dependencies (1 hop):",
            ]
            parts.extend(self._format_reachable_node(item) for item in direct if item["resolved"])
            if not any(item["resolved"] for item in direct):
                parts.append("  • None in the topology data")

            if traversal["max_hops"] > 1:
                parts.append(f"Indirect/reachable dependencies (2..{traversal['max_hops']} hops):")
                parts.extend(self._format_reachable_node(item) for item in indirect if item["resolved"])
                if not any(item["resolved"] for item in indirect):
                    parts.append("  • None in the topology data")

            if unresolved:
                parts.append(f"Unresolved topology references: {len(unresolved)}")
                parts.extend(self._format_reachable_node(item) for item in unresolved)
        else:
            # Use vendor-level context when the query does not name a node.
            vendor = None
            if filters and "equipment_vendor" in filters:
                vendor = filters["equipment_vendor"]
            else:
                for candidate in ["Nokia", "Cisco", "Juniper", "Ericsson", "Huawei", "Arista"]:
                    if candidate.lower() in query_lower:
                        vendor = candidate
                        break

            if not vendor:
                return ""

            relevant = [node for node in self._nodes_by_id.values() if node.get("vendor") == vendor]
            if not relevant:
                return ""

            parts = [
                f"Affected Vendor: {vendor} (vendor-level context only; no topology traversal without an exact node ID)",
            ]
            for node in relevant:
                role = node.get("role", "Unknown")
                connected = ", ".join(node.get("connected_to", [])) or "None"
                parts.append(f"  • Node: {node['node_id']} | Role: {role} | Connected to: {connected}")

        rules = self.topology.get("rules", [])
        if rules:
            parts.append("\nTopology interpretation rules:")
            parts.extend(f"  • {rule}" for rule in rules)

        return "\n".join(parts)
