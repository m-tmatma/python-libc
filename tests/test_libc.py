import sys
import time

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
    assert 2 - 1e3 < t < 2 + 1e3


def test_eventfd():
    efd = eventfd(0, 0)

    a = 10

    t = time.perf_counter()
    _ = os.write(efd, a.to_bytes(8, byteorder=sys.byteorder))
    b = os.read(efd, 8)
    t = time.perf_counter() - t
    assert 0 < t < 1e-3

    os.close(efd)

    c = int.from_bytes(b, byteorder=sys.byteorder)
    assert a == c
