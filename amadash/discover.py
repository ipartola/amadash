from __future__ import unicode_literals, print_function, absolute_import, division

import logging, logging.handlers
import sys
import os
import signal

from .sniffer import get_sniffer

from .ext.groper import define_opt, options, init_options, OptionsError, usage

define_opt('main', 'help', type=bool, cmd_name='help', cmd_short_name='h', cmd_group='help', is_help=True)
define_opt('main', 'interface', cmd_name='interface', cmd_short_name='i', default=None)
define_opt('main', 'allow_sniffer_fallback', type=bool)

make_shutdown_handler = lambda sniffer, detector: lambda signum, frame: shutdown(signum, sniffer, detector)


def shutdown(signum, sniffer, detector):
    '''Perform a gracefully shutdown.'''

    if signum:
        logging.getLogger().info('Recevied signal {}. Shutting down.'.format(signum))
    sniffer.shutdown()


def setup_logging():
    '''Sets up internal logging. Run this once at startup.'''

    logger = logging.getLogger()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)


def handle_button_press(mac, proto):
    if proto == 8:
        logging.getLogger().info('Button press detected: {}'.format(mac))


def main():
    try:
        init_options()
    except OptionsError as e:
        sys.stderr.write("Error: {0}\n\n".format(e))
        sys.stderr.write(usage())
        sys.stderr.write("\n");
        sys.stderr.flush()
        sys.exit(os.EX_CONFIG)

    if os.getuid() != 0:
        sys.stderr.write("You must run this program as root!\n\n")
        sys.stderr.write(usage())
        sys.stderr.write("\n");
        sys.stderr.flush()
        sys.exit(os.EX_CONFIG)

    try:
        sniffer = get_sniffer(options.main.interface, options.main.allow_sniffer_fallback)
    except Exception as e:
        sys.stderr.write("Error: {}\n".format(e))
        sys.exit(os.EX_CONFIG)

    setup_logging()

    signal_handler = make_shutdown_handler(sniffer, None)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.getLogger().info('Startup finished. Monitoring button presses.')

    sniffer.sniff_broadcast(handle_button_press)


if __name__ == '__main__':
    main()

