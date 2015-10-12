#!/usr/bin/env python2
import os, re, tempfile, shutil, time, signal
from subprocess import Popen, check_call

def slurp(file):
    with open(file) as f:
        return f.read()

def wait_until_exists(file, timeout=1, delay=0.02):
    start = time.time()
    while time.time() < start + timeout:
        if os.path.exists(file):
            return
        time.sleep(delay)
    raise Exception("timeout waiting for " + file)

def run_tests(tmpdir):
    socket_file = os.path.join(tmpdir, "logductd.sock")
    logs_dir = os.path.join(tmpdir, "logs")
    daemon = Popen(["python2", "./logductd", "-s", socket_file, "-d", logs_dir, "--trust-blindly"])

    unit = "dummyunit"
    stdio_log = os.path.join(logs_dir, unit, "stdio.log")
    third_log = os.path.join(logs_dir, unit, "third.log")
    try:
        wait_until_exists(socket_file)

        # stdio
        check_call(["python2", "./logduct-run", "-s", socket_file, "-u", unit, "echo", "hello"])
        wait_until_exists(stdio_log)

        data = slurp(stdio_log)
        match = re.match(r"\d\d:\d\d:\d\d.\d\d\d (unknown|echo)\[\d+\]: hello\n", data)
        assert match

        # pipe fd
        check_call(["python2", "./logduct-run", "-s", socket_file, "-u", unit, "--fd", "3:third",
                    "--no-stdio", "bash", "-c", "echo there >&3"])
        wait_until_exists(third_log)

        data = slurp(third_log)
        match = re.match(r"\d\d:\d\d:\d\d.\d\d\d: there\n", data)
        assert match
    finally:
        daemon.send_signal(signal.SIGINT)
        time.sleep(0.2)
        daemon.kill()

def main():
    try:
        tmpdir = tempfile.mkdtemp("logduct-test")
        run_tests(tmpdir)
    finally:
        shutil.rmtree(tmpdir)

if __name__ == '__main__': main()