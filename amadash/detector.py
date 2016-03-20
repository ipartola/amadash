from __future__ import unicode_literals, print_function, absolute_import, division

import time
import subprocess
import os
import logging

from .daemon import daemonize
from .ext.groper import define_opt, options

define_opt('main', 'button_timeout', type=float, default=10.0)


class Detector(object):
    def __init__(self, sniffer):
        self.buttons = {}
        self.sniffer = sniffer

    def add_button(self, mac, name, action):
        mac = mac.strip().lower()
        self.buttons[mac] = {
            'mac': mac,
            'name': name.strip(),
            'action': action,
            'last_seen': 0,
        }

    def run(self):
        self.sniffer.sniff(self.buttons.keys(), self.handle_button_traffic)

    def handle_button_traffic(self, mac, eth_protocol):
        button = self.buttons.get(mac)
        if not button:
            return

        now = time.time()
        time_delta = now - button['last_seen']
        button['last_seen'] = now
        if time_delta < options.main.button_timeout:
            return

        logging.getLogger().info('Button press detected: {} [{}].'.format(button['name'], button['mac']))
        action = button['action']
        env = dict(os.environ)
        env.update({
            'BUTTON_NAME': button['name'],
            'BUTTON_MAC': button['mac'],
        })

        pid = None
        try:
            pid = os.fork()
        except OSError as e:
            logging.getLogger().info("Could not fork for action: [{}] {}".format(e.errno, e.strerr))

        if pid == 0:
            daemonize(False)
            subprocess.Popen(action, shell=True, env=env).wait()
            os._exit(0)

    def shutdown(self):
        '''Currently a no-op.'''
        pass
