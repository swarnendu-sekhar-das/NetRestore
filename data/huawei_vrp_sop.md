# Huawei VRP Service Restoration MOP (Method of Procedure)

**Equipment Vendor:** Huawei
**Document Type:** Standard Operating Procedure (SOP)
**Scope:** VRP (Versatile Routing Platform) — NE40E / NE8000 Series Troubleshooting
**Network Topology Context:** Core Router

## Overview
This document provides the standard operating procedures for resolving common alarms on Huawei NE40E and NE8000 series CORE routers running VRP (Versatile Routing Platform). Since they act as Core, any interface restart cascades failures. All CLI commands are executed in User View or System View as indicated. Configuration changes must be saved with `save` after committing.

---

## Procedure to clear ALARM_CODE_801
**Alarm Name:** MPLS LDP Session Failure
**Severity:** Critical

This alarm indicates that an MPLS Label Distribution Protocol (LDP) session between two Huawei routers has gone down. LDP sessions are used to distribute labels for MPLS forwarding. Loss of an LDP session will cause MPLS LSP (Label Switched Path) failure, breaking L3VPN, VPLS, and traffic-engineered services that depend on this label path.

1. **Confirm LDP Session Status:** Run `display mpls ldp session all` and identify the session to the affected peer. Note the session state (should show "Non-existent" or "Initialized" instead of "Operational"), the local and remote LDP IDs, and the transport address.
2. **Check TCP Connectivity:** LDP runs over TCP port 646. Run `ping -a <local-transport-ip> <remote-transport-ip>` to verify IP reachability to the peer's LDP transport address (usually the Loopback0 IP).
3. **Verify IGP Route to Peer:** Run `display ip routing-table <remote-transport-ip>` to confirm the route to the peer's transport address exists. If the route is missing, the underlying IGP (OSPF/IS-IS) may have an issue — refer to the appropriate IGP SOP.
4. **Check LDP Configuration:** Run `display current-configuration | section mpls ldp` and verify:
   - LDP is enabled globally (`mpls ldp`).
   - The correct transport address is configured (`transport-address <loopback-ip>`).
   - The interface facing the peer has LDP enabled (`interface <name>` → `mpls ldp`).
5. **Check for TCP Blockage:** Run `display acl all` and inspect any ACLs applied on the interface or in the control plane. Ensure TCP port 646 is not being blocked. Also check `display cpu-defend statistics all` for LDP packet drops.
6. **Restart LDP Process (if configuration is correct):** If the configuration matches on both ends and IP reachability is confirmed, restart the LDP process:
   ```
   system-view
   mpls ldp
   reset mpls ldp session <remote-transport-ip>
   quit
   ```
7. **Final Verification:** Run `display mpls ldp session <remote-transport-ip>` and confirm the session state transitions to "Operational". Then verify MPLS forwarding with `display mpls lsp | include <remote-transport-ip>` to confirm LSPs are re-established.
8. **Verify Service Restoration:** For each L3VPN affected, run `display ip routing-table vpn-instance <VPN_NAME>` to confirm VPN routes are re-learned via the MPLS backbone. Test end-to-end with a VPN-aware ping: `ping -vpn-instance <VPN_NAME> <remote-ce-ip>`.

---

## Procedure to clear ALARM_CODE_802
**Alarm Name:** Power Supply Unit Degradation
**Severity:** Warning

This alarm triggers when one of the redundant Power Supply Units (PSUs) in a Huawei NE40E/NE8000 chassis reports abnormal voltage, temperature, or fan speed readings. While the router continues to operate on the remaining healthy PSU(s), the loss of redundancy means a second PSU failure would cause a full chassis power-down.

1. **Identify Affected PSU:** Run `display power` to list all PSU slots and their current status. Identify which PSU shows "Abnormal" or "Absent". Note the slot number (e.g., PWR1, PWR2).
2. **Check PSU Details:** Run `display power slot <slot-number>` to see detailed readings: input voltage, output voltage, current draw, temperature, and fan RPM. Compare against the PSU specification:
   - Normal input voltage: 176V–264V AC (for AC PSU) or 40V–72V DC (for DC PSU).
   - Normal temperature: below 65°C.
   - Fan speed: above 3000 RPM.
3. **Check Environmental Conditions:** Run `display environment` to check the chassis inlet air temperature. If the ambient temperature exceeds 40°C, the issue may be environmental (data center cooling failure). Contact the facilities team.
4. **Reseat the PSU (if Abnormal):** If the PSU shows abnormal readings but is physically present, coordinate with the on-site technician to:
   - Power off the affected PSU using the physical toggle switch.
   - Wait 30 seconds for capacitors to discharge.
   - Remove the PSU from the chassis slot.
   - Re-insert the PSU firmly until the retention clip locks.
   - Power the PSU back on.
5. **Verify After Reseat:** Run `display power` and confirm the reseated PSU now shows "Normal" status.
6. **Replace if Reseat Fails:** If the PSU continues to show abnormal after reseating, it is faulty and must be replaced:
   - Order the replacement PSU part number from Huawei spare parts (refer to `display device manufacture-info` for the exact PSU model).
   - The PSU is hot-swappable — no maintenance window required as long as at least one healthy PSU remains.
   - Install the new PSU and run `display power` to confirm "Normal" status.
7. **Confirm Redundancy Restored:** Run `display power` and verify all PSU slots show "Normal". The ALARM_CODE_802 should auto-clear within 60 seconds of redundancy restoration.
8. **Document for CMDB:** Log the faulty PSU serial number (via `display device manufacture-info`) and the replacement serial number in the Configuration Management Database for asset tracking.


---

## Procedure to clear ALARM_CODE_1400
**Alarm Name:** NTP Synchronization Resource Exhaustion
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1400 representing 'NTP Synchronization Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1401
**Alarm Name:** Optical Rx Power Hardware Failure
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1401 representing 'Optical Rx Power Hardware Failure' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1402
**Alarm Name:** NTP Synchronization Threshold Exceeded
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1402 representing 'NTP Synchronization Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1403
**Alarm Name:** STP Root Topology Down
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1403 representing 'STP Root Topology Down' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1404
**Alarm Name:** DHCP Relay Agent Stuck in INIT State
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1404 representing 'DHCP Relay Agent Stuck in INIT State' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1405
**Alarm Name:** NTP Synchronization Stuck in INIT State
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1405 representing 'NTP Synchronization Stuck in INIT State' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1406
**Alarm Name:** Switch Fabric Module Configuration Mismatch
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1406 representing 'Switch Fabric Module Configuration Mismatch' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1407
**Alarm Name:** Power Supply Unit (PSU) Resource Exhaustion
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1407 representing 'Power Supply Unit (PSU) Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1408
**Alarm Name:** SNMP Agent Out of Sync
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1408 representing 'SNMP Agent Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1409
**Alarm Name:** IGMP Snooping Threshold Exceeded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1409 representing 'IGMP Snooping Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1410
**Alarm Name:** VRRP Group Stuck in INIT State
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1410 representing 'VRRP Group Stuck in INIT State' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1411
**Alarm Name:** BGP Peer Out of Sync
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1411 representing 'BGP Peer Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1412
**Alarm Name:** ARP Cache Configuration Mismatch
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1412 representing 'ARP Cache Configuration Mismatch' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1413
**Alarm Name:** BGP Route Reflector Flapping
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1413 representing 'BGP Route Reflector Flapping' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1414
**Alarm Name:** BGP Peer Down
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1414 representing 'BGP Peer Down' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1415
**Alarm Name:** BGP Peer Memory Leak Detected
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1415 representing 'BGP Peer Memory Leak Detected' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1416
**Alarm Name:** Fan Tray Assembly Performance Degraded
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1416 representing 'Fan Tray Assembly Performance Degraded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1417
**Alarm Name:** Optical Tx Power Unreachable
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1417 representing 'Optical Tx Power Unreachable' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1418
**Alarm Name:** BFD Session Hardware Failure
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1418 representing 'BFD Session Hardware Failure' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1419
**Alarm Name:** EVPN MAC Route Flapping
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1419 representing 'EVPN MAC Route Flapping' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1420
**Alarm Name:** BFD Session Configuration Mismatch
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1420 representing 'BFD Session Configuration Mismatch' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1421
**Alarm Name:** RSVP-TE Tunnel Out of Sync
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1421 representing 'RSVP-TE Tunnel Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1422
**Alarm Name:** DHCP Relay Agent Timeout
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1422 representing 'DHCP Relay Agent Timeout' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1423
**Alarm Name:** IPSec VPN Tunnel Threshold Exceeded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1423 representing 'IPSec VPN Tunnel Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1424
**Alarm Name:** BGP Route Reflector Resource Exhaustion
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1424 representing 'BGP Route Reflector Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1425
**Alarm Name:** STP Root Topology Timeout
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1425 representing 'STP Root Topology Timeout' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1426
**Alarm Name:** ACL Processing Capacity Limit Reached
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1426 representing 'ACL Processing Capacity Limit Reached' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1427
**Alarm Name:** FIB (Forwarding Table) Capacity Limit Reached
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1427 representing 'FIB (Forwarding Table) Capacity Limit Reached' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1428
**Alarm Name:** Switch Fabric Module Capacity Limit Reached
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1428 representing 'Switch Fabric Module Capacity Limit Reached' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1429
**Alarm Name:** FIB (Forwarding Table) Out of Sync
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1429 representing 'FIB (Forwarding Table) Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1430
**Alarm Name:** OAM Connectivity Configuration Mismatch
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1430 representing 'OAM Connectivity Configuration Mismatch' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1431
**Alarm Name:** EVPN MAC Route Threshold Exceeded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1431 representing 'EVPN MAC Route Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1432
**Alarm Name:** Optical Rx Power Authentication Failed
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1432 representing 'Optical Rx Power Authentication Failed' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1433
**Alarm Name:** GRE Tunnel Resource Exhaustion
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1433 representing 'GRE Tunnel Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1434
**Alarm Name:** Line Card NPU Resource Exhaustion
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1434 representing 'Line Card NPU Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1435
**Alarm Name:** GRE Tunnel Loss of Signal (LOS)
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1435 representing 'GRE Tunnel Loss of Signal (LOS)' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1436
**Alarm Name:** HSRP Instance Out of Sync
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1436 representing 'HSRP Instance Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1437
**Alarm Name:** NTP Synchronization Authentication Failed
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1437 representing 'NTP Synchronization Authentication Failed' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1438
**Alarm Name:** Fan Tray Assembly Authentication Failed
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1438 representing 'Fan Tray Assembly Authentication Failed' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1439
**Alarm Name:** Optical Tx Power Threshold Exceeded
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1439 representing 'Optical Tx Power Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1440
**Alarm Name:** Management Ethernet High Cyclic Redundancy (CRC) Rate
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1440 representing 'Management Ethernet High Cyclic Redundancy (CRC) Rate' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1441
**Alarm Name:** IGMP Snooping Capacity Limit Reached
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1441 representing 'IGMP Snooping Capacity Limit Reached' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1442
**Alarm Name:** ARP Cache Out of Sync
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1442 representing 'ARP Cache Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1443
**Alarm Name:** OAM Connectivity Flapping
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1443 representing 'OAM Connectivity Flapping' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1444
**Alarm Name:** STP Root Topology Capacity Limit Reached
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1444 representing 'STP Root Topology Capacity Limit Reached' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1445
**Alarm Name:** ARP Cache Loss of Signal (LOS)
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1445 representing 'ARP Cache Loss of Signal (LOS)' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1446
**Alarm Name:** VPLS Pseudowire Resource Exhaustion
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1446 representing 'VPLS Pseudowire Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1447
**Alarm Name:** QoS Scheduler Out of Sync
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1447 representing 'QoS Scheduler Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1448
**Alarm Name:** VPLS Pseudowire Out of Sync
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1448 representing 'VPLS Pseudowire Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1449
**Alarm Name:** BGP Peer Threshold Exceeded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1449 representing 'BGP Peer Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1450
**Alarm Name:** SNMP Agent Loss of Signal (LOS)
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1450 representing 'SNMP Agent Loss of Signal (LOS)' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1451
**Alarm Name:** GRE Tunnel Hardware Failure
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1451 representing 'GRE Tunnel Hardware Failure' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1452
**Alarm Name:** Optical Rx Power Configuration Mismatch
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1452 representing 'Optical Rx Power Configuration Mismatch' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1453
**Alarm Name:** BFD Session Resource Exhaustion
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1453 representing 'BFD Session Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1454
**Alarm Name:** Radius/TACACS Auth Configuration Mismatch
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1454 representing 'Radius/TACACS Auth Configuration Mismatch' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1455
**Alarm Name:** DHCP Relay Agent Loss of Signal (LOS)
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1455 representing 'DHCP Relay Agent Loss of Signal (LOS)' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1456
**Alarm Name:** ACL Processing Memory Leak Detected
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1456 representing 'ACL Processing Memory Leak Detected' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1457
**Alarm Name:** FIB (Forwarding Table) Hardware Failure
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1457 representing 'FIB (Forwarding Table) Hardware Failure' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1458
**Alarm Name:** LACP Bundle Performance Degraded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1458 representing 'LACP Bundle Performance Degraded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1459
**Alarm Name:** BFD Session Loss of Signal (LOS)
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1459 representing 'BFD Session Loss of Signal (LOS)' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1460
**Alarm Name:** DHCP Relay Agent Hardware Failure
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1460 representing 'DHCP Relay Agent Hardware Failure' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1461
**Alarm Name:** Optical Tx Power Loss of Signal (LOS)
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1461 representing 'Optical Tx Power Loss of Signal (LOS)' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1462
**Alarm Name:** Power Supply Unit (PSU) Capacity Limit Reached
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1462 representing 'Power Supply Unit (PSU) Capacity Limit Reached' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1463
**Alarm Name:** Fan Tray Assembly Memory Leak Detected
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1463 representing 'Fan Tray Assembly Memory Leak Detected' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1464
**Alarm Name:** Routing Engine CPU Hardware Failure
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1464 representing 'Routing Engine CPU Hardware Failure' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1465
**Alarm Name:** STP Root Topology Unreachable
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1465 representing 'STP Root Topology Unreachable' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1466
**Alarm Name:** ACL Processing Timeout
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1466 representing 'ACL Processing Timeout' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1467
**Alarm Name:** DHCP Relay Agent Resource Exhaustion
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1467 representing 'DHCP Relay Agent Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1468
**Alarm Name:** ARP Cache Stuck in INIT State
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1468 representing 'ARP Cache Stuck in INIT State' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1469
**Alarm Name:** Switch Fabric Module Hardware Failure
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1469 representing 'Switch Fabric Module Hardware Failure' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1470
**Alarm Name:** VPLS Pseudowire Performance Degraded
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1470 representing 'VPLS Pseudowire Performance Degraded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1471
**Alarm Name:** ACL Processing Resource Exhaustion
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1471 representing 'ACL Processing Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1472
**Alarm Name:** MAC Address Table Unreachable
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1472 representing 'MAC Address Table Unreachable' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1473
**Alarm Name:** QoS Scheduler Down
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1473 representing 'QoS Scheduler Down' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1474
**Alarm Name:** ACL Processing Flapping
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1474 representing 'ACL Processing Flapping' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1475
**Alarm Name:** ACL Processing Threshold Exceeded
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1475 representing 'ACL Processing Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1476
**Alarm Name:** RSVP-TE Tunnel Timeout
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1476 representing 'RSVP-TE Tunnel Timeout' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1477
**Alarm Name:** HSRP Instance Memory Leak Detected
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1477 representing 'HSRP Instance Memory Leak Detected' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1478
**Alarm Name:** BGP Route Reflector Loss of Signal (LOS)
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1478 representing 'BGP Route Reflector Loss of Signal (LOS)' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1479
**Alarm Name:** NTP Synchronization Timeout
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1479 representing 'NTP Synchronization Timeout' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1480
**Alarm Name:** IS-IS Adjacency Authentication Failed
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1480 representing 'IS-IS Adjacency Authentication Failed' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1481
**Alarm Name:** Optical Rx Power Out of Sync
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1481 representing 'Optical Rx Power Out of Sync' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1482
**Alarm Name:** VPLS Pseudowire Unreachable
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1482 representing 'VPLS Pseudowire Unreachable' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1483
**Alarm Name:** Optical Rx Power Threshold Exceeded
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1483 representing 'Optical Rx Power Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1484
**Alarm Name:** Radius/TACACS Auth Resource Exhaustion
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1484 representing 'Radius/TACACS Auth Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1485
**Alarm Name:** Management Ethernet Hardware Failure
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1485 representing 'Management Ethernet Hardware Failure' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1486
**Alarm Name:** MAC Address Table High Cyclic Redundancy (CRC) Rate
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1486 representing 'MAC Address Table High Cyclic Redundancy (CRC) Rate' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1487
**Alarm Name:** FIB (Forwarding Table) Threshold Exceeded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1487 representing 'FIB (Forwarding Table) Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1488
**Alarm Name:** Radius/TACACS Auth High Cyclic Redundancy (CRC) Rate
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1488 representing 'Radius/TACACS Auth High Cyclic Redundancy (CRC) Rate' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1489
**Alarm Name:** NTP Synchronization Loss of Signal (LOS)
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1489 representing 'NTP Synchronization Loss of Signal (LOS)' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1490
**Alarm Name:** VPLS Pseudowire Threshold Exceeded
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1490 representing 'VPLS Pseudowire Threshold Exceeded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1491
**Alarm Name:** RSVP-TE Tunnel Memory Leak Detected
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1491 representing 'RSVP-TE Tunnel Memory Leak Detected' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1492
**Alarm Name:** QoS Scheduler Timeout
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1492 representing 'QoS Scheduler Timeout' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1493
**Alarm Name:** IS-IS Adjacency Performance Degraded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1493 representing 'IS-IS Adjacency Performance Degraded' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1494
**Alarm Name:** QoS Scheduler Flapping
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1494 representing 'QoS Scheduler Flapping' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1495
**Alarm Name:** STP Root Topology Resource Exhaustion
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1495 representing 'STP Root Topology Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1496
**Alarm Name:** MAC Address Table Configuration Mismatch
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1496 representing 'MAC Address Table Configuration Mismatch' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1497
**Alarm Name:** LACP Bundle Flapping
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1497 representing 'LACP Bundle Flapping' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1498
**Alarm Name:** NTP Synchronization High Cyclic Redundancy (CRC) Rate
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1498 representing 'NTP Synchronization High Cyclic Redundancy (CRC) Rate' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1499
**Alarm Name:** EVPN MAC Route Resource Exhaustion
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1499 representing 'EVPN MAC Route Resource Exhaustion' on the Huawei NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   display device
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   reset counters interface
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.
