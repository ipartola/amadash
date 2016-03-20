from __future__ import unicode_literals, print_function, absolute_import, division

import logging, logging.handlers
import sys
import os
import atexit
import errno
import signal
import pwd
from ConfigParser import RawConfigParser

from .sniffer import get_sniffer
from .daemon import drop_privileges, write_pid, daemonize
from .detector import Detector

from .ext.groper import define_opt, options, init_options, OptionsError, usage

define_opt('main', 'help', type=bool, cmd_name='help', cmd_short_name='h', cmd_group='help', is_help=True)

define_opt('main', 'config', cmd_name='config', cmd_short_name='c', is_config_file=True, cmd_only=True)
define_opt('main', 'pidfile', cmd_name='pid', cmd_short_name='p', default='')
define_opt('main', 'daemon', type=bool, cmd_name='daemon', cmd_short_name='d')
define_opt('main', 'user', cmd_name='user', cmd_short_name='u', default=None)
define_opt('main', 'interface', cmd_name='interface', cmd_short_name='i', default=None)
define_opt('main', 'allow_sniffer_fallback', type=bool)

define_opt('log', 'filename', cmd_name='log', cmd_short_name='l', default='')
define_opt('log', 'backup_count', type=int, default=14)
define_opt('log', 'when', default='midnight')
define_opt('log', 'level', default='INFO')

make_shutdown_handler = lambda sniffer, detector: lambda signum, frame: shutdown(signum, sniffer, detector)


def shutdown(signum, sniffer, detector):
    '''Perform a gracefully shutdown.'''

    if signum:
        logging.getLogger().info('Recevied signal {}. Shutting down.'.format(signum))
    sniffer.shutdown()
    detector.shutdown()


def setup_logging():
    '''Sets up internal logging. Run this once at startup.'''

    logger = logging.getLogger()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    if options.log.filename:
        handler = logging.handlers.TimedRotatingFileHandler(filename=options.log.filename, when=options.log.when, backupCount=options.log.backup_count, utc=True)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if not options.main.daemon:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    level = getattr(logging, options.log.level.upper())
    logger.setLevel(level)


def exit_handler():
    '''Cleanup routine. This function runs right before the daemon is about to exit.'''

    if options.main.pidfile:
        try:
            os.unlink(options.main.pidfile)
        except OSError as e:
            if e.errno == errno.ENOENT:
                pass # No such file or directory


def create_dirs():
    '''Pre-creates necessary directories and chowns them if necessary.'''

    dirs = []
    if options.log.filename:
        dirs.append(os.path.dirname(os.path.abspath(options.log.filename)))

    pwnam = pwd.getpwnam(options.main.user)
    uid, gid = (pwnam[2], pwnam[3])

    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            if uid != os.getuid() or gid != os.getgid():
                os.chown(d, uid, gid)


def get_buttons():
    cp = RawConfigParser()

    # NOTE: apparently, cp.read() will happily do nothing if the file doesn't exist.
    # Thus, we use cp.readfp() instead, letting open() fail if something is wrong.
    f = open(options.main.config, 'r')
    cp.readfp(f, options.main.config)
    f.close()

    # First we add all root facilities
    for section in cp.sections():
        if section.startswith('button:'):
            yield {
                'name': cp.get(section, 'name').strip(),
                'mac': cp.get(section, 'mac').strip().lower(),
                'action': cp.get(section, 'action'),
            }


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

    if options.main.daemon:
        daemonize()

    create_dirs()

    if options.main.pidfile:
        write_pid(options.main.pidfile)
        atexit.register(exit_handler)

    try:
        sniffer = get_sniffer(options.main.interface, options.main.allow_sniffer_fallback)
    except Exception as e:
        sys.stderr.write("Error: {}\n".format(e))
        sys.exit(os.EX_CONFIG)

    if options.main.user:
        drop_privileges(options.main.user)
    
    setup_logging()

    detector = Detector(sniffer)
    for button in get_buttons():
        detector.add_button(button['mac'], button['name'], button['action'])

    signal_handler = make_shutdown_handler(sniffer, detector)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.getLogger().info('Startup finished. Monitoring button presses.')
    detector.run()


if __name__ == '__main__':
    main()

