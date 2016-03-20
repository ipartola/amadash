
import os, sys, resource, errno, pwd

MAXFD = 2048


def close_open_files():
    '''Closes all open files. Useful after a fork.'''

    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if maxfd == resource.RLIM_INFINITY:
        maxfd = MAXFD

    for fd in reversed(range(maxfd)):
        try:
            os.close(fd)
        except OSError, e:
            if e.errno == errno.EBADF:
                pass # File not open
            else:
                raise Exception("Failed to close file descriptor %d: %s" % (fd, e))


def daemonize(double_fork=True):
    '''Puts process in the background using usual UNIX best practices.'''

    try:
        os.umask(0o22)
    except Exception as e:
        raise Exception("Unable to change file creation mask: %s" % e)

    os.chdir('/')

    # First fork
    if double_fork:
        try:
            pid = os.fork()
            if pid > 0:
                os._exit(0)
        except OSError as e:
            raise Exception("Error on first fork: [%d] %s" % (e.errno, e.strerr,))

    os.setsid()

    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)
    except OSError as e:
        raise Exception("Error on second fork: [%d] %s" % (e.errno, e.strerr,))

    close_open_files()
    os.dup2(os.open(os.devnull, os.O_RDWR), sys.stdin.fileno())
    os.dup2(os.open(os.devnull, os.O_RDWR), sys.stdout.fileno())
    os.dup2(os.open(os.devnull, os.O_RDWR), sys.stderr.fileno())


def write_pid(filename):
    '''Atomically writes a pid file, or fails if the file already exists.'''

    fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o644)
    os.write(fd, str(os.getpid()))
    os.close(fd)


def drop_privileges(user):
    '''If running as root, drop process privileges to the given user and user's main group.'''

    if os.getuid() == 0:
        pwnam = pwd.getpwnam(user)
        running_uid, running_gid = (pwnam[2], pwnam[3])

        if running_gid != os.getgid():
            os.setgid(running_gid)

        if running_uid != os.getuid():
            os.setuid(running_uid)

