"""
cli.py
~~~~~~
Command-line interface for the ipam-subnet-toolkit.

Entry point: ``ipam`` (configured in pyproject.toml).

Sub-commands
------------
info
    Print all subnet details for a CIDR block.
contains
    Check whether an IP address belongs to a CIDR block.
export
    Calculate subnet info and write results to a JSON file.

Examples
--------
::

    ipam info 192.168.1.0/24
    ipam info 10.0.0.0/8 --json
    ipam contains 192.168.1.0/24 192.168.1.100
    ipam export 172.16.0.0/12 --output result.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .calculator import SubnetInfo, calculate_subnet, contains_ip


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def _print_table(info: SubnetInfo) -> None:
    """Print subnet info as a human-readable aligned table."""
    rows = [
        ("CIDR Block", info.cidr),
        ("Network Address", info.network_address),
        ("Broadcast Address", info.broadcast_address),
        ("Subnet Mask", info.subnet_mask),
        ("Wildcard Mask", info.wildcard_mask),
        ("Prefix Length", f"/{info.prefix_length}"),
        ("Total Hosts", f"{info.total_hosts:,}"),
        ("Usable Hosts", f"{info.usable_hosts:,}"),
        ("First Usable Host", info.first_usable_host or "N/A"),
        ("Last Usable Host", info.last_usable_host or "N/A"),
        ("IP Class", info.ip_class),
        ("Private Range", "Yes" if info.is_private else "No"),
        ("Loopback Range", "Yes" if info.is_loopback else "No"),
    ]
    col_width = max(len(label) for label, _ in rows)
    print()
    print(f"  Subnet Analysis: {info.cidr}")
    print("  " + "-" * (col_width + 22))
    for label, value in rows:
        print(f"  {label:<{col_width}}  :  {value}")
    print()


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------


def cmd_info(args: argparse.Namespace) -> int:
    """Handle the ``info`` sub-command."""
    try:
        info = calculate_subnet(args.cidr)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(info.to_json())
    else:
        _print_table(info)
    return 0


def cmd_contains(args: argparse.Namespace) -> int:
    """Handle the ``contains`` sub-command."""
    try:
        result = contains_ip(args.cidr, args.ip)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    status = "BELONGS TO" if result else "does NOT belong to"
    print(f"\n  {args.ip}  {status}  {args.cidr}\n")
    return 0 if result else 2


def cmd_export(args: argparse.Namespace) -> int:
    """Handle the ``export`` sub-command."""
    try:
        info = calculate_subnet(args.cidr)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    try:
        output_path.write_text(info.to_json(), encoding="utf-8")
    except OSError as exc:
        print(f"Error writing file '{output_path}': {exc}", file=sys.stderr)
        return 1

    print(f"\n  Results written to: {output_path.resolve()}\n")
    return 0


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="ipam",
        description=(
            "ipam-subnet-toolkit — IPv4 subnet calculator and IPAM helper.\n\n"
            "Analyse CIDR blocks, check IP membership, and export results to JSON."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ipam info 192.168.1.0/24\n"
            "  ipam info 10.0.0.0/8 --json\n"
            "  ipam contains 192.168.1.0/24 192.168.1.50\n"
            "  ipam export 172.16.0.0/12 --output report.json\n"
        ),
    )
    parser.add_argument(
        "--version", action="version", version="ipam-subnet-toolkit 1.0.0"
    )

    subparsers = parser.add_subparsers(
        title="sub-commands",
        dest="command",
        metavar="<command>",
    )

    # ---- info ---------------------------------------------------------------
    info_parser = subparsers.add_parser(
        "info",
        help="Display detailed subnet information for a CIDR block.",
        description=(
            "Calculate and display all properties of an IPv4 CIDR block:\n"
            "network address, broadcast address, subnet mask, host range, and more."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ipam info 192.168.1.0/24\n"
            "  ipam info 10.0.0.0/8 --json\n"
            "  ipam info 172.16.50.100/20\n"
        ),
    )
    info_parser.add_argument(
        "cidr",
        metavar="CIDR",
        help="IPv4 network in CIDR notation, e.g. 192.168.1.0/24",
    )
    info_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON instead of a human-readable table.",
    )
    info_parser.set_defaults(func=cmd_info)

    # ---- contains -----------------------------------------------------------
    contains_parser = subparsers.add_parser(
        "contains",
        help="Check whether an IP address belongs to a subnet.",
        description=(
            "Test IP membership: returns exit code 0 if the IP is in the subnet,\n"
            "or exit code 2 if it is not (suitable for shell scripting)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ipam contains 192.168.1.0/24 192.168.1.100\n"
            "  ipam contains 10.0.0.0/8 10.250.100.1\n"
            "  ipam contains 172.16.0.0/16 192.168.0.1\n"
        ),
    )
    contains_parser.add_argument(
        "cidr",
        metavar="CIDR",
        help="IPv4 network in CIDR notation.",
    )
    contains_parser.add_argument(
        "ip",
        metavar="IP",
        help="IPv4 address to test.",
    )
    contains_parser.set_defaults(func=cmd_contains)

    # ---- export -------------------------------------------------------------
    export_parser = subparsers.add_parser(
        "export",
        help="Export subnet analysis results to a JSON file.",
        description="Calculate subnet information and save it as a formatted JSON file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ipam export 192.168.1.0/24 --output subnet.json\n"
            "  ipam export 10.0.0.0/8 --output rfc1918-a.json\n"
        ),
    )
    export_parser.add_argument(
        "cidr",
        metavar="CIDR",
        help="IPv4 network in CIDR notation.",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        default="subnet_info.json",
        help="Path to the output JSON file (default: subnet_info.json).",
    )
    export_parser.set_defaults(func=cmd_export)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> None:
    """Parse arguments and dispatch to the appropriate sub-command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
