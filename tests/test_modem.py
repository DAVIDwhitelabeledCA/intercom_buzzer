import pytest

from modem import is_ring_line


def test_is_ring_line_basic():
    assert is_ring_line("RING")
    assert is_ring_line("  ring  ")
    assert is_ring_line("+CMTI: \"SM\",1\r\nRING\r\n")


def test_is_ring_line_false():
    assert not is_ring_line("")
    assert not is_ring_line("NO CARRIER")
    assert not is_ring_line("some other text")
