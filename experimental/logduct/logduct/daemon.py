#!/usr/bin/env python
from __future__ import print_function
import os, asyncore, socket, struct, ctypes, array, re, errno, argparse, time
import stat, sys, signal, json
from collections import namedtuple
from sendmsg import recvmsg, SCM_RIGHTS, SCM_CREDENTIALS, SO_PASSCRED, SO_PEERCRED
from datetime import datetime
from subprocess import Popen, PIPE

if os.getenv("COVERAGE_PROCESS_START"):
    import coverage
    coverage.process_startup()

Cred = namedtuple("Cred", "pid uid gid")
Metadata = namedtuple("Metadata", "time pid comm unit")

def is_a_socket(fd):
    """tests if the given file descriptor is a socket"""
    return stat.S_ISSOCK(os.fstat(fd).st_mode)

def slurp(path):
    """Read the contents of a file, stripping leading and trailing whitespace."""
    with open(path) as f:
        return f.read().strip()

def parse_ancdata(ancdata):
    """Parse unix socket ancilliary data that was received by recvmsg. Returns
    (fds, cred) where fds is a list of received file descriptors and cred is
    the sending processes' pid, uid and gid.  Either or both may be None.
    """
    fds = None
    cred = None
    for level, type_, value in ancdata:
        if level == socket.SOL_SOCKET:
            if type_ == SCM_RIGHTS:
                fds = array.array('i', value)
            elif type_ == SCM_CREDENTIALS:
                cred = Cred(*struct.unpack('3i', value))
    return fds, cred

def comm_for_pid(pid):
    """Retrieve the process name for a given process id."""
    try:
        return slurp('/proc/%d/comm' % pid)
    except IOError:
        return None

def unit_for_pid(pid):
    """Work out the systemd unit for a process by reading its cgroup."""
    try:
        cgroup = slurp('/proc/%d/cgroup' % pid)
        match = re.search("1:name=systemd:/system.slice/(?:jvm:)?(.+?).service", cgroup)
        return match.group(1) if match else None
    except IOError:
        return None

def format_prefix(meta):
    """Format log metadata as a prefix to be prepended to log lines."""
    ts = meta.time.strftime('%H:%M:%S.%f')[:-3]
    if meta.comm and meta.pid:
        return "%s %s[%d]: " % (ts, meta.comm, meta.pid)
    else:
        return ts + ": "

def getpeercred(sock):
    """Returns the pid, uid and gid of the other end of a socket."""
    data = sock.getsockopt(socket.SOL_SOCKET, SO_PEERCRED,
            struct.calcsize('3i'))
    return Cred(*struct.unpack('3i', data))

class LogWriter:
    """A date rotated log file"""

    def __init__(self, log_dir, unit, logname, start_of_line=True):
        self.unit = unit
        self.logname = logname
        self.file = None
        self.path = None
        self.start_of_line = start_of_line
        self.template = "{log_dir}/{unit}/%Y%m/{logname}.%Y-%m-%d.log".format(
                log_dir=log_dir, unit=unit, logname=logname)
        self.link_path = "{log_dir}/{unit}/{logname}.log".format(
                log_dir=log_dir, unit=unit, logname=logname)
        self.last_active = time.time()

    def save(self):
        return {
            "unit": self.unit,
            "logname": self.logname,
            "start_of_line": self.start_of_line,
        }

    def open_file(self, now):
        """(Re)open the log file, creating parent directories as needed."""
        path = now.strftime(self.template)
        if path != self.path:
            if self.file is not None:
                self.file.close()
            self.path = path
            try:
                self.file = open(path, 'a', 0)
            except IOError as e:
                if e.errno == errno.ENOENT:
                    os.makedirs(os.path.dirname(path))
                    self.file = open(path, 'a', 0)

            self.update_link()

    def update_link(self):
        """Create or update a symlink to point at the latest rotation."""
        try:
            os.symlink(self.path, self.link_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                os.unlink(self.link_path)
                os.symlink(self.path, self.link_path)

    def write(self, data, meta):
        """Write a string to the logfile, prefixing new lines with metadata."""
        self.last_active = time.time()
        self.open_file(now=meta.time)
        prefix = format_prefix(meta)

        if self.start_of_line:
            print(prefix, end="", file=self.file)

        if data.endswith("\n"):
            print(data[:-1].replace('\n', '\n' + prefix), file=self.file)
            self.start_of_line = True
        else:
            print(data.replace('\n', '\n' + prefix), end="", file=self.file)
            self.start_of_line = False

    def close(self):
        """Close the log file. Note that the next invocation of write() will
        reopen it.
        """
        if self.file is not None:
            self.file.close()
            self.file = None

    def key(self):
        return (self.unit, self.logname)


class LogManager:
    """Tracks open log files"""

    def __init__(self, log_dir, max_idle, trust_blindly=False, writers=[]):
        self.writers = {}
        self.log_dir = log_dir
        self.max_idle = max_idle
        self.last_idle_check = 0
        self.trust_blindly = trust_blindly

        for wstate in writers:
            writer = LogWriter(log_dir=self.log_dir, **wstate)
            self.writers[writer.key()] = writer

    def get(self, unit, logname):
        """Retrieves a LogWriter, creating it if necessary"""
        assert unit is not None
        writer = self.writers.get((unit, logname))
        if writer is None:
            writer = LogWriter(self.log_dir, unit, logname)
            self.writers[writer.key()] = writer
        return writer

    def close_idle(self):
        """Closes any LogWriters which have been idle for max_idle secondss"""
        now = time.time()
        if now < self.last_idle_check + self.max_idle:
            return
        for key, writer in self.writers.items():
            if writer.last_active + self.max_idle < now:
                writer.close()
                del self.writers[key]
        self.last_idle_check = now

    def close_all(self):
        """Closes all LogWriters"""
        for key, writer in self.writers.items():
            writer.close()
            del self.writers[key]


    def save(self):
        return {
            "log_dir": self.log_dir,
            "max_idle": self.max_idle,
            "trust_blindly": self.trust_blindly,
            "writers": [writer.save() for writer in self.writers.itervalues()],
        }

class PipeHandler(asyncore.file_dispatcher):
    """Handles secondary log messages from sources that do not work with
    sockets.  Unforunately there's no (fast) way to get the pid of the
    other end of a pipe so we don't log any process metadata.
    """

    def __init__(self, log_manager, fd, unit, logname):
        asyncore.file_dispatcher.__init__(self, fd)
        os.close(fd)

        self.log_manager = log_manager
        self.unit = unit
        self.logname = logname

    def handle_read(self):
        """Called when data is available for reading."""
        data = self.recv(8192)
        meta = Metadata(time=datetime.now(), pid=None,
            comm=None, unit=self.unit)

        if meta.unit is not None:
            log = self.log_manager.get(meta.unit, self.logname)
            log.write(data, meta)

    def writable(self):
        """Prevent asyncore for waking up constantly: we never need to write"""
        return False

    def save(self):
        return {
            "type": "PipeHandler",
            "fd": self.socket.fileno(),
            "unit": self.unit,
            "logname": self.logname
        }

class Handler(asyncore.dispatcher):
    """Handles incoming log messages from applications."""

    def __init__(self, log_manager, sock=None, fd=None, unit=None, header_buffer=""):
        if fd is not None:
            sock = socket.fromfd(fd, socket.AF_UNIX, socket.SOCK_STREAM)
            os.close(fd)
        sock.setsockopt(socket.SOL_SOCKET, SO_PASSCRED, 1)
        asyncore.dispatcher.__init__(self, sock)
        self.log_manager = log_manager
        self.header_buffer = header_buffer
        cred = getpeercred(sock)
        self.unit = unit or unit_for_pid(cred.pid)

    def writable(self):
        """Prevent asyncore for waking up constantly: we never need to write"""
        return False

    def handle_read(self):
        """Called when data is available for reading."""
        data, ancdata, _, _ = recvmsg(self.socket, 65536, 4096)

        if not data:
            return self.handle_close()

        fds, cred = parse_ancdata(ancdata)

        if self.header_buffer is not None:
            self.header_buffer += data

            linefeed = self.header_buffer.find('\n')
            if linefeed == -1:
                return

            header = json.loads(self.header_buffer[:linefeed])
            data = self.header_buffer[linefeed + 1:]
            self.header_buffer = None

            self.handle_header(fds, header)

            if not data:
                return

        meta = Metadata(time=datetime.now(), pid=cred.pid,
            comm=(comm_for_pid(cred.pid) or "unknown"),
            unit=(unit_for_pid(cred.pid) or self.unit))

        if meta.unit is not None:
            log = self.log_manager.get(meta.unit, "stdio")
            log.write(data, meta)

    def handle_header(self, fds, header):
        if self.log_manager.trust_blindly and self.unit is None:
            self.unit = header['unit']

        if fds:
            lognames = header.get("lognames", [])
            for i, fd in enumerate(fds):
                if i < len(lognames):
                    logname = lognames[i]
                else:
                    logname = "stdio"
                PipeHandler(self.log_manager, fd, self.unit, logname)

    def writable(self):
        """Prevent asyncore for waking up constantly: we never need to write"""
        return False

    def save(self):
        """Save state for process reloading"""
        return {
            "type": "Handler",
            "fd": self.socket.fileno(),
            "unit": self.unit,
        }

class Server(asyncore.dispatcher):
    """Listens for new logduct connections and accepts them."""
    def __init__(self, log_manager, sock=None, fd=None):
        if fd is not None:
            sock = socket.fromfd(fd, socket.AF_UNIX, socket.SOCK_STREAM)
            os.close(fd)
        if isinstance(sock, str):
            asyncore.dispatcher.__init__(self)
            self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.bind(sock)
            self.listen(5)
        else:
            asyncore.dispatcher.__init__(self, sock)
        self.log_manager = log_manager

    def handle_accept(self):
        """Called when new connections are incoming. Accepts them and creates
        a handler for them."""
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            Handler(self.log_manager, sock)

    def save(self):
        """Save state for process reloading"""
        return {
            "type": "Server",
            "fd": self.socket.fileno()
        }

def parse_arguments():
    parser = argparse.ArgumentParser(
            description="Listens on a unix socket for application log messages and writes them to a rotated file.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-s", "--socket", default="/run/logduct.sock", help="unix socket to listen on")
    parser.add_argument("-d", "--logdir", default="/logs", help="directory to write logs under")
    parser.add_argument("--idle", default=60, metavar='SECS', type=float, help="seconds after which idle log files will be closed")
    parser.add_argument("--trust-blindly", action='store_true', help="accept without verifying the unit name the client gives us")
    # --restore is for internal use only when reloading the daemon
    parser.add_argument("--restore", action='store_true', help=argparse.SUPPRESS)
    return parser.parse_args()

class Daemon:
    def __init__(self):
        args = parse_arguments()
        if args.restore:
            self.restore()
        else:
            self.init(args)
        signal.signal(signal.SIGHUP, self.handle_hup)

    def init(self, args):
        """Initialise everything afresh, not called when restoring."""
        self.log_manager = LogManager(args.logdir, args.idle, args.trust_blindly)
        if is_a_socket(sys.stdin.fileno()):
            sock = socket.fromfd(sys.stdin.fileno(), socket.AF_UNIX, socket.SOCK_STREAM)
            sys.stdin.close()
        else:
            sock = args.socket
        self.server = Server(self.log_manager, sock)

    def restore(self):
        """Reconstruct all our state from a json string."""
        state = json.loads(sys.stdin.read())
        self.log_manager = LogManager(**state["log_manager"])

        for dstate in state["dispatchers"]:
            dtype = dstate.pop("type")
            if dtype == 'Server':
                self.server = Server(self.log_manager, **dstate)
            elif dtype == 'Handler':
                Handler(self.log_manager, **dstate)
            elif dtype == 'PipeHandler':
                PipeHandler(self.log_manager, **dstate)

        # kill our parent and take their place so that nobody notices
        if "parent_to_kill" in state:
            os.kill(state["parent_to_kill"], signal.SIGINT)
            

    def handle_hup(self, signum, frame):
        pid = os.getpid()
        print('Reloading logductd...' + str(pid))
        state = self.save()
        
        # prevent log file fds from being inherited
        # our successor can reopen them
        self.log_manager.close_all()

        print('State:', state)

        state["parent_to_kill"] = os.getpid()

        # The child will send us SIGINT to let us know its taken over.
        old_sigint_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

        try:
            child = Popen([__file__, '--restore'], stdin=PIPE, close_fds=False)
            child.communicate(json.dumps(state))
            retcode = child.wait()
            print("Reloading failed, child returned ", retcode)
        finally:
            signal.signal(signal.SIGINT, old_sigint_handler)

    def save(self):
        """Save the state of all open dispatchers"""
        state = {
            "log_manager": self.log_manager.save(),
            "dispatchers": [dispatcher.save() for dispatcher
                            in asyncore.socket_map.itervalues()
                            if hasattr(dispatcher, "save")],
        }
        return state

    def loop(self):
        while asyncore.socket_map:
            asyncore.loop(timeout=self.log_manager.max_idle, count=1)
            self.log_manager.close_idle()

def main():
    Daemon().loop()

if __name__ == '__main__': main()
