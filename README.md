# ipam-subnet-toolkit

A command-line toolkit for **IP Address Management (IPAM)** and **IPv4 subnet calculations**.
Given any CIDR block, it instantly computes every property a network engineer needs — with clean output, JSON export, and scriptable exit codes.

Built with the Python standard library only (no third-party dependencies).

---

## Features

| Capability | Detail |
|---|---|
| Subnet analysis | Network address, broadcast, mask, wildcard, prefix length |
| Host counting | Total hosts and usable hosts (RFC-correct for /31, /32) |
| Usable host range | First and last assignable addresses |
| IP class detection | A / B / C / D (Multicast) / E (Reserved) |
| Private / loopback flags | RFC 1918, RFC 5735 awareness |
| IP membership check | Test whether any IP belongs to a subnet |
| JSON export | Machine-readable output for automation pipelines |
| Shell-script friendly | Exit code `0` = in subnet, `2` = not in subnet |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/ipam-subnet-toolkit.git
cd ipam-subnet-toolkit

# Install in editable mode (no extra dependencies needed)
pip install -e .
```

After installation, the `ipam` command is available on your `PATH`.

---

## Quick Start

```bash
# Analyse a /24 LAN segment
ipam info 192.168.1.0/24

# Check if a DHCP-assigned IP is inside the corporate subnet
ipam contains 10.0.0.0/8 10.42.17.200

# Export WAN link details to JSON for a CMDB
ipam export 203.0.113.0/30 --output wan_link.json
```

---

## CLI Reference

### `ipam info <CIDR>`

Print a full subnet breakdown to the terminal.

```
usage: ipam info [-h] [--json] CIDR

positional arguments:
  CIDR        IPv4 network in CIDR notation, e.g. 192.168.1.0/24

optional arguments:
  --json      Output results as JSON instead of a human-readable table
```

**Example — home LAN:**

```bash
$ ipam info 192.168.1.0/24

  Subnet Analysis: 192.168.1.0/24
  ----------------------------------------
  CIDR Block         :  192.168.1.0/24
  Network Address    :  192.168.1.0
  Broadcast Address  :  192.168.1.255
  Subnet Mask        :  255.255.255.0
  Wildcard Mask      :  0.0.0.255
  Prefix Length      :  /24
  Total Hosts        :  256
  Usable Hosts       :  254
  First Usable Host  :  192.168.1.1
  Last Usable Host   :  192.168.1.254
  IP Class           :  C
  Private Range      :  Yes
  Loopback Range     :  No
```

**Example — RFC 1918 Class A with JSON output:**

```bash
$ ipam info 10.0.0.0/8 --json
{
  "cidr": "10.0.0.0/8",
  "network_address": "10.0.0.0",
  "broadcast_address": "10.255.255.255",
  "subnet_mask": "255.0.0.0",
  "wildcard_mask": "0.255.255.255",
  "prefix_length": 8,
  "total_hosts": 16777216,
  "usable_hosts": 16777214,
  "first_usable_host": "10.0.0.1",
  "last_usable_host": "10.255.255.254",
  "ip_class": "A",
  "is_private": true,
  "is_loopback": false
}
```

---

### `ipam contains <CIDR> <IP>`

Check whether an IP address belongs to a subnet.
Exit code `0` = IP is in the subnet; exit code `2` = IP is not.

```
usage: ipam contains [-h] CIDR IP

positional arguments:
  CIDR        IPv4 network in CIDR notation
  IP          IPv4 address to test
```

**Example — IP inside the subnet:**

```bash
$ ipam contains 10.0.0.0/8 10.42.100.200

  10.42.100.200  BELONGS TO  10.0.0.0/8

$ echo $?
0
```

**Example — IP outside the subnet:**

```bash
$ ipam contains 192.168.1.0/24 172.16.0.5

  172.16.0.5  does NOT belong to  192.168.1.0/24

$ echo $?
2
```

**Shell scripting example:**

```bash
#!/bin/bash
if ipam contains 10.0.0.0/8 "$ASSIGNED_IP" > /dev/null; then
    echo "IP is on the corporate network"
else
    echo "IP is outside the corporate network — VPN required"
fi
```

---

### `ipam export <CIDR> [--output FILE]`

Calculate subnet info and save it as a formatted JSON file.

```
usage: ipam export [-h] [--output FILE] CIDR

positional arguments:
  CIDR                  IPv4 network in CIDR notation

optional arguments:
  --output FILE, -o FILE
                        Path to output JSON file (default: subnet_info.json)
```

**Example:**

```bash
$ ipam export 172.16.0.0/12 --output rfc1918_b.json

  Results written to: /home/user/rfc1918_b.json
```

---

## Networking Use Cases

### 1. Data Centre VLAN Planning

When segmenting a data centre you often carve a Class B range into VLANs.
Use `ipam info` to verify each segment before committing to IPAM software:

```bash
# Management VLAN
ipam info 10.10.0.0/24

# Production servers
ipam info 10.10.1.0/23    # 510 usable hosts across two octets

# Database tier (tightly scoped)
ipam info 10.10.4.0/26    # 62 usable hosts
```

### 2. WAN Point-to-Point Links

Point-to-point links between routers traditionally use `/30` blocks (2 usable hosts),
or `/31` (RFC 3021) to conserve address space:

```bash
# Classic /30 WAN link
$ ipam info 203.0.113.0/30 --json | python3 -m json.tool
# → first_usable_host: "203.0.113.1"  (router interface)
# → last_usable_host:  "203.0.113.2"  (peer interface)

# RFC 3021 /31 — no network/broadcast overhead
ipam info 203.0.113.4/31
```

### 3. Firewall ACL Wildcard Masks

Cisco ACLs use wildcard masks instead of subnet masks.
The `wildcard_mask` field gives you the value to paste directly into your config:

```bash
$ ipam info 192.168.10.0/27 --json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'access-list 100 permit ip {d[\"network_address\"]} {d[\"wildcard_mask\"]} any')
"
# access-list 100 permit ip 192.168.10.0 0.0.0.31 any
```

### 4. Cloud VPC Subnet Validation

Before provisioning AWS/GCP/Azure subnets, verify that your CIDR allocations
don't overlap and have enough usable addresses:

```bash
ipam info 10.1.0.0/20   # us-east-1 — 4094 usable hosts
ipam info 10.2.0.0/20   # eu-west-1 — 4094 usable hosts
ipam info 10.3.0.0/20   # ap-south-1
```

### 5. DHCP Scope Sizing

Determine if a /24 pool is large enough for 200 devices on a guest Wi-Fi network:

```bash
$ ipam info 192.168.50.0/24 --json | python3 -c "
import sys, json
d = json.load(sys.stdin)
needed = 200
available = d['usable_hosts']
print(f'Need {needed} addresses, {available} available — ', end='')
print('OK' if available >= needed else 'INSUFFICIENT')
"
# Need 200 addresses, 254 available — OK
```

### 6. Automation / CMDB Integration

Export results to JSON and pipe them into your CMDB, Ansible inventory, or
Terraform variable files:

```bash
# Generate subnet records for all /28 blocks in a /24
for i in $(seq 0 15); do
    start=$((i * 16))
    ipam export "192.168.1.${start}/28" -o "vlan_${i}.json"
done
```

---

## Running Tests

The test suite requires no extra dependencies beyond `pytest`:

```bash
pip install pytest
pytest tests/ -v
```

Expected output: **95 tests, all passing** across:

- **`tests/test_calculator.py`** — unit tests for the core calculation engine
  (Class A/B/C subnets, edge cases `/0`–`/32`, membership checks, serialisation, error handling)
- **`tests/test_cli.py`** — integration tests for all three CLI sub-commands
  (table output, JSON flag, exit codes, file export, invalid input)

---

## Project Structure

```
ipam-subnet-toolkit/
├── ipam_subnet_toolkit/
│   ├── __init__.py       # Public API surface
│   ├── calculator.py     # Core subnet logic (SubnetInfo dataclass + helpers)
│   └── cli.py            # argparse CLI with info / contains / export sub-commands
├── tests/
│   ├── test_calculator.py
│   └── test_cli.py
├── pyproject.toml        # Build metadata and pytest config
└── README.md
```

---

## Key Design Decisions

**Zero external dependencies** — The entire project uses only `ipaddress`, `json`, `argparse`, and `dataclasses` from the Python standard library. This makes it trivially installable in any environment.

**RFC-correct host counts** — `/31` point-to-point links (RFC 3021) and `/32` host routes are handled explicitly rather than applying a naive `total - 2` formula.

**Scriptable exit codes** — `ipam contains` returns exit code `2` (not `1`) when the IP is absent, following the Unix convention that allows distinguishing "command error" (`1`) from "negative answer" (`2`) in shell scripts.

**Dataclass-first** — `SubnetInfo` is a plain dataclass. It serialises to dict/JSON with no custom logic, and is easy to import as a library (`from ipam_subnet_toolkit import calculate_subnet`).

---

## License

MIT
