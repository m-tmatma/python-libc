import errno
import os
import sys
import time
import select

import pytest

from libc import *


def test_getpid():
    pid = getpid()
    assert pid == os.getpid()


def test_timerfd():
    tfd = timerfd_create(CLOCK.REALTIME, 0)
    timerfd_settime(tfd, 0, (0.5, 1))
    t = time.perf_counter()
    _ = os.read(tfd, 8)
    _ = os.read(tfd, 8)
    _ = os.read(tfd, 8)
    t = time.perf_counter() - t
    assert 2 - 1e-3 < t < 2 + 1e-3

    # close timerfd
    os.close(tfd)

    # try to close the timerfd which was already closed.
    with pytest.raises(OSError) as exc_info:
        os.close(tfd)

    # check detail of OSError
    assert exc_info.value.args[0] == errno.EBADF
    assert exc_info.value.args[1] == os.strerror(errno.EBADF)


def test_eventfd():
    efd = eventfd(0, 0)

    a = 10

    _ = os.write(efd, a.to_bytes(8, byteorder=sys.byteorder))
    b = os.read(efd, 8)
    c = int.from_bytes(b, byteorder=sys.byteorder)
    assert a == c

    os.close(efd)

    # try to close the eventfd which was already closed.
    with pytest.raises(OSError) as exc_info:
        os.close(efd)

    # check detail of OSError
    assert exc_info.value.args[0] == errno.EBADF
    assert exc_info.value.args[1] == os.strerror(errno.EBADF)

def test_eventfd_EFD_SEMAPHORE():
    efd = eventfd(0, EFD.NONBLOCK | EFD.SEMAPHORE)

    a = 10

    _ = os.write(efd, a.to_bytes(8, byteorder=sys.byteorder))

    rlist=[efd]
    wlist = []
    xlist = []
    for i in range(a):
        select.select(rlist, wlist, xlist)
        print(i)
        b = os.read(efd, 8)
        c = int.from_bytes(b, byteorder=sys.byteorder)
        assert c == 1

    select.select(rlist, wlist, xlist)
    b = os.read(efd, 8)
    c = int.from_bytes(b, byteorder=sys.byteorder)
    assert c == 1


    os.close(efd)

    # try to close the eventfd which was already closed.
    with pytest.raises(OSError) as exc_info:
        os.close(efd)

    # check detail of OSError
    assert exc_info.value.args[0] == errno.EBADF
    assert exc_info.value.args[1] == os.strerror(errno.EBADF)


def test_memfd():
    mfd = memfd_create("test", 0)
    pid = getpid()
    name = os.readlink(f"/proc/{pid}/fd/{mfd}")
    assert name.startswith(f"/memfd:test ")

    # close memfd
    os.close(mfd)
    assert not os.path.exists(f"/proc/{pid}/fd/{mfd}")

    # try to close the memfd which was already closed.
    with pytest.raises(OSError) as exc_info:
        os.close(mfd)

    # check detail of OSError
    assert exc_info.value.args[0] == errno.EBADF
    assert exc_info.value.args[1] == os.strerror(errno.EBADF)
