import errno
import os
import sys
import select
import time
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


def test_timerfd_nonblocking():
    tfd = timerfd_create(CLOCK.REALTIME, TFD.NONBLOCK)

    ev = select.epoll()
    ev.register(tfd, select.EPOLLIN)

    timerfd_settime(tfd, 0, (0.5, 1))

    t = time.perf_counter()
    for i in range(3):
        events = ev.poll(-1)
        for fd, event in events:
            if event & select.EPOLLIN:
                if fd == tfd:
                    print("signaled")
                    _ = os.read(tfd, 8)
    t = time.perf_counter() - t
    assert 2 - 1e-3 < t < 2 + 1e-3

    ev.unregister(tfd)

    # close timerfd
    os.close(tfd)

    # try to close the timerfd which was already closed.
    with pytest.raises(OSError) as exc_info:
        os.close(tfd)

    # check detail of OSError
    assert exc_info.value.args[0] == errno.EBADF
    assert exc_info.value.args[1] == os.strerror(errno.EBADF)

    del ev


def test_eventfd():
    efd = eventfd(0, 0)

    a = 10

    _ = os.write(efd, a.to_bytes(8, byteorder=sys.byteorder))
    b = os.read(efd, 8)
    os.close(efd)

    c = int.from_bytes(b, byteorder=sys.byteorder)
    assert a == c

    # try to close the fd which was already closed.
    with pytest.raises(OSError) as exc_info:
        os.close(efd)

    # check detail of OSError
    assert exc_info.value.args[0] == errno.EBADF
    assert exc_info.value.args[1] == os.strerror(errno.EBADF)

def test_eventfd_nonblocking():
    efd = eventfd(0, EFD.NONBLOCK)

    ev = select.epoll()
    ev.register(efd, select.EPOLLIN)

    a = 10
    _ = os.write(efd, a.to_bytes(8, byteorder=sys.byteorder))

    events = ev.poll(-1)
    for fd, event in events:
        if event & select.EPOLLIN:
            if fd == efd:
                print("signaled")
                b = os.read(efd, 8)
                ev.unregister(efd)

                c = int.from_bytes(b, byteorder=sys.byteorder)
                assert a == c

    os.close(efd)

    # try to close the fd which was already closed.
    with pytest.raises(OSError) as exc_info:
        os.close(efd)

    # check detail of OSError
    assert exc_info.value.args[0] == errno.EBADF
    assert exc_info.value.args[1] == os.strerror(errno.EBADF)

    del ev

