# ipam-subnet-toolkit

A compact Python CLI project that solves a practical networking task: **quick IPv4 subnet inspection for labs, scripts, and day-to-day IP planning**.

It is intentionally simple and dependency-free (Python standard library only), so a recruiter or hiring manager can review both the code and the UX in under a minute.

## Why I Built This

As a Cloud & Network Engineering student, I wanted a small project that demonstrates:
- clean Python fundamentals,
- real networking concepts (CIDR math, RFC-aware host rules), and
- CLI design that is useful in automation workflows.

## What It Does

- Calculates subnet details from any IPv4 CIDR.
- Handles edge cases like `/31` (RFC 3021) and `/32` host routes.
- Checks whether an IP belongs to a subnet.
- Exports results as JSON for scripts and pipelines.
- Returns script-friendly exit codes (`contains`: `0` in subnet, `2` out of subnet).

## Installation

```bash
git clone https://github.com/your-username/ipam-subnet-toolkit.git
cd ipam-subnet-toolkit
pip install -e .
```

## Practical Use Cases

- Validate subnet plans before creating cloud VPC/VNet ranges.
- Double-check host capacity for VLAN sizing.
- Generate wildcard masks for ACL drafting.
- Add quick IP membership checks in shell automation.
- Export subnet metadata into inventory/CMDB-style JSON files.

## Example Commands (with expected output)

```bash
$ ipam info 192.168.10.0/24
# Prints a readable subnet table including network, broadcast, usable hosts, and range.

$ ipam info 10.0.0.0/8 --json
# Prints JSON with fields like "cidr", "usable_hosts", and "wildcard_mask".

$ ipam contains 10.0.0.0/8 10.42.17.200
# Output contains: is in
# Exit code: 0

$ ipam contains 192.168.1.0/24 172.16.0.5
# Output contains: is NOT in
# Exit code: 2

$ ipam export 203.0.113.0/30 --output wan_link.json
# Writes JSON file and prints the resolved output path.

$ ipam info 203.0.113.4/31 --json
# Shows usable_hosts as 2 (point-to-point behavior).
```

## Sample Terminal Output (`ipam info`)

```text
$ ipam info 192.168.1.0/24

  Subnet Analysis: 192.168.1.0/24
  ---------------------------------------
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

## Project Structure

```text
ipam_subnet_toolkit/
  calculator.py   # subnet calculations and data model
  cli.py          # argparse CLI and command handlers
tests/
  test_calculator.py
  test_cli.py
pyproject.toml
README.md
```

## Limitations

- IPv4 only (no IPv6 support yet).
- Single-subnet operations only (no overlap detection across multiple CIDRs).
- No direct integrations with cloud APIs or IPAM platforms.

## Future Improvements

- Add an optional `overlap` command for comparing two CIDRs.
- Add CSV export alongside JSON for spreadsheet workflows.
- Expand help examples for common cloud subnet sizing patterns.

## Running Tests

```bash
pytest -q
```
