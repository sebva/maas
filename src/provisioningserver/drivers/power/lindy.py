"""Lindy RS232 Power Driver.

Sébastien Vaucher, University of Neuchâtel, November 2017
"""
import re
import time

import serial

__all__ = []

from provisioningserver.drivers import (
    make_setting_field,
    SETTING_SCOPE,
    make_ip_extractor
)
from provisioningserver.drivers.power import (
    PowerDriver,
    PowerConnError
)


class LindyPowerDriver(PowerDriver):
    name = 'lindy'
    description = "Lindy IPower"
    settings = [
        make_setting_field('power_address', "Write IP of MAAS controller here", required=True),
        make_setting_field(
            'node_outlet', "PDU node outlet number (1-C)", scope=SETTING_SCOPE.NODE, required=True),
    ]
    ip_extractor = make_ip_extractor('power_address')

    def detect_missing_packages(self):
        return []

    def query_states(self):
        statuses = dict()
        with serial.Serial("/dev/ttyS0", 115200, timeout=2) as ser:
            time.sleep(1)
            ser.reset_output_buffer()
            ser.reset_input_buffer()

            ser.write(b"\r\n")
            lines = ser.readlines()

            regex = re.compile(r"<([1-9A-C])> (ON|OFF)\s*")
            for line in lines:
                matcher = regex.match(line.decode().rstrip())
                if matcher is not None:
                    statuses[matcher.group(1)] = matcher.group(2).lower()
            ser.write(b"\x1b")

        return statuses

    def toggle_port(self, port):
        with serial.Serial("/dev/ttyS0", 115200, timeout=2) as ser:
            time.sleep(1)
            ser.reset_output_buffer()
            ser.reset_input_buffer()

            ser.write(b"\r\n")
            ser.write(port.encode())
            ser.write(b"\x1b")
            time.sleep(1)

    def power_on(self, system_id, context):
        port = context['node_outlet']
        try:
            if self.query_states()[port] == 'on':
                self.toggle_port(port)
            self.toggle_port(port)
        except KeyError as ex:
            raise PowerConnError(ex)

    def power_off(self, system_id, context):
        try:
            port = context['node_outlet']
            if self.query_states()[port] == 'on':
                self.toggle_port(port)
        except KeyError as ex:
            raise PowerConnError(ex)

    def power_query(self, system_id, context):
        port = context['node_outlet']
        try:
            state = self.query_states()[port]

            if state in ("on", "off"):
                return state
            else:
                raise PowerConnError()
        except KeyError as ex:
            raise PowerConnError(ex)
