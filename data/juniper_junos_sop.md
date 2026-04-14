# Juniper JunOS Service Restoration MOP (Method of Procedure)

**Equipment Vendor:** Juniper
**Document Type:** Standard Operating Procedure (SOP)
**Scope:** JunOS MX-Series / PTX-Series Router Troubleshooting
**Network Topology Context:** Provider Edge (PE) Router

## Overview
This document provides the standard operating procedures for resolving common alarms on Juniper Networks MX-Series and PTX-Series routers running JunOS as Provider Edge (PE) nodes. Always verify Customer SLA tags. All commands must be executed from the CLI operational mode unless otherwise stated. Configuration changes require `commit confirm 5` to auto-rollback if connectivity is lost.

---

## Procedure to clear ALARM_CODE_601
**Alarm Name:** IS-IS Adjacency Failure (MTU Mismatch)
**Severity:** Critical

This alarm triggers when an IS-IS adjacency between two Juniper routers fails to reach the UP state due to a Maximum Transmission Unit (MTU) mismatch on the interconnecting interface. IS-IS PDUs larger than the smallest MTU on the link will be silently discarded, preventing adjacency formation.

1. **Confirm Adjacency State:** Run `show isis adjacency` to verify the neighbor is in the INIT or DOWN state, not UP.
2. **Check IS-IS Interface Details:** Run `show isis interface <interface-name> detail` and note the reported MTU value under "PDU MTU size".
3. **Check Physical MTU:** Run `show interfaces <interface-name> | match MTU` to see the configured interface MTU (e.g., 9192 for jumbo frames or 1514 for standard Ethernet).
4. **Compare with Remote Router:** SSH to the remote peer and run the same `show interfaces` command. The IS-IS MTU must match on both ends. Common mismatch: one side has jumbo frames (9192) enabled and the other uses default (1514).
5. **Align the MTU:** On the side that needs to change, enter configuration mode:
   ```
   configure
   set interfaces <interface-name> mtu <CORRECT_MTU_VALUE>
   commit confirm 5
   ```
   **Warning:** Use `commit confirm 5` so the router will automatically rollback in 5 minutes if you lose connectivity due to the change.
6. **Confirm and Finalize:** Once the IS-IS adjacency comes up (visible via `show isis adjacency`), confirm the commit:
   ```
   commit
   ```
7. **Verify Routing Table:** Run `show route protocol isis` to verify IS-IS routes are being learned from the peer. Confirm end-to-end reachability with `ping <remote-loopback-ip> source <local-loopback-ip> size 8972 do-not-fragment` to validate jumbo MTU is working.

---

## Procedure to clear ALARM_CODE_602
**Alarm Name:** Routing Engine High CPU Utilization
**Severity:** Warning

This alarm fires when the Routing Engine (RE) CPU utilization exceeds 85% for more than 5 consecutive minutes. Sustained high CPU can cause protocol timeouts (BGP, OSPF, IS-IS), delayed CLI response, and potential traffic forwarding degradation.

1. **Check Overall CPU:** Run `show chassis routing-engine` to see current CPU utilization for both RE0 and RE1 (if dual-RE). Note the "CPU utilization" percentages for User, System, and Interrupt.
2. **Identify Top Processes:** Run `show system processes extensive | match "PID|%CPU" | head 20` to list the top CPU-consuming processes. Common culprits include `rpd` (routing protocol daemon), `dfwd` (firewall daemon), or `snmpd`.
3. **Check for Route Churn:** If `rpd` is the top consumer, run `show route summary` and compare the total route count against the baseline. A route leak or flapping peer can cause massive churn. Run `show bgp summary | match Estab` to identify any peers that are flapping.
4. **Check SNMP Polling:** If `snmpd` is the culprit, a misconfigured NMS (Network Management System) may be polling too aggressively. Run `show snmp statistics` and check the "Get-request" counter rate. Contact the NMS team to reduce polling frequency to no less than 300-second intervals.
5. **Check for DDoS Protection Events:** Run `show ddos-protection protocols statistics terse` to see if the control plane is being hit by a traffic storm (e.g., ARP, ICMP, or TTL-expired packets).
6. **Mitigate if DDoS Detected:** If a specific protocol is exceeding its policer, increase the policer bandwidth temporarily:
   ```
   configure
   set system ddos-protection protocols <protocol-name> aggregate bandwidth <new-value>
   commit confirm 5
   ```
7. **Monitor Recovery:** Run `show chassis routing-engine` every 60 seconds for 5 minutes and confirm CPU returns below 70%. If CPU remains elevated, capture a diagnostic snapshot:
   ```
   request system diagnostics running-config-check
   file archive compress source /var/log/ destination /var/tmp/cpu-diag.tgz
   ```
   Escalate to Juniper JTAC with the diagnostic archive attached.


---

## Procedure to clear ALARM_CODE_1200
**Alarm Name:** Radius/TACACS Auth Stuck in INIT State
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1200 representing 'Radius/TACACS Auth Stuck in INIT State' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1201
**Alarm Name:** BFD Session Out of Sync
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1201 representing 'BFD Session Out of Sync' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1202
**Alarm Name:** RSVP-TE Tunnel Stuck in INIT State
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1202 representing 'RSVP-TE Tunnel Stuck in INIT State' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1203
**Alarm Name:** EVPN MAC Route Capacity Limit Reached
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1203 representing 'EVPN MAC Route Capacity Limit Reached' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1204
**Alarm Name:** FIB (Forwarding Table) Stuck in INIT State
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1204 representing 'FIB (Forwarding Table) Stuck in INIT State' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1205
**Alarm Name:** Multicast PIM Neighbor Flapping
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1205 representing 'Multicast PIM Neighbor Flapping' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1206
**Alarm Name:** DHCP Relay Agent Configuration Mismatch
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1206 representing 'DHCP Relay Agent Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1207
**Alarm Name:** BFD Session Performance Degraded
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1207 representing 'BFD Session Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1208
**Alarm Name:** BGP Route Reflector Authentication Failed
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1208 representing 'BGP Route Reflector Authentication Failed' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1209
**Alarm Name:** VPLS Pseudowire Authentication Failed
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1209 representing 'VPLS Pseudowire Authentication Failed' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1210
**Alarm Name:** HSRP Instance Capacity Limit Reached
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1210 representing 'HSRP Instance Capacity Limit Reached' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1211
**Alarm Name:** GRE Tunnel Configuration Mismatch
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1211 representing 'GRE Tunnel Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1212
**Alarm Name:** IGMP Snooping High Cyclic Redundancy (CRC) Rate
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1212 representing 'IGMP Snooping High Cyclic Redundancy (CRC) Rate' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1213
**Alarm Name:** FIB (Forwarding Table) Configuration Mismatch
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1213 representing 'FIB (Forwarding Table) Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1214
**Alarm Name:** Line Card NPU Configuration Mismatch
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1214 representing 'Line Card NPU Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1215
**Alarm Name:** Multicast PIM Neighbor Configuration Mismatch
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1215 representing 'Multicast PIM Neighbor Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1216
**Alarm Name:** Switch Fabric Module Timeout
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1216 representing 'Switch Fabric Module Timeout' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1217
**Alarm Name:** HSRP Instance Down
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1217 representing 'HSRP Instance Down' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1218
**Alarm Name:** Radius/TACACS Auth Unreachable
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1218 representing 'Radius/TACACS Auth Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1219
**Alarm Name:** MPLS LDP Session Threshold Exceeded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1219 representing 'MPLS LDP Session Threshold Exceeded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1220
**Alarm Name:** Line Card NPU Memory Leak Detected
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1220 representing 'Line Card NPU Memory Leak Detected' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1221
**Alarm Name:** FIB (Forwarding Table) Authentication Failed
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1221 representing 'FIB (Forwarding Table) Authentication Failed' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1222
**Alarm Name:** VRRP Group Resource Exhaustion
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1222 representing 'VRRP Group Resource Exhaustion' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1223
**Alarm Name:** QoS Scheduler Authentication Failed
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1223 representing 'QoS Scheduler Authentication Failed' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1224
**Alarm Name:** Line Card NPU Performance Degraded
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1224 representing 'Line Card NPU Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1225
**Alarm Name:** Management Ethernet Stuck in INIT State
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1225 representing 'Management Ethernet Stuck in INIT State' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1226
**Alarm Name:** OSPF Adjacency Loss of Signal (LOS)
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1226 representing 'OSPF Adjacency Loss of Signal (LOS)' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1227
**Alarm Name:** ARP Cache Unreachable
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1227 representing 'ARP Cache Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1228
**Alarm Name:** QoS Scheduler Unreachable
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1228 representing 'QoS Scheduler Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1229
**Alarm Name:** EVPN MAC Route Down
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1229 representing 'EVPN MAC Route Down' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1230
**Alarm Name:** HSRP Instance Timeout
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1230 representing 'HSRP Instance Timeout' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1231
**Alarm Name:** Switch Fabric Module Unreachable
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1231 representing 'Switch Fabric Module Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1232
**Alarm Name:** RSVP-TE Tunnel Loss of Signal (LOS)
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1232 representing 'RSVP-TE Tunnel Loss of Signal (LOS)' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1233
**Alarm Name:** VRRP Group Timeout
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1233 representing 'VRRP Group Timeout' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1234
**Alarm Name:** Management Ethernet Unreachable
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1234 representing 'Management Ethernet Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1235
**Alarm Name:** Optical Rx Power Unreachable
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1235 representing 'Optical Rx Power Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1236
**Alarm Name:** IGMP Snooping Resource Exhaustion
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1236 representing 'IGMP Snooping Resource Exhaustion' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1237
**Alarm Name:** Optical Tx Power Memory Leak Detected
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1237 representing 'Optical Tx Power Memory Leak Detected' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1238
**Alarm Name:** Fan Tray Assembly Capacity Limit Reached
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1238 representing 'Fan Tray Assembly Capacity Limit Reached' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1239
**Alarm Name:** OSPF Adjacency Threshold Exceeded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1239 representing 'OSPF Adjacency Threshold Exceeded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1240
**Alarm Name:** SNMP Agent Timeout
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1240 representing 'SNMP Agent Timeout' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1241
**Alarm Name:** IGMP Snooping Flapping
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1241 representing 'IGMP Snooping Flapping' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1242
**Alarm Name:** OAM Connectivity Loss of Signal (LOS)
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1242 representing 'OAM Connectivity Loss of Signal (LOS)' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1243
**Alarm Name:** HSRP Instance Hardware Failure
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1243 representing 'HSRP Instance Hardware Failure' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1244
**Alarm Name:** IS-IS Adjacency High Cyclic Redundancy (CRC) Rate
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1244 representing 'IS-IS Adjacency High Cyclic Redundancy (CRC) Rate' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1245
**Alarm Name:** Line Card NPU Flapping
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1245 representing 'Line Card NPU Flapping' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1246
**Alarm Name:** Line Card NPU Timeout
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1246 representing 'Line Card NPU Timeout' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1247
**Alarm Name:** VRRP Group Performance Degraded
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1247 representing 'VRRP Group Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1248
**Alarm Name:** Optical Tx Power Authentication Failed
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1248 representing 'Optical Tx Power Authentication Failed' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1249
**Alarm Name:** Switch Fabric Module Flapping
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1249 representing 'Switch Fabric Module Flapping' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1250
**Alarm Name:** GRE Tunnel Memory Leak Detected
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1250 representing 'GRE Tunnel Memory Leak Detected' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1251
**Alarm Name:** ACL Processing Unreachable
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1251 representing 'ACL Processing Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1252
**Alarm Name:** VRRP Group Down
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1252 representing 'VRRP Group Down' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1253
**Alarm Name:** STP Root Topology Flapping
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1253 representing 'STP Root Topology Flapping' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1254
**Alarm Name:** FIB (Forwarding Table) Flapping
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1254 representing 'FIB (Forwarding Table) Flapping' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1255
**Alarm Name:** Multicast PIM Neighbor Out of Sync
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1255 representing 'Multicast PIM Neighbor Out of Sync' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1256
**Alarm Name:** VPLS Pseudowire Down
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1256 representing 'VPLS Pseudowire Down' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1257
**Alarm Name:** RSVP-TE Tunnel Configuration Mismatch
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1257 representing 'RSVP-TE Tunnel Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1258
**Alarm Name:** DHCP Relay Agent Performance Degraded
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1258 representing 'DHCP Relay Agent Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1259
**Alarm Name:** Optical Tx Power Flapping
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1259 representing 'Optical Tx Power Flapping' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1260
**Alarm Name:** Power Supply Unit (PSU) Threshold Exceeded
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1260 representing 'Power Supply Unit (PSU) Threshold Exceeded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1261
**Alarm Name:** ACL Processing Configuration Mismatch
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1261 representing 'ACL Processing Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1262
**Alarm Name:** GRE Tunnel High Cyclic Redundancy (CRC) Rate
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1262 representing 'GRE Tunnel High Cyclic Redundancy (CRC) Rate' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1263
**Alarm Name:** IGMP Snooping Out of Sync
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1263 representing 'IGMP Snooping Out of Sync' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1264
**Alarm Name:** IPSec VPN Tunnel Timeout
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1264 representing 'IPSec VPN Tunnel Timeout' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1265
**Alarm Name:** BGP Route Reflector Memory Leak Detected
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1265 representing 'BGP Route Reflector Memory Leak Detected' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1266
**Alarm Name:** Optical Tx Power Timeout
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1266 representing 'Optical Tx Power Timeout' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1267
**Alarm Name:** STP Root Topology High Cyclic Redundancy (CRC) Rate
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1267 representing 'STP Root Topology High Cyclic Redundancy (CRC) Rate' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1268
**Alarm Name:** Management Ethernet Performance Degraded
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1268 representing 'Management Ethernet Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1269
**Alarm Name:** BGP Peer Authentication Failed
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1269 representing 'BGP Peer Authentication Failed' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1270
**Alarm Name:** BGP Route Reflector Configuration Mismatch
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1270 representing 'BGP Route Reflector Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1271
**Alarm Name:** IPSec VPN Tunnel Configuration Mismatch
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1271 representing 'IPSec VPN Tunnel Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1272
**Alarm Name:** MAC Address Table Performance Degraded
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1272 representing 'MAC Address Table Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1273
**Alarm Name:** IS-IS Adjacency Memory Leak Detected
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1273 representing 'IS-IS Adjacency Memory Leak Detected' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1274
**Alarm Name:** STP Root Topology Performance Degraded
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1274 representing 'STP Root Topology Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1275
**Alarm Name:** NTP Synchronization Capacity Limit Reached
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1275 representing 'NTP Synchronization Capacity Limit Reached' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1276
**Alarm Name:** HSRP Instance Configuration Mismatch
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1276 representing 'HSRP Instance Configuration Mismatch' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1277
**Alarm Name:** MPLS LDP Session Authentication Failed
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1277 representing 'MPLS LDP Session Authentication Failed' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1278
**Alarm Name:** Switch Fabric Module Stuck in INIT State
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1278 representing 'Switch Fabric Module Stuck in INIT State' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1279
**Alarm Name:** BGP Route Reflector Unreachable
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1279 representing 'BGP Route Reflector Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1280
**Alarm Name:** VRRP Group Memory Leak Detected
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1280 representing 'VRRP Group Memory Leak Detected' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1281
**Alarm Name:** Multicast PIM Neighbor Timeout
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1281 representing 'Multicast PIM Neighbor Timeout' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1282
**Alarm Name:** IPSec VPN Tunnel Resource Exhaustion
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1282 representing 'IPSec VPN Tunnel Resource Exhaustion' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1283
**Alarm Name:** IS-IS Adjacency Flapping
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1283 representing 'IS-IS Adjacency Flapping' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1284
**Alarm Name:** ARP Cache Authentication Failed
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1284 representing 'ARP Cache Authentication Failed' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1285
**Alarm Name:** Radius/TACACS Auth Out of Sync
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1285 representing 'Radius/TACACS Auth Out of Sync' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1286
**Alarm Name:** EVPN MAC Route Hardware Failure
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1286 representing 'EVPN MAC Route Hardware Failure' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1287
**Alarm Name:** Radius/TACACS Auth Threshold Exceeded
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1287 representing 'Radius/TACACS Auth Threshold Exceeded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1288
**Alarm Name:** Management Ethernet Capacity Limit Reached
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1288 representing 'Management Ethernet Capacity Limit Reached' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1289
**Alarm Name:** GRE Tunnel Stuck in INIT State
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1289 representing 'GRE Tunnel Stuck in INIT State' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1290
**Alarm Name:** SNMP Agent Unreachable
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1290 representing 'SNMP Agent Unreachable' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1291
**Alarm Name:** ARP Cache Hardware Failure
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1291 representing 'ARP Cache Hardware Failure' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1292
**Alarm Name:** DHCP Relay Agent Down
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1292 representing 'DHCP Relay Agent Down' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1293
**Alarm Name:** Radius/TACACS Auth Performance Degraded
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1293 representing 'Radius/TACACS Auth Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1294
**Alarm Name:** LACP Bundle Out of Sync
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1294 representing 'LACP Bundle Out of Sync' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1295
**Alarm Name:** Management Ethernet Resource Exhaustion
**Severity:** Warning

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1295 representing 'Management Ethernet Resource Exhaustion' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1296
**Alarm Name:** Fan Tray Assembly Stuck in INIT State
**Severity:** Major

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1296 representing 'Fan Tray Assembly Stuck in INIT State' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1297
**Alarm Name:** RSVP-TE Tunnel Threshold Exceeded
**Severity:** Critical

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1297 representing 'RSVP-TE Tunnel Threshold Exceeded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1298
**Alarm Name:** Multicast PIM Neighbor Down
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1298 representing 'Multicast PIM Neighbor Down' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.

---

## Procedure to clear ALARM_CODE_1299
**Alarm Name:** FIB (Forwarding Table) Performance Degraded
**Severity:** Minor

This alarm represents a unique fault vector. Immediate validation is required to avoid SLA breaches.

1. **Acknowledge Alarm:** Confirm the alarm code 1299 representing 'FIB (Forwarding Table) Performance Degraded' on the Juniper NMS dashboard.
2. **Diagnostic Check:** Run the vendor-specific diagnostic check:
   ```
   show chassis hardware
   ```
3. **Restoration Execution:** Perform the restoration sequence below to reset the affected logic:
   ```
   clear bgp neighbor
   ```
4. **Post-Check Validation:** Verify the state has stabilized and clear the alarm administratively.
