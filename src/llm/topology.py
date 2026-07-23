import json
import os

class NetworkTopologyService:
    """
    Handles reading the network topology graph and building cascade context.
    Extracted to adhere to the Single Responsibility Principle.
    """
    def __init__(self, topology_path: str = None):
        if not topology_path:
            topology_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data", "network_topology.json")
            )
        self.topology = self._load_topology(topology_path)

    def _load_topology(self, topology_path: str) -> dict:
        """Load the network topology JSON file for cascade failure analysis."""
        if os.path.exists(topology_path):
            with open(topology_path, "r") as f:
                data = json.load(f)
            print(f"✅ Network topology loaded: {len(data.get('network_topology', {}).get('nodes', []))} nodes")
            return data.get("network_topology", {})
        else:
            print("⚠️  network_topology.json not found. Topology-aware reasoning disabled.")
            return {}

    def get_topology_context(self, query: str, filters: dict = None) -> str:
        """
        Build a topology context string for the given query.
        """
        if not self.topology:
            return ""

        nodes = self.topology.get("nodes", [])
        
        # 1. Exact Node-ID Matching
        specific_node = None
        for node in nodes:
            if node.get("node_id", "").lower() in query.lower():
                specific_node = node
                break
                
        if specific_node:
            relevant = [specific_node]
            vendor = specific_node.get("vendor", "Unknown")
            parts = [f"Affected Node: {specific_node['node_id']} (Vendor: {vendor})"]
        else:
            # 2. Fallback to Vendor Matching
            vendor = None
            if filters and "equipment_vendor" in filters:
                vendor = filters["equipment_vendor"]
            else:
                for v in ["Nokia", "Cisco", "Juniper", "Ericsson", "Huawei", "Arista"]:
                    if v.lower() in query.lower():
                        vendor = v
                        break
            
            if not vendor:
                return ""
                
            relevant = [n for n in nodes if n.get("vendor") == vendor]
            if not relevant:
                return ""
            
            parts = [f"Affected Vendor: {vendor} (Note: Specify exact node ID for precise topology context)"]

        # Build context string
        for node in relevant:
            role = node.get("role", "Unknown")
            connected = ", ".join(node.get("connected_to", []))
            parts.append(f"  • Node: {node['node_id']} | Role: {role} | Connected to: {connected}")

        # Add cascade rules
        rules = self.topology.get("rules", [])
        if rules:
            parts.append("\nCascade Failure Rules:")
            for rule in rules:
                parts.append(f"  • {rule}")

        return "\n".join(parts)
