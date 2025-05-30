"""Device manager for inputs.
This module provides a way to access all connected and detectible user input
devices, such as gamepads.
"""

import os
import glob
from warnings import warn
import ctypes

from .constants import (
    XINPUT_DLL_NAMES,
    XINPUT_ERROR_DEVICE_NOT_CONNECTED,
    XINPUT_ERROR_SUCCESS,
)

from .libi.system import WIN
from .devices.gamepad.gamepad import GamePad
from .devices.base import OtherDevice
from .devices.gamepad._win import XinputState


class DeviceManager(object):  # pylint: disable=useless-object-inheritance
    """Provides access to all connected and detectible user input
    devices."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        self._raw = []
        self.gamepads = []
        self.other_devices = []
        self.all_devices = []
        self.microbits = []
        self.xinput = None
        self.xinput_dll = None
        self._post_init()

    def _post_init(self):
        """Call the find devices method for the relevant platform."""
        if WIN:
            self._find_devices_win()
        else:
            self._find_devices()
        self._update_all_devices()

    def _update_all_devices(self):
        """Update the all_devices list."""
        self.all_devices = []
        self.all_devices.extend(self.gamepads)
        self.all_devices.extend(self.other_devices)

    def _parse_device_path(self, device_path, char_path_override=None):
        """Parse each device and add to the approriate list."""

        # 1. Make sure that we can parse the device path.
        try:
            device_type = device_path.rsplit("-", 1)[1]
        except IndexError:
            warn(
                "The following device path was skipped as it could "
                "not be parsed: %s" % device_path,
                RuntimeWarning,
            )
            return

        # 2. Make sure each device is only added once.
        realpath = os.path.realpath(device_path)
        if realpath in self._raw:
            return
        self._raw.append(realpath)

        # 3. All seems good, append the device to the relevant list.
        if device_type == "joystick":
            self.gamepads.append(GamePad(self, device_path, char_path_override))
        else:
            self.other_devices.append(
                OtherDevice(self, device_path, char_path_override)
            )

    def _find_xinput(self):
        """Find most recent xinput library."""
        for dll in XINPUT_DLL_NAMES:
            try:
                self.xinput = getattr(ctypes.windll, dll)
            except OSError:
                pass
            else:
                # We found an xinput driver
                self.xinput_dll = dll
                break
        else:
            # We didn't find an xinput library
            warn("No xinput driver dll found, gamepads not supported.", RuntimeWarning)

    def _find_devices_win(self):
        """Find devices on Windows."""
        self._find_xinput()
        if self.xinput:
            self._detect_gamepads()

    def _detect_gamepads(self):
        """Find gamepads."""
        state = XinputState()
        # Windows allows up to 4 gamepads.
        for device_number in range(4):
            res = self.xinput.XInputGetState(device_number, ctypes.byref(state))
            if res == XINPUT_ERROR_SUCCESS:
                # We found a gamepad
                device_path = (
                    "/dev/input/by_id/"
                    + "usb-Microsoft_Corporation_Controller_%s-event-joystick"
                    % device_number
                )
                self.gamepads.append(GamePad(self, device_path))
                continue
            if res != XINPUT_ERROR_DEVICE_NOT_CONNECTED:
                raise RuntimeError(
                    "Unknown error %d attempting to get state of device %d"
                    % (res, device_number)
                )

    def _find_devices(self):
        """Find available devices."""
        self._find_by("id")
        self._find_by("path")

    def _find_by(self, key):
        """Find devices."""
        by_path = glob.glob("/dev/input/by-{key}/*-event-*".format(key=key))
        for device_path in by_path:
            self._parse_device_path(device_path)

    def __iter__(self):
        return iter(self.all_devices)

    def __getitem__(self, index):
        try:
            return self.all_devices[index]
        except IndexError:
            raise IndexError("list index out of range")
