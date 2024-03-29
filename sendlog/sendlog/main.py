#!/usr/bin/env python
from __future__ import print_function # python 2 compat

import argparse, ssl, socket, sys, glob, re, os, json, time
from datetime import datetime
from dateutil import tz

TZLOCAL = tz.tzlocal()

class Syslog:
    def __init__(self, options):
        self.options = options
        self.sock = None
        self.connect()
        self.max_length = options.max_length
        self.header = "<%d>1" % (options.facility * 8 + options.severity)

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

    def send(self, msg, timestamp, host=socket.getfqdn().split('.')[0], app_name="-", procid="-", msgid="-", structured_data="-"):
        payload = " ".join([self.header, timestamp.isoformat(), host, app_name, procid, msgid, structured_data, msg])
        if self.max_length > 0:
            payload = payload[:self.max_length]
        if self.sock is not None:
            self.sock.send((str(len(payload)) + " " + payload).encode())
        else:
            print(payload)


SYSLOG_FACILITIES = {
    'kern': 0,
    'user': 1,
    'mail': 2,
    'daemon': 3,
    'auth': 4,
    'syslog': 5,
    'lpr': 6,
    'news': 7,
    'uucp': 8,
    'cron': 9,
    'authpriv': 10,
    'ftp': 11,
    'local0': 16,
    'local1': 17,
    'local2': 18,
    'local3': 19,
    'local4': 20,
    'local5': 21,
    'local6': 22,
    'local7': 23
}


def syslog_facility(s):
    return SYSLOG_FACILITIES.get(s) or int(s)


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
    parser.add_argument("--first-reset", action="store_true", help="reset if the state file does not exist")
    parser.add_argument("--max-length", default=8192, type=int, help='maximum message length to truncate to')
    parser.add_argument("--facility", default='user', type=syslog_facility, help='syslog facility name or number')
    parser.add_argument("--severity", default=7, type=int, help='syslog severity level')
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
    s = s.replace("${MONTH}", '%02d' % now.month)
    s = s.replace("${DAY}", '%02d' % now.day)
    return s


def scan_files(options):
    return glob.glob(expand_macros(options.fileglob))


def poll(options, state, syslog):
    for path in scan_files(options):
        old_size, old_offset = state.get(path, (0, 0))

        path_match = options.path_regex.match(path)
        if not path_match:
            if options.verbose:
                print("file excluded by regex:", path)
            continue

        new_size = os.path.getsize(path)
        if new_size == old_size:
            if options.verbose:
                print("file size unchanged so skipping:", path)
            continue
        elif new_size < old_size:
            old_offset = 0

        groups = path_match.groupdict()

        with open(path) as f:
            if old_offset > 0:
                f.seek(old_offset)

            leftover = 0

            try:
                while True:
                    line = f.readline()
                    if not line: break
                    leftover = len(line)
                    if line[-1] == '\n':
                        match = options.line_regex.match(line)
                        if match:
                            groups.update(match.groupdict())
                            line_date = datetime.strptime(groups["date"], options.date_format).date()
                            line_time = datetime.strptime(groups["time"], options.time_format).time()
                            timestamp = datetime.combine(line_date, line_time).replace(tzinfo=TZLOCAL)

                            syslog.send(match.group("msg"), timestamp, procid=groups["procid"],
                                        app_name=groups["app_name"])
                        else:
                            if options.verbose:
                                print("line excluded by regex:", line[:-1])
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

    if options.reset or (options.first_reset and not os.path.exists(options.statefile)):
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
