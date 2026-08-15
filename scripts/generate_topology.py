import json
import random
import os

def generate_topology():
    nodes = []
    
    # Vendors
    core_vendors = ['Nokia', 'Juniper']
    pe_vendors = ['Cisco', 'Ericsson']
    access_vendors = ['Huawei', 'Arista']
    
    # 15 locations for the 15 PE routers in Bangalore
    pe_locations = ['KOR', 'WFD', 'IND', 'MG', 'BTM', 'ELEC', 'HSR', 'MALL', 'JAY', 'BAS', 'YEL', 'HEB', 'MAR', 'WHI', 'KR']
    
    core_nodes = []
    pe_nodes = []
    access_nodes = []
    
    # Generate 2 Core Nodes
    for i in range(1, 3):
        node_id = f"BLR-CORE-{i:02d}"
        node = {
            "node_id": node_id,
            "role": "Core",
            "vendor": random.choice(core_vendors),
            "ip_address": f"10.0.0.{i}",
            "bgp_asn": 65000,
            "neighbors": []
        }
        nodes.append(node)
        core_nodes.append(node)
        
    # Generate 15 PE Nodes
    for i in range(1, 16):
        loc = pe_locations[i-1]
        node_id = f"{loc}-PE-{i:02d}"
        node = {
            "node_id": node_id,
            "role": "PE",
            "vendor": random.choice(pe_vendors),
            "ip_address": f"10.1.{i}.1",
            "bgp_asn": 65000 + i,
            "neighbors": []
        }
        nodes.append(node)
        pe_nodes.append(node)
        
    # Generate 83 Access Nodes
    for i in range(1, 84):
        parent_pe = random.choice(pe_nodes)
        pe_loc = parent_pe["node_id"].split("-")[0]
        node_id = f"{pe_loc}-ACC-{i:02d}"
        node = {
            "node_id": node_id,
            "role": "Access",
            "vendor": random.choice(access_vendors),
            "ip_address": f"10.2.{i}.1",
            "bgp_asn": None, # Access nodes typically don't run BGP
            "neighbors": []
        }
        nodes.append(node)
        access_nodes.append(node)
        
    # Build Connections (Edges)
    # Core to Core (Redundant Link)
    core_nodes[0]["neighbors"].append({
        "node_id": core_nodes[1]["node_id"],
        "local_interface": "HundredGigE0/0/0",
        "remote_interface": "HundredGigE0/0/0"
    })
    core_nodes[1]["neighbors"].append({
        "node_id": core_nodes[0]["node_id"],
        "local_interface": "HundredGigE0/0/0",
        "remote_interface": "HundredGigE0/0/0"
    })
    
    # PE to Core
    for pe in pe_nodes:
        # Connect to both cores for redundancy
        for core in core_nodes:
            pe_int = f"TenGigE0/1/{random.randint(1,10)}"
            core_int = f"TenGigE0/1/{random.randint(1,48)}"
            pe["neighbors"].append({
                "node_id": core["node_id"],
                "local_interface": pe_int,
                "remote_interface": core_int
            })
            core["neighbors"].append({
                "node_id": pe["node_id"],
                "local_interface": core_int,
                "remote_interface": pe_int
            })
        
    # Access to PE
    for acc in access_nodes:
        pe_loc = acc["node_id"].split("-")[0]
        parent_pe = next(pe for pe in pe_nodes if pe["node_id"].startswith(pe_loc))
        
        acc_int = "GigabitEthernet0/1"
        pe_int = f"GigabitEthernet0/{random.randint(11,48)}"
        
        acc["neighbors"].append({
            "node_id": parent_pe["node_id"],
            "local_interface": acc_int,
            "remote_interface": pe_int
        })
        parent_pe["neighbors"].append({
            "node_id": acc["node_id"],
            "local_interface": pe_int,
            "remote_interface": acc_int
        })
        
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'network_topology.json')
    with open(output_path, 'w') as f:
        json.dump({"network_topology": {"nodes": nodes}}, f, indent=4)
        
    print(f"Successfully generated {len(nodes)} nodes and saved to {output_path}")

if __name__ == "__main__":
    generate_topology()
