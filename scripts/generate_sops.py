import os
import random
import shutil

VENDORS = {
    "Cisco": "../data/cisco_ios_xr_sop.md",
    "Nokia": "../data/nokia_router_mop.md",
    "Juniper": "../data/juniper_junos_sop.md",
    "Ericsson": "../data/ericsson_ipos_sop.md",
    "Huawei": "../data/huawei_vrp_sop.md"
}

COMPONENTS = [
    "BGP Peer", "OSPF Adjacency", "IS-IS Adjacency", "MPLS LDP Session", "RSVP-TE Tunnel", 
    "BFD Session", "LACP Bundle", "VRRP Group", "HSRP Instance", "STP Root Topology", 
    "Optical Rx Power", "Optical Tx Power", "Line Card NPU", "Switch Fabric Module", "Routing Engine CPU",
    "FIB (Forwarding Table)", "QoS Scheduler", "ACL Processing", "Power Supply Unit (PSU)", 
    "Fan Tray Assembly", "Management Ethernet", "SNMP Agent", "NTP Synchronization", 
    "Radius/TACACS Auth", "MAC Address Table", "ARP Cache", "DHCP Relay Agent", 
    "IPSec VPN Tunnel", "GRE Tunnel", "VPLS Pseudowire", "EVPN MAC Route", 
    "Multicast PIM Neighbor", "IGMP Snooping", "BGP Route Reflector", "OAM Connectivity"
]

CONDITIONS = [
    "Down", "Timeout", "Flapping", "Performance Degraded", "Resource Exhaustion", 
    "Configuration Mismatch", "Threshold Exceeded", "Hardware Failure", 
    "Loss of Signal (LOS)", "High Cyclic Redundancy (CRC) Rate", "Unreachable", 
    "Out of Sync", "Authentication Failed", "Capacity Limit Reached", 
    "Memory Leak Detected", "Stuck in INIT State"
]

SEVERITIES = ["Critical", "Major", "Minor", "Warning"]

commands_map = {
    "Cisco": "show running-config\nclear ip route *",
    "Nokia": "show router status\nclear router ospf",
    "Juniper": "show chassis hardware\nclear bgp neighbor",
    "Ericsson": "show system processes\nclear port hardware",
    "Huawei": "display device\nreset counters interface"
}

UNIQUE_ERRORS = [f"{comp} {cond}" for comp in COMPONENTS for cond in CONDITIONS]
random.shuffle(UNIQUE_ERRORS)

def generate_procedure(vendor, alarm_type, idx):
    alarm_code = 1000 + idx
    severity = random.choice(SEVERITIES)
    cmds = commands_map[vendor].split("\n")
    return f"""
---

## Procedure to clear ALARM_CODE_{alarm_code}
**Alarm Name:** {alarm_type}
**Severity:** {severity}

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code {alarm_code} representing '{alarm_type}' on the {vendor} NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   {cmds[0]}
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   {cmds[1]}
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.
"""

# Delete the data/generated folder as requested
if os.path.exists("../data/generated"):
    shutil.rmtree("../data/generated")

# Slice errors, 100 per vendor
global_count = 0
for vendor, path in VENDORS.items():
    if not os.path.exists(path):
        continue
        
    appended_content = "\n"
    for j in range(100):
        alarm_type = UNIQUE_ERRORS[global_count]
        appended_content += generate_procedure(vendor, alarm_type, global_count)
        global_count += 1
        
    with open(path, "a") as f:
        f.write(appended_content)
        
    print(f"Appended 100 unique procedures to {path}")
