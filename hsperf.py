#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function
import os, mmap, pwd
from ctypes import *

DATA_TYPES = {'I': c_int, 'J': c_long}

UNIT_NONE = 1
UNIT_BYTES = 2
UNIT_TICKS = 3
UNIT_EVENTS = 4
UNIT_STRING = 5
UNIT_HERTZ = 6


class PerfData(Structure):
    _fields_ = [
            ('magic', c_uint),
            ('byte_order', c_byte),
            ('major_version', c_byte),
            ('minor_version', c_byte),
            ('accessible', c_byte),
            ('used', c_int),
            ('overflow', c_int),
            ('mtime', c_long),
            ('entry_offset', c_int),
            ('num_entries', c_int)]

    @classmethod
    def from_file(cls, path):
        with open(path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_COPY)
        data = cls.from_buffer(mm)
        if not data.is_valid():
            raise ValueError("%s: unsupported hsperfdata version (magic=0x%x, ver=%d.%d)" % 
                    (path, data.magic, data.major_version, data.minor_version))
        return data

    @classmethod
    def from_pid(cls, pid):
        uid = os.stat("/proc/%d" % pid).st_uid
        user = pwd.getpwuid(uid).pw_name
        return cls.from_file("/tmp/hsperfdata_%s/%d" % (user, pid))

    def is_valid(self):
        return ((self.magic == 0xcafec0c0L or self.magic == 0xc0c0fecaL) and
                self.major_version == 2 and
                self.entry_offset == sizeof(self))

    def __iter__(self):
        addr = addressof(self) + self.entry_offset
        for i in xrange(self.num_entries):
            entry = PerfEntry.from_address(addr)
            yield entry
            addr += entry.entry_length

    def __getitem__(self, key):
        for entry in self:
            if entry.name == key:
                return entry

class PerfEntry(Structure):
    _name = None
    _cvalue = None
    _fields_ = [
            ('entry_length', c_int),
            ('name_offset', c_int),
            ('vector_length', c_int),
            ('data_type', c_char),
            ('flags', c_byte),
            ('data_unit', c_byte),
            ('data_variability', c_byte),
            ('data_offset', c_int)]

    @property
    def name(self):
        if self._name is None:
            self._name = string_at(addressof(self) + self.name_offset)
        return self._name

    @property
    def value(self):
        if self._cvalue is not None:
            return self._cvalue.value
        elif self.vector_length > 0:
            if self.data_type == 'B':
                return string_at(addressof(self) + self.data_offset)
        else:
            ctype = DATA_TYPES[self.data_type]
            self._cvalue = ctype.from_address(addressof(self) + self.data_offset)
            return self._cvalue.value

if __name__ == '__main__':
    import argparse, time, sys, itertools

    def binfmt(n, unit='B'):
        for prefix in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if n < 1024.0:
                return '%3.1f %s%s' % (n, prefix, unit)
            n /= 1024.0
        return '%3.1f %s%s' % (n, 'Yi', unit)

    def sifmt(n, unit=''):
        if abs(n) < 1.0:
            for prefix in ['m', 'μ', 'n', 'p']:
                if abs(n) >= 1.0:
                    return '%4.1f %s%s' % (n, prefix, unit)
                n *= 1000.0
            return '%3.1f %s%s' % (n, 'f', unit)
        else:
            for prefix in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
                if abs(n) < 1000.0:
                    return '%3.1f %s%s' % (n, prefix, unit)
                n /= 1000.0
            return '%3.1f %s%s' % (n, 'Y', unit)

    def timefmt(n):
        if abs(n) < 1.0:
            return sifmt(n, 's')
        for unit, divisor in [('s', 60), ('min', 60), ('hr', 24)]:
            if abs(n) < divisor:
                return '%3.1f %s' % (n, unit)
            n /= divisor
        return '%3.1f %s' % (n, 'days')

    parser = argparse.ArgumentParser(description="Read JVM hsperfdata performance counters.")
    parser.add_argument('key', nargs='*')
    parser.add_argument('-p', '--pid', type=int)
    parser.add_argument('-f', '--file', type=str)
    parser.add_argument('-i', '--interval', type=float, default=0.0)
    parser.add_argument('-c', '--count', type=int)
    parser.add_argument('-H', '--human-readable', action='store_true', help="format bytes with IEC binary units")
    parser.add_argument('--si', action='store_true', help="format bytes using SI units")
    args = parser.parse_args()

    if args.pid:
        data = PerfData.from_pid(args.pid)
    elif args.file:
        data = PerfData.from_file(args.file)
    else:
        print("%s: --pid or --file must be given" % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    if args.count is not None and args.interval <= 0:
        args.interval = 0.05

    hrtfreq = float(data['sun.os.hrt.frequency'].value)

    def fmt(entry):
        if entry.vector_length == 0:
            if entry.data_unit == UNIT_BYTES:
                if args.human_readable:
                    return binfmt(entry.value, 'B')
                elif args.si:
                    return sifmt(entry.value, 'B')
            elif entry.data_unit == UNIT_TICKS:
                if args.human_readable:
                    return timefmt(entry.value / hrtfreq)
                elif args.si:
                    return sismft(entry.value / hrtfreq, 's')
            elif entry.data_unit == UNIT_HERTZ:
                if args.human_readable or args.si:
                    return sifmt(entry.value, 'Hz')
        return str(entry.value)

    i = 1
    while True:
        if args.key:
            print(' '.join(fmt(data[key]) for key in args.key))
        else:
            for entry in data:
                print(entry.name, '=', fmt(entry))
        if args.interval > 0 and (args.count is None or i < args.count):
            time.sleep(args.interval)
            i += 1
        else:
            break

