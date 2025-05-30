"""High level input utilities for reading from gamepads."""

from . import DeviceManager
from .libi.errors import UnpluggedError

devices = DeviceManager()  # pylint: disable=invalid-name


def get_gamepad():
    """Get a single action from a gamepad."""
    try:
        gamepad = devices.gamepads[0]
    except IndexError:
        raise UnpluggedError("No gamepad found.")
    return gamepad.read()
