# Copyright 2015 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Wake on LAN with SSH backdoor Power Driver."""
import subprocess

__all__ = []

from provisioningserver.drivers import (
    IP_EXTRACTOR_PATTERNS,
    make_ip_extractor,
    make_setting_field,
)
from provisioningserver.drivers.power import PowerDriver
from provisioningserver.utils import shell

REQUIRED_PACKAGES = [["wakeonlan", "wakeonlan"]]


class WakeOnLanDriver(PowerDriver):
    name = 'wakeonlan'
    chassis = False
    description = "Wake on LAN with SSH backdoor"
    settings = [
        make_setting_field('power_address', "Power IP address", required=True),
        make_setting_field('power_mac', "Power MAC address", required=True),
        make_setting_field('power_user', "Power username", required=True),
    ]
    ip_extractor = make_ip_extractor('power_address', IP_EXTRACTOR_PATTERNS.URL)

    def detect_missing_packages(self):
        missing_packages = set()
        for binary, package in REQUIRED_PACKAGES:
            if not shell.has_command_available(binary):
                missing_packages.add(package)
        return list(missing_packages)

    def power_on(self, system_id, context):
        subprocess.check_call(["wakeonlan", context.get("power_mac")])

    def power_off(self, system_id, context):
        subprocess.call(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
             "%s@%s" % (context.get("power_user"), context.get("power_address")), "sudo", "poweroff"])

    def power_query(self, system_id, context):
        errcode = subprocess.call(["ping", "-q", "-c", "1", "-W", "2", context.get("power_address")])
        if errcode == 0:
            return 'on'
        else:
            return 'off'
