"""
sendmsg and recvmsg are only available in Python 3 which is not available on
EL7.  This is a mostly API compatible implementation of them for Python 2.
"""

from ctypes import (Structure, c_size_t, c_int, c_char_p, c_uint, POINTER,
                    sizeof, c_void_p, CDLL, create_string_buffer, cast,
                    get_errno)
import os, socket

try:
    SO_PASSCRED = socket.SO_PASSCRED
except AttributeError:
    SO_PASSCRED = 16

try:
    SO_PEERCRED = socket.SO_PEERCRED
except AttributeError:
    SO_PEERCRED = 17

SCM_RIGHTS = 1
SCM_CREDENTIALS = 2

class Cmsghdr(Structure):
    _fields_ = [
        ('len', c_size_t),
        ('level', c_int),
        ('type', c_int)]

class Iovec(Structure):
    _fields_ = [
        ('base', c_char_p),
        ('len', c_size_t)]

class Msghdr(Structure):
    _fields_ = [
        ('name', c_char_p),
        ('namelen', c_uint),
        ('iov', POINTER(Iovec)),
        ('iovlen', c_size_t),
        ('control', c_void_p),
        ('controllen', c_size_t),
        ('flags', c_int)]

def cmsg_align(length):
    return (length + sizeof(c_size_t) - 1) & ~(sizeof(c_size_t) - 1)

def cmsg_space(length):
    return cmsg_align(length) + cmsg_align(sizeof(Cmsghdr))

def cmsg_len(length):
    return cmsg_align(sizeof(Cmsghdr)) + length

libc = CDLL("libc.so.6", use_errno=True)
libc.sendmsg.argtypes = (c_int, POINTER(Msghdr), c_int)
libc.recvmsg.argtypes = (c_int, POINTER(Msghdr), c_int)

def sendmsg(sock, buffers, ancdata=None, flags=0):
    if ancdata is None:
        ancdata = []
    iov = (Iovec * len(buffers))()

    for i, buf in enumerate(buffers):
        iov[i].base = buf
        iov[i].len = len(buf)

    clen = sum(cmsg_space(len(buffer(data))) for _, _, data in ancdata)
    cbuf = create_string_buffer(clen)
    pos = 0

    for level, type_, data in ancdata:
        data = buffer(data)
        hdr = Cmsghdr.from_buffer(cbuf, pos)
        hdr.len = cmsg_len(len(data))
        hdr.level = level
        hdr.type = type_
        pos += cmsg_len(0)
        cbuf[pos:pos + len(data)] = data
        pos += cmsg_align(len(data))

    msg = Msghdr(
        control=cast(cbuf, c_void_p),
        controllen=clen,
        iov=iov,
        iovlen=len(iov))

    result = libc.sendmsg(sock.fileno(), msg, flags)

    if result == -1:
        errno = get_errno()
        raise OSError(errno, os.strerror(errno))
    else:
        return result

def recvmsg(sock, bufsize, ancbufsize=0, flags=0):
    buf = create_string_buffer(bufsize)
    cbuf = create_string_buffer(ancbufsize)
    
    iov = (Iovec * 1)()
    iov[0].base = cast(buf, c_char_p)
    iov[0].len = bufsize

    msg = Msghdr(
        iov=iov,
        iovlen=len(iov),
        control=cast(cbuf, c_void_p),
        controllen=ancbufsize)

    result = libc.recvmsg(sock.fileno(), msg, flags)
    if result == -1:
        errno = get_errno()
        raise OSError(errno, os.strerror(errno))

    ancdata = []
    pos = 0
    while pos < ancbufsize:
        cmsg = Cmsghdr.from_buffer(cbuf, pos)
        if cmsg.len < sizeof(Cmsghdr):
            break
        data_start = pos + cmsg_len(0)
        data_end = pos + cmsg.len
        
        data = bytes(cbuf[data_start : data_end])
        ancdata.append((cmsg.level, cmsg.type, data))
        pos += cmsg_align(cmsg.len)

    return (bytes(buf[:result]), ancdata, msg.flags, None)
