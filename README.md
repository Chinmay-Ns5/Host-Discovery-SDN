# 🌐 Host Discovery Service in Software Defined Networking

**Course:** Computer Networks — SDN Lab (CN-ORANGE)  
**Name:** Chinmay N S  
**SRN:** PES2UG24AM047  
**Controller:** POX (OpenFlow 1.0)  
**Environment:** Ubuntu 24.04 · Mininet · Open vSwitch  

---

## 📌 Problem Statement

Implement an SDN-based **Host Discovery Service** using the POX OpenFlow controller and Mininet. The system must:

- Automatically detect hosts via `packet_in` events
- Maintain a **live host database** containing:
  - MAC Address
  - IP Address
  - Switch DPID
  - Port Number
- Operate with **zero pre-configuration** of host identities — all discovery is purely event-driven

---

## 🏗️ Topology

A **star topology** with one Open vSwitch (OVS) and four hosts:

```
        [POX Controller]
               |
           [s1 - OVS]
          /   |   |   \
        h1   h2  h3   h4
     10.0.0.1  .2  .3  .4
```

- Switch DPID: `0000000000000001`
- Hosts h1–h4 each connected on ports 1–4 respectively
- h4 starts **network-silent** (interface down) to simulate a dynamic join event

---

## ⚙️ Setup & Execution

### Prerequisites

```bash
# Install Mininet
sudo apt-get install mininet

# Install Open vSwitch
sudo apt-get install openvswitch-switch

# Clone POX controller
git clone https://github.com/noxrepo/pox.git ~/pox

# Clone this repository
git clone https://github.com/Chinmay-Ns5/Host-Discovery-SDN.git
cd Host-Discovery-SDN
```

### Running the Controller

```bash
# Terminal 1 — Start POX with the host discovery component
cd ~/pox
python3 pox.py log.level --DEBUG host_discovery
```

### Starting the Mininet Topology

```bash
# Terminal 2 — Launch the custom topology
sudo python3 topology.py
```

### Running Test Scenarios

```bash
# Inside Mininet CLI

# Scenario 1: Initial host discovery
mininet> pingall

# Scenario 2: Dynamic join — activate h4 at runtime
mininet> h4 ip link set h4-eth0 up
mininet> h4 ip addr add 10.0.0.4/8 dev h4-eth0
mininet> h4 ping -c 3 h1

# Targeted latency test
mininet> h1 ping -c 5 h2
```

### Verifying the Flow Table

```bash
# In a separate terminal
sudo ovs-ofctl dump-flows s1
```

---

## 📁 Repository Structure

```
Host-Discovery-SDN/
├── host_discovery.py      # POX controller component
├── topology.py            # Mininet topology definition
└── README.md              # This file
```

---

## 🔍 How It Works

### Controller Logic (`host_discovery.py`)

1. **Switch Connection** — On switch connect, the controller installs a **table-miss flow rule**:
   - `priority=1`, `match=all`, `action=CONTROLLER:65535`
   - This ensures every first packet from every host is forwarded to the controller

2. **`packet_in` Handling** — For every packet received:
   - Extracts **source MAC** from the Ethernet header
   - Extracts **source IP** from the ARP `protosrc` field or IPv4 `srcip`
   - Records **switch DPID** and **ingress port** from the OpenFlow event metadata
   - Adds a new entry to `host_db` (keyed by MAC) or updates an existing one

3. **IP Resolution** — Two-stage process:
   - Stage 1: MAC is recorded immediately on first frame
   - Stage 2: IP is resolved when ARP/IPv4 payload is parsed (often within the same `packet_in` burst)

4. **Duplicate Prevention** — Checks if MAC already exists in `host_db` before creating a new entry

5. **Packet-out Response** — Uses `OFPP_FLOOD` to ensure connectivity is maintained during discovery

### Match-Action Flow Rule Design

| Field | Value | Meaning |
|-------|-------|---------|
| `priority` | `1` | Lowest priority — fires only for unmatched packets |
| `match` | all packets | No specific match criteria |
| `action` | `CONTROLLER:65535` | Forward full packet to controller (`OFPP_CONTROLLER`) |

---

## 🧪 Test Scenarios

### Scenario 1 — Initial Host Discovery

**Trigger:** `pingall` executed in Mininet CLI  
**Expected behaviour:**
- Each of h1, h2, h3 triggers a `NEW HOST DETECTED` log entry
- Host database grows from 1 → 2 → 3 entries
- IP addresses resolved in the same `packet_in` burst

**Expected controller log:**
```
INFO:host_discovery:NEW HOST DETECTED
INFO:host_discovery:MAC: 00:00:00:00:00:01
INFO:host_discovery:IP: 10.0.0.1
INFO:host_discovery:DPID: 0000000000000001 PORT: 1
INFO:host_discovery:HOST DATABASE (3 host(s))
```

**Validation:** `pingall` shows `0% dropped (12/12 received)`

---

### Scenario 2 — Dynamic Host Join (h4)

**Trigger:** h4 interface brought up at runtime with IP assigned  
**Expected behaviour:**
- Controller has **zero prior knowledge** of h4
- On h4's first ping, `packet_in` fires and h4 is added to the database
- Database grows from 3 → 4 entries without any controller restart

**Commands to activate h4:**
```bash
mininet> h4 ip link set h4-eth0 up
mininet> h4 ip addr add 10.0.0.4/8 dev h4-eth0
mininet> h4 ping -c 3 h1
```

**Expected controller log:**
```
INFO:host_discovery:NEW HOST DETECTED
INFO:host_discovery:MAC: 00:00:00:00:00:04
INFO:host_discovery:IP: Unknown
INFO:host_discovery:DPID: 0000000000000001 PORT: 4
INFO:host_discovery:HOST UPDATED: 00:00:00:00:00:04
INFO:host_discovery:HOST DATABASE (4 host(s))
```

> **Note on `connection aborted` debug message:** A `DEBUG: openflow.of_01:1 connection aborted` message may appear during h4 activation. This is a **non-fatal** artefact of POX's asyncore compatibility layer with OVS 3.x on Linux kernel 6.x. The controller recovers immediately and processes the `packet_in` event successfully.

---

## 📊 Expected Output

### Final Host Database (after both scenarios)

| MAC Address       | IP Address | Switch DPID       | Port |
|-------------------|------------|-------------------|------|
| 00:00:00:00:00:01 | 10.0.0.1   | 0000000000000001  | 1    |
| 00:00:00:00:00:02 | 10.0.0.2   | 0000000000000001  | 2    |
| 00:00:00:00:00:03 | 10.0.0.3   | 0000000000000001  | 3    |
| 00:00:00:00:00:04 | 10.0.0.4   | 0000000000000001  | 4    |

### Flow Table (`ovs-ofctl dump-flows s1`)

```
cookie=0x0, duration=211.521s, table=0, n_packets=64, n_bytes=4844,
priority=1 actions=CONTROLLER:65535
```

### Connectivity (`pingall`)

```
mininet> pingall
*** Ping: testing ping reachability
h1 -> h2 h3 h4
h2 -> h1 h3 h4
h3 -> h1 h2 h4
h4 -> h1 h2 h3
*** Results: 0% dropped (12/12 received)
```

### Latency (`h1 ping -c 5 h2`)

```
rtt min/avg/max/mdev = 1.606/2.102/2.870/0.516 ms
```

> RTT is ~2 ms (vs ~0.1 ms for direct switch forwarding) because every packet traverses the OpenFlow controller round-trip via the table-miss rule. This is expected and by design for a discovery-mode controller.

---

## 🔑 Key SDN Concepts Demonstrated

| Concept | Implementation |
|---------|---------------|
| Control/data plane separation | POX controller manages all discovery logic; OVS handles forwarding |
| `packet_in` event handling | Table-miss rule triggers controller inspection on every new flow |
| Match-action flow rules | `match=all → action=CONTROLLER:65535` |
| Dynamic state maintenance | Host DB updated in real time without restart |
| OpenFlow protocol | Controller-switch communication over TCP port 6633 (OpenFlow 1.0) |

---

## ⚠️ Known Limitations & Engineering Decisions

- **POX + Python 3.12 compatibility:** POX uses the deprecated `asyncore` module, which causes occasional `connection aborted` debug messages with OVS 3.x on kernel 6.x. These are non-fatal.
- **Dynamic host addition via `net.addLink()`** was found unstable on Ubuntu 24.04 + kernel 6.x due to OVS `ofp_port_status` handling. The **pre-declared silent-host approach** is the accepted academic workaround and produces identical controller-side behaviour.
- **No host-specific forwarding rules** are installed — this is intentional. The project goal is discovery, not forwarding optimisation. In production, host-specific rules would be added after discovery to reduce controller load.

---
