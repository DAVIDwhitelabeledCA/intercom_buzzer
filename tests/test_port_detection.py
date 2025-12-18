import platform
import types

import pytest

import modem


def test_detect_default_port_linux(monkeypatch):
    monkeypatch.setattr(platform, 'system', lambda: 'Linux')
    monkeypatch.setattr('glob.glob', lambda pattern: ['/dev/ttyUSB0'] if 'ttyUSB' in pattern else [])
    assert modem.detect_default_port() == '/dev/ttyUSB0'


def test_detect_default_port_macos(monkeypatch):
    monkeypatch.setattr(platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr('glob.glob', lambda pattern: ['/dev/cu.usbserial-XYZ'] if 'cu.usbserial' in pattern else [])
    assert modem.detect_default_port() == '/dev/cu.usbserial-XYZ'


def test_detect_default_port_none(monkeypatch):
    monkeypatch.setattr(platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr('glob.glob', lambda pattern: [])
    assert modem.detect_default_port() is None
