"""
test_calculator.py
~~~~~~~~~~~~~~~~~~
Unit tests for :mod:`ipam_subnet_toolkit.calculator`.

Covers common real-world subnets used in enterprise and home networking,
edge cases (host routes, point-to-point links, default route), and the
IP membership check helper.
"""

import pytest

from ipam_subnet_toolkit.calculator import SubnetInfo, calculate_subnet, contains_ip


# ---------------------------------------------------------------------------
# Fixtures / shared helpers
# ---------------------------------------------------------------------------


def subnet(cidr: str) -> SubnetInfo:
    """Shorthand to calculate subnet info."""
    return calculate_subnet(cidr)


# ---------------------------------------------------------------------------
# Class A – RFC 1918 (10.0.0.0/8)
# ---------------------------------------------------------------------------


class TestClassA:
    def test_network_address(self):
        assert subnet("10.0.0.0/8").network_address == "10.0.0.0"

    def test_broadcast_address(self):
        assert subnet("10.0.0.0/8").broadcast_address == "10.255.255.255"

    def test_subnet_mask(self):
        assert subnet("10.0.0.0/8").subnet_mask == "255.0.0.0"

    def test_wildcard_mask(self):
        assert subnet("10.0.0.0/8").wildcard_mask == "0.255.255.255"

    def test_prefix_length(self):
        assert subnet("10.0.0.0/8").prefix_length == 8

    def test_total_hosts(self):
        assert subnet("10.0.0.0/8").total_hosts == 2**24  # 16,777,216

    def test_usable_hosts(self):
        assert subnet("10.0.0.0/8").usable_hosts == 2**24 - 2  # 16,777,214

    def test_first_usable_host(self):
        assert subnet("10.0.0.0/8").first_usable_host == "10.0.0.1"

    def test_last_usable_host(self):
        assert subnet("10.0.0.0/8").last_usable_host == "10.255.255.254"

    def test_ip_class(self):
        assert subnet("10.0.0.0/8").ip_class == "A"

    def test_is_private(self):
        assert subnet("10.0.0.0/8").is_private is True

    def test_cidr_canonicalised(self):
        # Host bits stripped automatically
        info = calculate_subnet("10.5.6.7/8")
        assert info.cidr == "10.0.0.0/8"


# ---------------------------------------------------------------------------
# Class B – RFC 1918 (172.16.0.0/12)
# ---------------------------------------------------------------------------


class TestClassB:
    def test_network_address(self):
        assert subnet("172.16.0.0/12").network_address == "172.16.0.0"

    def test_broadcast_address(self):
        assert subnet("172.16.0.0/12").broadcast_address == "172.31.255.255"

    def test_subnet_mask(self):
        assert subnet("172.16.0.0/12").subnet_mask == "255.240.0.0"

    def test_total_hosts(self):
        assert subnet("172.16.0.0/12").total_hosts == 2**20  # 1,048,576

    def test_usable_hosts(self):
        assert subnet("172.16.0.0/12").usable_hosts == 2**20 - 2

    def test_ip_class(self):
        assert subnet("172.16.0.0/12").ip_class == "B"

    def test_is_private(self):
        assert subnet("172.16.0.0/12").is_private is True


# ---------------------------------------------------------------------------
# Class C – RFC 1918 (192.168.1.0/24)
# ---------------------------------------------------------------------------


class TestClassC:
    def test_network_address(self):
        assert subnet("192.168.1.0/24").network_address == "192.168.1.0"

    def test_broadcast_address(self):
        assert subnet("192.168.1.0/24").broadcast_address == "192.168.1.255"

    def test_subnet_mask(self):
        assert subnet("192.168.1.0/24").subnet_mask == "255.255.255.0"

    def test_wildcard_mask(self):
        assert subnet("192.168.1.0/24").wildcard_mask == "0.0.0.255"

    def test_total_hosts(self):
        assert subnet("192.168.1.0/24").total_hosts == 256

    def test_usable_hosts(self):
        assert subnet("192.168.1.0/24").usable_hosts == 254

    def test_first_usable_host(self):
        assert subnet("192.168.1.0/24").first_usable_host == "192.168.1.1"

    def test_last_usable_host(self):
        assert subnet("192.168.1.0/24").last_usable_host == "192.168.1.254"

    def test_ip_class(self):
        assert subnet("192.168.1.0/24").ip_class == "C"

    def test_is_private(self):
        assert subnet("192.168.1.0/24").is_private is True


# ---------------------------------------------------------------------------
# Common smaller subnets (/25, /26, /27, /28, /30)
# ---------------------------------------------------------------------------


class TestSmallerSubnets:
    def test_slash25_usable_hosts(self):
        assert subnet("192.168.1.0/25").usable_hosts == 126

    def test_slash25_broadcast(self):
        assert subnet("192.168.1.0/25").broadcast_address == "192.168.1.127"

    def test_slash26_usable_hosts(self):
        assert subnet("192.168.1.0/26").usable_hosts == 62

    def test_slash27_usable_hosts(self):
        assert subnet("192.168.1.0/27").usable_hosts == 30

    def test_slash28_usable_hosts(self):
        assert subnet("192.168.1.0/28").usable_hosts == 14

    def test_slash28_subnet_mask(self):
        assert subnet("192.168.1.0/28").subnet_mask == "255.255.255.240"

    def test_slash30_usable_hosts(self):
        # Typical point-to-point WAN link allocation (old-style)
        assert subnet("10.1.1.0/30").usable_hosts == 2

    def test_slash30_first_host(self):
        assert subnet("10.1.1.0/30").first_usable_host == "10.1.1.1"

    def test_slash30_last_host(self):
        assert subnet("10.1.1.0/30").last_usable_host == "10.1.1.2"


# ---------------------------------------------------------------------------
# Edge cases: /31, /32, /0
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_slash31_usable_hosts(self):
        # RFC 3021 point-to-point link — both addresses are usable
        assert subnet("10.0.0.0/31").usable_hosts == 2

    def test_slash31_first_host(self):
        assert subnet("10.0.0.0/31").first_usable_host == "10.0.0.0"

    def test_slash31_last_host(self):
        assert subnet("10.0.0.0/31").last_usable_host == "10.0.0.1"

    def test_slash32_usable_hosts(self):
        # Host route — exactly 1 address
        assert subnet("192.168.1.1/32").usable_hosts == 1

    def test_slash32_total_hosts(self):
        assert subnet("192.168.1.1/32").total_hosts == 1

    def test_slash32_network_equals_broadcast(self):
        info = subnet("192.168.1.1/32")
        assert info.network_address == info.broadcast_address == "192.168.1.1"

    def test_slash32_first_host_is_address(self):
        assert subnet("192.168.1.1/32").first_usable_host == "192.168.1.1"

    def test_slash32_last_usable_host_is_none(self):
        assert subnet("192.168.1.1/32").last_usable_host is None

    def test_slash0_default_route(self):
        info = subnet("0.0.0.0/0")
        assert info.total_hosts == 2**32
        assert info.usable_hosts == 2**32 - 2
        assert info.network_address == "0.0.0.0"
        assert info.broadcast_address == "255.255.255.255"


# ---------------------------------------------------------------------------
# Loopback
# ---------------------------------------------------------------------------


class TestLoopback:
    def test_is_loopback(self):
        assert subnet("127.0.0.0/8").is_loopback is True

    def test_is_private_matches_stdlib_behavior(self):
        # Python's ipaddress module considers 127.0.0.0/8 private (RFC 6890).
        # We expose the stdlib value directly without overriding it.
        result = subnet("127.0.0.0/8")
        # is_private should match ipaddress.ip_network("127.0.0.0/8").is_private
        import ipaddress
        expected = ipaddress.ip_network("127.0.0.0/8").is_private
        assert result.is_private is expected

    def test_loopback_class(self):
        assert subnet("127.0.0.0/8").ip_class == "A"


# ---------------------------------------------------------------------------
# IP classes
# ---------------------------------------------------------------------------


class TestIPClass:
    def test_class_a(self):
        assert subnet("10.0.0.0/8").ip_class == "A"

    def test_class_b(self):
        assert subnet("172.16.0.0/16").ip_class == "B"

    def test_class_c(self):
        assert subnet("192.168.0.0/24").ip_class == "C"

    def test_class_d_multicast(self):
        assert "D" in subnet("224.0.0.0/4").ip_class

    def test_class_e_reserved(self):
        assert "E" in subnet("240.0.0.0/4").ip_class


# ---------------------------------------------------------------------------
# contains_ip / SubnetInfo.contains
# ---------------------------------------------------------------------------


class TestContainsIP:
    def test_ip_in_subnet(self):
        assert contains_ip("192.168.1.0/24", "192.168.1.100") is True

    def test_ip_not_in_subnet(self):
        assert contains_ip("192.168.1.0/24", "192.168.2.1") is False

    def test_network_address_in_subnet(self):
        assert contains_ip("10.0.0.0/8", "10.0.0.0") is True

    def test_broadcast_in_subnet(self):
        assert contains_ip("10.0.0.0/8", "10.255.255.255") is True

    def test_ip_just_outside_upper_bound(self):
        assert contains_ip("192.168.1.0/24", "192.168.2.0") is False

    def test_ip_just_outside_lower_bound(self):
        assert contains_ip("192.168.1.0/24", "192.168.0.255") is False

    def test_slash30_member(self):
        assert contains_ip("10.1.1.0/30", "10.1.1.2") is True

    def test_slash30_non_member(self):
        assert contains_ip("10.1.1.0/30", "10.1.1.4") is False

    def test_via_subnet_info_contains(self):
        info = calculate_subnet("172.16.0.0/12")
        assert info.contains("172.20.50.1") is True
        assert info.contains("172.32.0.1") is False


# ---------------------------------------------------------------------------
# Invalid input
# ---------------------------------------------------------------------------


class TestInvalidInput:
    def test_invalid_cidr_raises(self):
        with pytest.raises(ValueError, match="Invalid CIDR"):
            calculate_subnet("not-a-cidr")

    def test_bare_ip_treated_as_slash32(self):
        # ipaddress.ip_network accepts a bare IP and treats it as a /32 host
        # route.  We propagate that behaviour rather than rejecting it.
        info = calculate_subnet("192.168.1.1")
        assert info.prefix_length == 32
        assert info.total_hosts == 1

    def test_out_of_range_octet_raises(self):
        with pytest.raises(ValueError):
            calculate_subnet("256.0.0.0/8")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            calculate_subnet("")

    def test_negative_prefix_raises(self):
        with pytest.raises(ValueError):
            calculate_subnet("10.0.0.0/-1")


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------


class TestSerialisation:
    def test_to_dict_has_expected_keys(self):
        d = subnet("192.168.1.0/24").to_dict()
        expected_keys = {
            "cidr", "network_address", "broadcast_address",
            "subnet_mask", "wildcard_mask", "prefix_length",
            "total_hosts", "usable_hosts", "first_usable_host",
            "last_usable_host", "ip_class", "is_private", "is_loopback",
        }
        assert expected_keys == set(d.keys())

    def test_to_json_is_valid_json(self):
        import json
        raw = subnet("10.0.0.0/8").to_json()
        parsed = json.loads(raw)
        assert parsed["cidr"] == "10.0.0.0/8"

    def test_to_json_indent(self):
        raw = subnet("10.0.0.0/8").to_json(indent=4)
        # 4-space indented JSON has leading spaces on inner lines
        assert "    " in raw
