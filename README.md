# 🌐 Host Discovery Service in SDN

> **CN-ORANGE SDN Mini-Project** · PES2UG24AM047 · Chinmay N S

An SDN-based host discovery service built with **POX** and **Mininet** that automatically detects hosts via OpenFlow `packet_in` events, maintains a live host database, and demonstrates full controller–switch interaction over OpenFlow 1.0.


## 🎯 Problem Statement

In a Software Defined Network, the controller must maintain a real-time, accurate view of every host in the network — without any pre-configuration of host identities. This project implements a **Host Discovery Service** that:

- Automatically detects hosts the moment they send their first packet
- Records **MAC address, IP address, Switch DPID, and Port number** for each host
- Updates the database dynamically when new hosts join mid-session
- Maintains full network connectivity throughout the discovery process

The system uses the OpenFlow `packet_in` mechanism as its core discovery engine — every unmatched packet is forwarded to the controller for inspection, and host information is extracted from the Ethernet/ARP/IPv4 headers.

---

## 🏗 Architecture & Design

```
+---------------------------+         OpenFlow 1.0          +----------------------+
|      POX Controller       | <----------------------------> |   OVS Switch (s1)    |
|   host_discovery.py       |    packet_in / flow_mod /      |                      |
|                           |    packet_out messages         +---+----+----+----+---+
|  host_db = {              |                                    |    |    |    |
|    MAC → {IP, DPID, port} |                                   h1   h2   h3   h4
|  }                        |                              10.0.0.1 .2  .3  .4
+---------------------------+
```

### Topology
- **1 OVS switch** (s1) — OpenFlow 1.0
- **4 hosts** (h1–h4) — static IPs and MACs, star topology
- **Remote POX controller** on `127.0.0.1:6633`

### Discovery Mechanism
1. Controller installs a **table-miss flow rule** on every switch at connection time:
   - `match = all packets`, `action = CONTROLLER:65535`, `priority = 1`
2. Every host's first packet hits no flow entry → switch sends `packet_in` to controller
3. Controller extracts source MAC (Ethernet header), source IP (ARP/IPv4 payload), DPID and port (OpenFlow event metadata)
4. Entry is written to `host_db`; if the host is seen again from a new port/switch, the entry is updated (host mobility detection)
5. Controller replies with `packet_out` using `OFPP_FLOOD` to maintain connectivity

---

## 📁 Project Structure

```
pox/
└── ext/
    ├── host_discovery.py     # POX controller component — core discovery logic
    └── topology.py           # Custom Mininet topology (4 hosts, 1 switch)
```

---

## 💻 Environment & Prerequisites

| Component       | Version / Detail                        |
|-----------------|------------------------------------------|
| OS              | Ubuntu 24.04 (tested in VirtualBox VM)   |
| Python          | 3.12 (default system Python)             |
| POX Controller  | 0.7.0 (gar)                              |
| Mininet         | 2.3+                                     |
| Open vSwitch    | 3.x                                      |
| OpenFlow        | 1.0                                      |

### Install dependencies

```bash
# Mininet (if not installed)
sudo apt-get install mininet

# Open vSwitch (usually bundled with Mininet)
sudo apt-get install openvswitch-switch

# POX (clone into home directory)
git clone https://github.com/noxrepo/pox.git ~/pox
```

---

## ⚙️ Setup & Installation

**1. Clone this repository or copy the files into the POX `ext/` directory:**

```bash
# Copy controller component
cp host_discovery.py ~/pox/ext/

# Copy topology script
cp topology.py ~/pox/ext/
```

**2. Verify POX can find the component:**

```bash
cd ~/pox
python3 pox.py log.level --DEBUG host_discovery --help
# Should print component info without error
```

**3. Clean any previous Mininet state:**

```bash
sudo mn -c
```

---

## 🚀 Execution Steps

You need **two terminal windows** open side by side.

---

### Terminal 1 — Start the POX Controller

```bash
cd ~/pox
python3 pox.py log.level --DEBUG host_discovery
```

**Expected startup output:**
```
POX 0.7.0 (gar) / Copyright 2011-2020 James McCauley, et al.
INFO:host_discovery:HostDiscovery started
INFO:host_discovery:Host Discovery Running
DEBUG:openflow.of_01:Listening on 0.0.0.0:6633
```

> ⚠️ Leave Terminal 1 running. Do not close it.

---

### Terminal 2 — Start the Mininet Topology

```bash
cd ~/pox/ext
sudo python3 topology.py
```

**Expected output:**
```
*** Adding controller
*** Adding hosts and switch
*** Adding links
*** Starting network
*** Starting controllers
*** Starting switches
mininet>
```

At this point, Terminal 1 will show:
```
INFO:host_discovery:Switch connected: 0000000000000001
```

---

### Step 3 — Trigger Host Discovery

**In the Mininet CLI (Terminal 2):**

```bash
# Discover all hosts at once
mininet> pingall

# Or trigger individually
mininet> h1 ping -c 3 h2
mininet> h2 ping -c 3 h3
```

---

### Step 4 — Test Dynamic Host Join (Scenario 2)

```bash
# Bring h4 online mid-session (h4 starts with interface down)
mininet> h4 ip link set h4-eth0 up
mininet> h4 ip addr add 10.0.0.4/24 dev h4-eth0

# Trigger discovery for h4
mininet> h4 ping -c 2 h1
```

---

### Step 5 — Run iperf Throughput Test

```bash
# Start iperf server on h2 (background)
mininet> h2 iperf -s -u &

# Run UDP iperf from h1 to h2
mininet> h1 iperf -c 10.0.0.2 -u -b 100m -t 5
```

---

### Step 6 — Verify Flow Table

```bash
# In a separate terminal (or after exiting Mininet)
sudo ovs-ofctl dump-flows s1
```

---

### Step 7 — Exit

```bash
mininet> exit
# Then Ctrl+C in Terminal 1 to stop POX
sudo mn -c    # clean up any leftover state
```

---

## 🧪 Test Scenarios

### Scenario 1 — Initial Host Discovery

**Objective:** Verify the controller detects all hosts via `packet_in` events during initial communication.

**Steps:**
1. Start POX controller (Terminal 1)
2. Start Mininet topology (Terminal 2)
3. Run `mininet> pingall`

**What to observe in the POX log:**
- `NEW HOST DETECTED` logged for each host (h1, h2, h3)
- HOST DATABASE table printed after each detection
- IP addresses resolved from `Unknown` → `10.0.0.x` within the same `packet_in` burst
- Database grows from 1 → 2 → 3 entries progressively

**Pass condition:** All 3 initial hosts appear in the database with correct MAC, IP, DPID, and port. `pingall` shows 0% packet loss.

---

### Scenario 2 — Dynamic Host Join (h4)

**Objective:** Verify the controller detects a new host joining mid-session without any restart.

**Steps:**
1. After Scenario 1 is complete (h1–h3 discovered)
2. Bring h4's interface online and assign IP:
   ```bash
   mininet> h4 ip link set h4-eth0 up
   mininet> h4 ip addr add 10.0.0.4/24 dev h4-eth0
   mininet> h4 ping -c 2 h1
   ```

**What to observe in the POX log:**
- `NEW HOST DETECTED` for MAC `00:00:00:00:00:04`
- IP initially `Unknown`, then updated to `10.0.0.4`
- HOST DATABASE grows from 3 → 4 entries
- A `DEBUG: openflow.of_01:1 connection aborted` message may appear — this is a **non-fatal** POX/OVS compatibility artefact on Linux kernel 6.x; the controller recovers immediately

**Pass condition:** h4 appears in the database. `h4 ping -c 2 h1` succeeds.

---

## 📊 Expected Output

### POX Controller Log — Full Session

```
INFO:host_discovery:Switch connected: 0000000000000001

INFO:host_discovery:NEW HOST DETECTED
INFO:host_discovery:MAC: 00:00:00:00:00:01
INFO:host_discovery:IP: Unknown
INFO:host_discovery:DPID: 0000000000000001 PORT: 1
INFO:host_discovery:======================================================
INFO:host_discovery:HOST DATABASE (1 host(s))
INFO:host_discovery:------------------------------------------------------
INFO:host_discovery:MAC                IP          DPID              Port
INFO:host_discovery:------------------------------------------------------
INFO:host_discovery:00:00:00:00:00:01  Unknown     0000000000000001  1
INFO:host_discovery:======================================================
INFO:host_discovery:HOST UPDATED: 00:00:00:00:00:01
INFO:host_discovery:HOST DATABASE (1 host(s))
...
INFO:host_discovery:00:00:00:00:00:01  10.0.0.1    0000000000000001  1
INFO:host_discovery:======================================================

INFO:host_discovery:NEW HOST DETECTED
INFO:host_discovery:MAC: 00:00:00:00:00:02
INFO:host_discovery:IP: 10.0.0.2
INFO:host_discovery:DPID: 0000000000000001 PORT: 2
INFO:host_discovery:HOST DATABASE (2 host(s))
...

INFO:host_discovery:NEW HOST DETECTED
INFO:host_discovery:MAC: 00:00:00:00:00:03
...
INFO:host_discovery:HOST DATABASE (3 host(s))
...

# After h4 joins:
DEBUG:openflow.of_01:1 connection aborted          ← non-fatal, controller recovers
INFO:host_discovery:NEW HOST DETECTED
INFO:host_discovery:MAC: 00:00:00:00:00:04
INFO:host_discovery:IP: Unknown → 10.0.0.4
INFO:host_discovery:HOST DATABASE (4 host(s))
INFO:host_discovery:00:00:00:00:00:01  10.0.0.1    0000000000000001  1
INFO:host_discovery:00:00:00:00:00:02  10.0.0.2    0000000000000001  2
INFO:host_discovery:00:00:00:00:00:03  10.0.0.3    0000000000000001  3
INFO:host_discovery:00:00:00:00:00:04  10.0.0.4    0000000000000001  4
```

### Mininet — pingall Result

```
mininet> pingall
*** Ping: testing ping reachability
h1 -> h2 h3 h4
h2 -> h1 h3 h4
h3 -> h1 h2 h4
h4 -> h1 h2 h3
*** Results: 0% dropped (12/12 received)
```

---

## 📈 Performance Results

### Latency — `h1 ping -c 5 h2`

```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.67 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=1.61 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=2.57 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=64 time=1.80 ms
64 bytes from 10.0.0.2: icmp_seq=5 ttl=64 time=2.87 ms

--- 10.0.0.2 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4005ms
rtt min/avg/max/mdev = 1.606/2.102/2.870/0.516 ms
```

> The ~2 ms average RTT is expected — every packet routes through the controller (table-miss rule), adding a software round-trip compared to direct switch forwarding (~0.1 ms). This is by design for a discovery-mode controller.

---

### Throughput — `h1 iperf -c 10.0.0.2 -u -b 100m -t 5`

```
Client connecting to 10.0.0.2, UDP port 5001
Sending 1470 byte datagrams, IPG target: 117.60 us (kalman adjust)
UDP buffer size: 208 KByte (default)

[ 1] local 10.0.0.1 port 47592 connected with 10.0.0.2 port 5001
[ ID] Interval       Transfer     Bandwidth
[  1] 0.0000-5.0003 sec  59.6 MBytes  100 Mbits/sec
[  1] Sent 42517 datagrams
[  3] WARNING: did not receive ack of last datagram after 10 tries.
```

| Metric | Result |
|--------|--------|
| Bandwidth | 100 Mbits/sec (full requested rate) |
| Data transferred | 59.6 MB over 5 seconds |
| Datagrams sent | 42,517 UDP packets |
| Packet loss (data) | 0% |
| Final ACK warning | Expected — flood-only controller has no dedicated return path for the sentinel datagram. Does not affect the measured bandwidth. |

---

## 🔍 Flow Table Verification

```bash
sudo ovs-ofctl dump-flows s1
```

**Output:**
```
cookie=0x0, duration=211.521s, table=0, n_packets=64, n_bytes=4844, priority=1
actions=CONTROLLER:65535
```

| Field | Value | Meaning |
|-------|-------|---------|
| `cookie=0x0` | 0 | Default identifier — generic table-miss rule |
| `duration=211.521s` | 211 s | Rule persisted for entire test session |
| `table=0` | 0 | First table in OpenFlow pipeline |
| `n_packets=64` | 64 | Packets forwarded to controller (ARP + ICMP mix) |
| `n_bytes=4844` | 4,844 B | Consistent with 64 mixed ARP/ICMP packets |
| `priority=1` | Lowest | Only fires for packets with no specific match |
| `actions=CONTROLLER:65535` | OFPP_CONTROLLER | Full packet sent to POX for inspection |

A single table-miss rule is intentionally the only entry. This ensures every packet reaches the controller for host discovery. In a production system, per-host forwarding rules would be added after discovery to reduce controller load.

---

## ⚠️ Design Decisions & Limitations

### Why POX instead of Ryu?

Ryu requires Python 3.6–3.9 and is incompatible with Python 3.12 (the default on Ubuntu 24.04) due to `setuptools` and `pkgutil` deprecations. POX runs on Python 3.12 with minor version warnings but no functional issues. POX is explicitly allowed by the project guidelines.

### Why pre-declared hosts instead of `net.addLink()` at runtime?

Adding h4 dynamically using Mininet's `net.addLink()` API caused the OpenFlow session to drop consistently on Ubuntu 24.04 + Linux kernel 6.x. The root cause is a race condition in POX's `asyncore`-based socket dispatcher when OVS sends an `ofp_port_status` message during live datapath reconfiguration — a known incompatibility with OVS 3.x.

The workaround: h4 is declared in the topology at startup but kept **network-silent** (interface administratively down, no IP). Activating h4's interface mid-session via `ip link set up` + `ip addr add` produces identical controller-side behaviour — h4 is completely unknown to the controller until its first `packet_in` event. This is the correct SDN definition of dynamic host discovery.

### Controller-in-the-loop forwarding

Because only a table-miss rule is installed, every packet goes to the controller. This results in ~2 ms RTT instead of ~0.1 ms. For a host-discovery project this is intentional — if specific forwarding rules were installed per host pair, packets would bypass the controller and host mobility updates could be missed.

---

## 📚 References

1. **POX SDN Controller** — NOX/POX Project, James McCauley et al. (2011–2020)
   https://github.com/noxrepo/pox

2. **Mininet** — Mininet Project, Stanford University
   http://mininet.org/

3. **OpenFlow Switch Specification v1.0.0** — Open Networking Foundation (2009)
   https://opennetworking.org/wp-content/uploads/2013/04/openflow-spec-v1.0.0.pdf

4. **Open vSwitch Documentation** — The Linux Foundation
   https://docs.openvswitch.org/

5. **Software Defined Networking: A Comprehensive Survey** — Kreutz et al., IEEE, 2015
   https://ieeexplore.ieee.org/document/6994333

6. **Mininet Python API Reference**
   http://mininet.org/api/annotated.html

7. **iperf — The TCP, UDP and SCTP Network Bandwidth Measurement Tool**
   https://iperf.fr/

---

## 👤 Author

**Chinmay N S**
SRN: PES2UG24AM047
Course: Computer Networks — SDN Lab (CN-ORANGE)

---

*All screenshots and execution logs are included in the project report PDF submitted alongside this repository.*
