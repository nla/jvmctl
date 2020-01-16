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
    _gc_spaces = None
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
        data.buflen = len(mm)
        if data.magic not in (0xcafec0c0, 0xc0c0feca):
            raise ValueError("%s: bad magic (0x%x) not a hsperfdata file" % (path, data.magic))
        if data.major_version != 2:
            raise ValueError("%s: unsupported hsperfdata version: %d.%d" % (path, 
                data.major_version, data.minor_version))
        return data

    @classmethod
    def from_pid(cls, pid):
        uid = os.stat("/proc/%d" % pid).st_uid
        user = pwd.getpwuid(uid).pw_name
        return cls.from_file("/tmp/hsperfdata_%s/%d" % (user, pid))

    def __iter__(self):
        sane_min = sizeof(self)
        sane_max = self.buflen - sizeof(PerfEntry)
        offset = self.entry_offset
        for i in xrange(self.num_entries):
            if not sane_min <= offset <= sane_max - sizeof(PerfEntry):
                raise IndexError("start of entry out of bounds: %d" % offset)
            entry = PerfEntry.from_address(addressof(self) + offset)
            entry.entry_length = entry_length = entry.raw_entry_length
            if not sizeof(PerfEntry) <= entry_length <= self.buflen - offset:
                raise IndexError("entry_length out of bounds: %d" % entry_length)
            yield entry
            offset += entry_length

    def __getitem__(self, key):
        for entry in self:
            if entry.name == key:
                return entry

    @property
    def gc_spaces(self):
        if self._gc_spaces is None:
            spaces = {}
            for entry in data:
                m = re.match(r"^sun\.gc\.generation\.(\d+)\.space\.(\d+)\.(name|used|capacity|initCapacity|maxCapacity)$", entry.name)
                if m:
                    field = m.group(3)
                    key = (m.group(1), m.group(2))
                    if key not in spaces:
                        spaces[key] = GCSpace(*key)
                    if field == 'name':
                        spaces[key]._name = entry
                    elif field == 'used':
                        spaces[key]._used = entry
                    elif field == 'initCapacity':
                        spaces[key]._init = entry
                    elif field == 'capacity':
                        spaces[key]._capacity = entry
                    elif field == 'maxCapacity':
                        spaces[key]._max = entry
            self._gc_spaces = list(sorted(spaces.values(), key=lambda s: (s.generation_id, s.space_id)))
        return self._gc_spaces

def bounded_string_at(ptr, maxlen):
    s = string_at(ptr, maxlen)
    return s[:s.index('\0')]

class PerfEntry(Structure):
    _name = None
    _cvalue = None
    _fields_ = [
            ('raw_entry_length', c_int),
            ('raw_name_offset', c_int),
            ('vector_length', c_int),
            ('data_type', c_char),
            ('flags', c_byte),
            ('data_unit', c_byte),
            ('data_variability', c_byte),
            ('raw_data_offset', c_int)]

    @property
    def name_offset(self):
        name_offset = self.raw_name_offset
        if not sizeof(self) <= name_offset <= self.entry_length:
            raise IndexError("name_offset out of bounds: %d" % name_offset)
        return name_offset

    @property
    def data_offset(self):
        data_offset = self.raw_data_offset
        if not sizeof(self) <= data_offset <= self.entry_length:
            raise IndexError("data_offset out of bounds: %d" % data_offset)
        return data_offset

    @property
    def name(self):
        if self._name is None:
           offset = self.name_offset
           self._name = bounded_string_at(addressof(self) + offset, self.entry_length - offset)
        return self._name

    @property
    def value(self):
        if self._cvalue is not None:
            return self._cvalue.value
        offset = self.data_offset
        maxlen = self.entry_length - offset
        vlen = self.vector_length
        if vlen > 0:
            if self.data_type == 'B':
                if vlen > maxlen:
                    raise IndexError("string longer than entry")
                return bounded_string_at(addressof(self) + offset, vlen)
        else:
            ctype = DATA_TYPES[self.data_type]
            if sizeof(ctype) > maxlen:
                raise IndexError("data extends past end of entry")
            self._cvalue = ctype.from_address(addressof(self) + offset)
            return self._cvalue.value

class GCSpace:
    def __init__(self, generation_id, space_id):
        self.generation_id = generation_id
        self.space_id = space_id

    @property
    def name(self): return self._name.value
    @property 
    def used(self): return self._used.value
    @property
    def max(self): return self._max.value
    @property
    def init(self): return self._init.value
    @property
    def capacity(self): return self._capacity.value
    @property
    def free(self): return self.capacity - self.used

import argparse, time, sys, itertools, re

def binfmt(n, unit='iB', sep=' '):
    if n == 0:
        return 0
    for prefix in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if n < 1024.0:
            return '%3.3g%s%s%s' % (n, sep, prefix, unit)
        n /= 1024.0
    return '%3.3g%s%s%s' % (n, sep, 'Y', unit)

def sifmt(n, unit='', sep=' '):
    if 0.0 < abs(n) < 1.0:
        for prefix in ['m', 'μ', 'n', 'p']:
            if abs(n) >= 1.0:
                return '%3.3g%s%s%s' % (n, sep, prefix, unit)
            n *= 1000.0
        return '%3.3g%s%s%s' % (n, sep, 'f', unit)
    else:
        for prefix in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(n) < 1000.0:
                return '%3.3g%s%s%s' % (n, sep, prefix, unit)
            n /= 1000.0
        return '%3.3g%s%s%s' % (n, sep, 'Y', unit)

def timefmt(n, sep=' '):
    if abs(n) < 1.0:
        return sifmt(n, 's')
    for unit, divisor in [('s', 60), ('min', 60), ('hr', 24)]:
        if abs(n) < divisor:
            return '%3.3g%s%s' % (n, sep, unit)
        n /= divisor
    return '%3.3g%s%s' % (n, sep, 'days')

def fmtb(n, short=False):
    if args.human_readable:
        return binfmt(n, '' if short else 'iB', '' if short else ' ')
    elif args.si:
        return sifmt(n, '' if short else 'B', '' if short else ' ')
    return str(n)

def fmt(entry):
    if entry.vector_length == 0:
        if entry.data_unit == UNIT_BYTES:
            return fmtb(entry.value)
        elif entry.data_unit == UNIT_TICKS:
            if args.human_readable:
                return timefmt(entry.value / hrtfreq)
            elif args.si:
                return sifmt(entry.value / hrtfreq, 's')
        elif entry.data_unit == UNIT_HERTZ:
            if args.human_readable or args.si:
                return sifmt(entry.value, 'Hz')
    return str(entry.value)

def main():
    parser = argparse.ArgumentParser(description="Read JVM hsperfdata performance counters.")
    parser.add_argument('key', nargs='*')
    parser.add_argument('-p', '--pid', type=int)
    parser.add_argument('-f', '--file', type=str)
    parser.add_argument('-i', '--interval', type=float, default=0.0)
    parser.add_argument('-c', '--count', type=int)
    parser.add_argument('-H', '--human-readable', action='store_true', help="format bytes with IEC binary units")
    parser.add_argument('--si', action='store_true', help="format bytes using SI units")
    parser.add_argument('--free', action='store_true', help="show memory usage")
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


    i = 1
    while True:
        if args.free:
            if i > 1:
                print()
            if args.human_readable or args.si:
                spec = '%-6s %8s %8s %8s %6s %8s %8s'
            else:
                spec = '%-6s %12s %12s %12s %6s %12s %12s'
            print(spec % ('', 'Size', 'Used', 'Free', 'Use%', 'Max', 'Init'))
            for space in data.gc_spaces:
                print(spec % (space.name.title() + ':',
                        fmtb(space.capacity, short=True),
                        fmtb(space.used, short=True),
                        fmtb(space.free, short=True),
                        '%d%%' % long(space.used * 100 / space.capacity),
                        fmtb(space.max, short=True),
                        fmtb(space.init, short=True)))
        elif args.key:
            print(' '.join(fmt(data[key]) for key in args.key))
        else:
            for entry in data:
                print(entry.name, '=', fmt(entry))
        if args.interval > 0 and (args.count is None or i < args.count):
            sys.stdout.flush()
            time.sleep(args.interval)
            i += 1
        else:
            break

if __name__ == '__main__': main()
