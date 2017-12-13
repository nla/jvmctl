import argparse, ssl, socket, sys, glob, re, os, json, time
from datetime import datetime
from dateutil import tz

TZLOCAL = tz.tzlocal()

class Syslog:
    def __init__(self, options):
        self.options = options
        self.sock = None
        self.connect()

    def connect(self):
        if not self.options.host:
            return

        if self.sock is not None:
            self.sock.close()

        self.sock = ssl.wrap_socket(socket.socket(),
                                    keyfile=self.options.keyfile,
                                    certfile=self.options.certfile,
                                    ca_certs=self.options.ca_certs,
                                    cert_reqs=ssl.CERT_NONE if self.options.insecure else ssl.CERT_REQUIRED)
        self.sock.connect((self.options.host, self.options.port))

    def send(self, msg, timestamp, host=socket.getfqdn(), app_name="-", procid="-", msgid="-", structured_data="-"):
        payload = " ".join(["<1>1", timestamp.isoformat(), host, app_name, procid, msgid, structured_data, msg])
        if self.sock is not None:
            self.sock.send(str(len(payload)) + " " + payload)
        else:
            print payload


def parse_options():
    parser = argparse.ArgumentParser(description="Tail log files and send to a syslog server")
    parser.add_argument("--host", help='hostname of syslog server')
    parser.add_argument("--port", help='port of syslog server', type=int)
    parser.add_argument("--ca-certs", help='certificate of CA to trust')
    parser.add_argument("--certfile", help='client certificate to identify as')
    parser.add_argument("--keyfile", help='key corresponding to the client certificate')
    parser.add_argument("--insecure", help='disable server certificate validation', action='store_true')
    parser.add_argument("--verbose", "-v", action='store_true')
    parser.add_argument("--statefile", help='file to save and load current log reading positions in')
    parser.add_argument("--path-regex", type=re.compile, default=r".*/(?P<app_name>[^/]+)/\d+/stdio\.(?P<date>\d\d\d\d-\d\d-\d\d)\.log")
    parser.add_argument("--line-regex", type=re.compile, default=r"(?P<time>\d\d:\d\d:\d\d\.\d\d\d) (?P<procid>[^ *]+): (?P<msg>.*)")
    parser.add_argument("--date-format", default="%Y-%m-%d")
    parser.add_argument("--time-format", default="%H:%M:%S.%f")
    parser.add_argument("--interval", "-i", default=0.0, type=float, help='interval in seconds to repeat at')
    parser.add_argument("--reset", action="store_true", help="reset state to end of all files")
    parser.add_argument("fileglob")
    return parser.parse_args(sys.argv[1:])


def load_state(path):
    if path is None or not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_state(state, path):
    if path is None: return
    with open(path + '.tmp', 'w') as f:
        json.dump(state, f)
    os.rename(path + '.tmp', path)


def expand_macros(s):
    now = datetime.now()
    s = s.replace("${YEAR}", str(now.year))
    s = s.replace("${MONTH}", str(now.month))
    s = s.replace("${DAY}", str(now.day))
    return s


def scan_files(options):
    return glob.glob(expand_macros(options.fileglob))


def poll(options, state, syslog):
    for path in scan_files(options):
        old_size, old_offset = state.get(path, (0, 0))

        path_match = options.path_regex.match(path)
        if not path_match:
            if options.verbose:
                print "file excluded by regex:", path
            continue

        new_size = os.path.getsize(path)
        if new_size == old_size:
            if options.verbose:
                print "file size unchanged so skipping:", path
            continue
        elif new_size < old_size:
            old_offset = 0

        path_date = datetime.strptime(path_match.group("date"), options.date_format).date()

        with open(path) as f:
            if old_offset > 0:
                f.seek(old_offset)

            leftover = 0

            try:
                for line in f:
                    leftover = len(line)
                    if line[-1] == '\n':
                        match = options.line_regex.match(line)
                        if match:
                            line_time = datetime.strptime(match.group('time'), options.time_format).time()
                            timestamp = datetime.combine(path_date, line_time).replace(tzinfo=TZLOCAL)

                            syslog.send(match.group("msg"), timestamp, procid=match.group("procid"),
                                        app_name=path_match.group("app_name"))
                        else:
                            if options.verbose:
                                print "line excluded by regex:", line[:-1]
                        leftover = 0
            finally:
                position = f.tell()
                state[path] = (position, position - leftover)


def reset_state(options):
    state = {}
    for path in scan_files(options):
        size = os.path.getsize(path)
        state[path] = (size, size)
    return state


def main():
    options = parse_options()
    syslog = Syslog(options)

    if options.reset:
        state = reset_state(options)
    else:
        state = load_state(options.statefile)

    while True:
        try:
            poll(options, state, syslog)
        finally:
            save_state(state, options.statefile)
        if options.interval <= 0.0:
            break
        time.sleep(options.interval)

if __name__ == '__main__':
    main()