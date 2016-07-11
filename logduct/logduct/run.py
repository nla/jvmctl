#!/usr/bin/env python
from __future__ import print_function
import socket, os, sys, argparse, array
from sendmsg import sendmsg, SCM_RIGHTS, SO_PASSCRED
import json

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run a command with output piped to logductd.")
    parser.add_argument('-s', '--socket', default='/run/logduct.sock', help='logductd socket to connect to')
    parser.add_argument('--fd', action='append', metavar='FD:LOGNAME', help='redirect a file descriptor to a named secondary log')
    parser.add_argument('-u', '--unit', default=None, help='unit name to pass to logductd')
    parser.add_argument('--no-stdio', action='store_true', help='do not redirect stdout and stderr')
    parser.add_argument('command', help='command to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='arguments passed to command')
    return parser.parse_args()

def connect_to_logductd(socket_path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, SO_PASSCRED, 1)
    sock.connect(socket_path)
    return sock

def parse_fd_options(opts):
    fdlist = []
    if opts is not None:
        for opt in opts:
            fd, logname = opt.split(':')
            fdlist.append((int(fd), logname))
    return fdlist

def reserve_fds(fds):
    """Reserve the fds we're going to redirect so the logduct socket and pipes
    don't end up on the same number and get clobbered
    """
    for fd, logname in fds:
        if fd > 2:
            os.dup2(0, fd)

def redirect_fds(fds, sock, unit):
    """Redirect each fd to a pipe and pass the read end of the pipe to
    logductd.
    """
    pipes_to_send = []
    lognames = []
    for fd, logname in fds:
        read_end, write_end = os.pipe()
        os.dup2(write_end, fd)
        os.close(write_end)
        pipes_to_send.append(read_end)
        lognames.append(logname)

    header = {"unit": unit,
              "lognames": lognames}
    sendmsg(sock, json.dumps(header) + '\n',
            [(socket.SOL_SOCKET, SCM_RIGHTS, array.array("i", pipes_to_send))])

    for read_end in pipes_to_send:
        os.close(read_end)

def main():
    args = parse_arguments()
    fds = parse_fd_options(args.fd)

    reserve_fds(fds)
    sock = connect_to_logductd(args.socket)
    redirect_fds(fds, sock, args.unit)

    if not args.no_stdio:
        os.dup2(sock.fileno(), sys.stdout.fileno())
        os.dup2(sock.fileno(), sys.stderr.fileno())

    sock.close()
    os.execvp(args.command, [args.command] + args.args)

if __name__ == '__main__': main()
