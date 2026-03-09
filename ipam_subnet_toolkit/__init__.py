"""
ipam-subnet-toolkit
~~~~~~~~~~~~~~~~~~~
A CLI toolkit for IP Address Management (IPAM) and subnet calculations.

Provides tools to analyse IPv4 CIDR blocks: network/broadcast addresses,
usable host ranges, host counts, and IP membership checks.
"""

from .calculator import SubnetInfo, calculate_subnet

__all__ = ["SubnetInfo", "calculate_subnet"]
__version__ = "1.0.0"
