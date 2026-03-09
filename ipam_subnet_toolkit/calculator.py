"""
calculator.py
~~~~~~~~~~~~~
Core subnet calculation logic using the Python standard library ``ipaddress``
module.  No third-party dependencies are required.

Classes
-------
SubnetInfo
    A dataclass that holds all computed information about a CIDR block.

Functions
---------
calculate_subnet(cidr)
    Parse a CIDR string and return a :class:`SubnetInfo` instance.

contains_ip(cidr, ip)
    Return ``True`` if *ip* belongs to the subnet described by *cidr*.
"""

from __future__ import annotations

import ipaddress
import json
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class SubnetInfo:
    """All relevant details derived from a single CIDR block.

    Attributes
    ----------
    cidr : str
        The canonical CIDR notation of the network (e.g. ``"192.168.1.0/24"``).
    network_address : str
        The network (wire) address — first address in the block.
    broadcast_address : str
        The broadcast address — last address in the block.
    subnet_mask : str
        Dotted-decimal subnet mask (e.g. ``"255.255.255.0"``).
    wildcard_mask : str
        Wildcard (inverse) mask used in ACL / firewall rules.
    prefix_length : int
        The CIDR prefix length (0–32).
    total_hosts : int
        Total number of addresses in the block, including network and broadcast.
    usable_hosts : int
        Number of addresses available for assignment to hosts.
        This is ``total_hosts - 2`` for prefix lengths ≤ 30; for ``/31``
        (point-to-point RFC 3021) both addresses are usable; for ``/32``
        (host route) the single address is the host itself.
    first_usable_host : Optional[str]
        First assignable host address, or ``None`` for ``/32`` routes.
    last_usable_host : Optional[str]
        Last assignable host address, or ``None`` for ``/32`` routes.
    ip_class : str
        Traditional IPv4 class (A / B / C / D / E) or ``"N/A"`` for
        addresses that do not map cleanly to a class.
    is_private : bool
        ``True`` when the network falls within RFC 1918 private ranges.
    is_loopback : bool
        ``True`` when the network is in the loopback range (127.0.0.0/8).
    """

    cidr: str
    network_address: str
    broadcast_address: str
    subnet_mask: str
    wildcard_mask: str
    prefix_length: int
    total_hosts: int
    usable_hosts: int
    first_usable_host: Optional[str]
    last_usable_host: Optional[str]
    ip_class: str
    is_private: bool
    is_loopback: bool

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a plain dictionary representation."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Return a JSON string representation.

        Parameters
        ----------
        indent:
            Number of spaces used for pretty-printing.
        """
        return json.dumps(self.to_dict(), indent=indent)

    # ------------------------------------------------------------------
    # Membership test
    # ------------------------------------------------------------------

    def contains(self, ip: str) -> bool:
        """Return ``True`` if *ip* is within this subnet.

        Parameters
        ----------
        ip:
            An IPv4 address string (with or without prefix length).

        Raises
        ------
        ValueError
            If *ip* is not a valid IPv4 address.
        """
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            # Maybe they passed a CIDR; try stripping the prefix
            addr = ipaddress.ip_address(ip.split("/")[0])
        network = ipaddress.ip_network(self.cidr, strict=False)
        return addr in network

    # ------------------------------------------------------------------
    # Pretty display
    # ------------------------------------------------------------------

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            f"CIDR Block         : {self.cidr}",
            f"Network Address    : {self.network_address}",
            f"Broadcast Address  : {self.broadcast_address}",
            f"Subnet Mask        : {self.subnet_mask}",
            f"Wildcard Mask      : {self.wildcard_mask}",
            f"Prefix Length      : /{self.prefix_length}",
            f"Total Hosts        : {self.total_hosts:,}",
            f"Usable Hosts       : {self.usable_hosts:,}",
            f"First Usable Host  : {self.first_usable_host or 'N/A'}",
            f"Last Usable Host   : {self.last_usable_host or 'N/A'}",
            f"IP Class           : {self.ip_class}",
            f"Private Range      : {'Yes' if self.is_private else 'No'}",
            f"Loopback Range     : {'Yes' if self.is_loopback else 'No'}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calculate_subnet(cidr: str) -> SubnetInfo:
    """Parse *cidr* and compute all subnet properties.

    Parameters
    ----------
    cidr:
        An IPv4 CIDR string such as ``"10.0.0.0/8"`` or
        ``"192.168.100.50/24"`` (host bits are silently zeroed).

    Returns
    -------
    SubnetInfo
        Populated dataclass with every computed field.

    Raises
    ------
    ValueError
        If *cidr* is not a valid IPv4 network string.
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError as exc:
        raise ValueError(f"Invalid CIDR notation '{cidr}': {exc}") from exc

    if network.version != 4:
        raise ValueError(f"Only IPv4 is supported; got '{cidr}'")

    prefix = network.prefixlen
    total = network.num_addresses

    # Usable host calculation follows RFC conventions:
    #   /32  → 1 usable (the host itself)
    #   /31  → 2 usable (point-to-point, RFC 3021)
    #   else → total - 2 (subtract network + broadcast)
    if prefix == 32:
        usable = 1
        first_host: Optional[str] = str(network.network_address)
        last_host: Optional[str] = None
    elif prefix == 31:
        usable = 2
        hosts = list(network.hosts()) or list(network)
        first_host = str(network.network_address)
        last_host = str(network.broadcast_address)
    else:
        usable = total - 2
        first_host = str(network.network_address + 1)
        last_host = str(network.broadcast_address - 1)

    # Wildcard mask = bitwise NOT of subnet mask
    mask_int = int(network.netmask)
    wildcard_int = 0xFFFFFFFF ^ mask_int
    wildcard = str(ipaddress.IPv4Address(wildcard_int))

    return SubnetInfo(
        cidr=str(network),
        network_address=str(network.network_address),
        broadcast_address=str(network.broadcast_address),
        subnet_mask=str(network.netmask),
        wildcard_mask=wildcard,
        prefix_length=prefix,
        total_hosts=total,
        usable_hosts=usable,
        first_usable_host=first_host,
        last_usable_host=last_host,
        ip_class=_ip_class(network.network_address),
        is_private=network.is_private,
        is_loopback=network.is_loopback,
    )


def contains_ip(cidr: str, ip: str) -> bool:
    """Return ``True`` if *ip* belongs to the subnet *cidr*.

    Convenience wrapper around :meth:`SubnetInfo.contains` for callers that
    do not need the full :class:`SubnetInfo` object.

    Parameters
    ----------
    cidr:
        IPv4 CIDR string.
    ip:
        IPv4 address string to test.
    """
    info = calculate_subnet(cidr)
    return info.contains(ip)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ip_class(addr: ipaddress.IPv4Address) -> str:
    """Return the traditional IPv4 class letter for *addr*.

    Classes are determined by the leading bits of the first octet:

    * Class A: 0.0.0.0 – 127.255.255.255
    * Class B: 128.0.0.0 – 191.255.255.255
    * Class C: 192.0.0.0 – 223.255.255.255
    * Class D: 224.0.0.0 – 239.255.255.255 (multicast)
    * Class E: 240.0.0.0 – 255.255.255.255 (reserved)
    """
    first_octet = int(addr) >> 24
    if first_octet < 128:
        return "A"
    if first_octet < 192:
        return "B"
    if first_octet < 224:
        return "C"
    if first_octet < 240:
        return "D (Multicast)"
    return "E (Reserved)"
