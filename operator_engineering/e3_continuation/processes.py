"""Actual CPU/native child receipts with bounded cleanup of owned children only."""
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from .contract import SGT, require


def stamp():
    return dt.datetime.now(SGT).isoformat()


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def controller_lock(path):
    """Keep the marker; a kernel lease, not deleting a path, provides exclusion."""
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        os.write(fd, b'{"schema":"E3_EXTERNAL_CONTROLLER_FLOCK_V1"}\n')
    except FileExistsError:
        fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    handle = os.fdopen(fd, 'r+')
    try:
        handle.seek(0)
        require(json.loads(handle.read()) == {'schema':'E3_EXTERNAL_CONTROLLER_FLOCK_V1'},
                'unknown controller lock; preserve without deletion')
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return handle
    except BaseException:
        handle.close()
        raise


def identity(pid):
    folder = Path('/proc')/str(pid)
    fields = (folder/'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=folder.stat().st_uid, state=fields[0],
                start_ticks=int(fields[19]),
                command=[s.decode(errors='replace') for s in
                         (folder/'cmdline').read_bytes().split(b'\0') if s])


def signal_owned(process, expected, signum, group=False):
    if process.poll() is not None:
        return False
    observed = identity(process.pid)
    require(observed['uid'] == os.getuid() and
            observed['start_ticks'] == expected['start_ticks'] and
            observed['command'] == expected['command'], 'refuse signaling replaced/foreign PID')
    if group:
        require(os.getpgid(process.pid) == process.pid, 'owned process group identity differs')
        os.killpg(process.pid, signum)
    else:
        process.send_signal(signum)
    return True


def descendants(pid):
    observed = {}
    for folder in Path('/proc').iterdir():
        if not folder.name.isdigit():
            continue
        try:
            if folder.stat().st_uid != os.getuid():
                continue
            fields = (folder/'stat').read_text().rsplit(')', 1)[1].split()
            observed[int(folder.name)] = int(fields[1])
        except (OSError, ValueError):
            continue
    owned = {pid}
    while True:
        enlarged = owned | {child for child, parent in observed.items() if parent in owned}
        if enlarged == owned:
            break
        owned = enlarged
    result = {}
    for child in owned - {pid}:
        try:
            result[child] = identity(child)
        except OSError:
            pass
    return result


def live_same(expected):
    try:
        observed = identity(expected['pid'])
    except (OSError, ValueError):
        return False
    return (observed['uid'] == os.getuid() and
            observed['start_ticks'] == expected['start_ticks'] and
            observed['command'] == expected['command'] and observed['state'] not in ['Z', 'X'])


class Recorded:
    def __init__(self, folder, env, cwd):
        self.folder, self.env, self.cwd = Path(folder), env, cwd

    def start(self, label, command):
        require(label and all(c.isalnum() or c in '-_' for c in label), 'unsafe receipt label')
        path = self.folder/label
        # Open exclusively BEFORE spawn. No unrecorded child on name collision.
        reservation = path.with_suffix('.reserved.json')
        write(reservation, dict(at=stamp(), command=command, spawn_attempted=False))
        out = path.with_suffix('.stdout.private.txt').open('x')
        try:
            err = path.with_suffix('.stderr.private.txt').open('x')
            try:
                child = subprocess.Popen(command, cwd=self.cwd, env=self.env,
                                         stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                         start_new_session=True)
            except BaseException as exc:
                write(path.with_suffix('.spawn_error.json'),
                      dict(at=stamp(), actual_child_created=False,
                           child_returncode=None, exit_code=None,
                           error=type(exc).__name__, message=str(exc)))
                raise
            finally:
                err.close()
        finally:
            out.close()
        expected = identity(child.pid)
        write(path.with_suffix('.started.json'),
              dict(at=stamp(), command=command, process=expected))
        return child, expected

    def finish(self, label, child, expected, timeout, term_timeout=30, kill_timeout=10):
        signals = []
        timed_out = False
        tracked = {}
        deadline = time.monotonic() + timeout
        while child.poll() is None:
            tracked.update(descendants(child.pid))
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            try:
                child.wait(timeout=min(.1, remaining))
            except subprocess.TimeoutExpired:
                pass
        # Forked children may own separate process groups (native supervisor does).
        # Capture while the parent chain is observable; never signal a reused PID.
        leaked = [v for v in tracked.values() if live_same(v)]
        if not timed_out and leaked:
            grace = time.monotonic() + min(2., term_timeout)
            while leaked and time.monotonic() < grace:
                time.sleep(.02)
                leaked = [v for v in tracked.values() if live_same(v)]
        leak_error = bool(leaked) and not timed_out
        if timed_out or leaked:
            for sig, budget in [(signal.SIGTERM, term_timeout), (signal.SIGKILL, kill_timeout)]:
                if signal_owned(child, expected, sig, group=True):
                    signals.append(dict(pid=child.pid, signal=int(sig), target='OWNED_GROUP'))
                for descendant in tracked.values():
                    if live_same(descendant):
                        try:
                            os.kill(descendant['pid'], sig)
                            signals.append(dict(pid=descendant['pid'], signal=int(sig),
                                                target='OBSERVED_OWNED_DESCENDANT'))
                        except ProcessLookupError:
                            pass  # Exit raced the verified signal; never reinterpret as failure0.
                try:
                    child.wait(timeout=budget)
                except subprocess.TimeoutExpired:
                    pass
                until = time.monotonic() + budget
                while any(live_same(v) for v in tracked.values()) and time.monotonic() < until:
                    time.sleep(.02)
                if child.poll() is not None and not any(live_same(v) for v in tracked.values()):
                    break
            require(child.poll() is not None, 'owned child still alive after bounded cleanup')
        code = child.returncode
        value = dict(at=stamp(), process=expected, child_returncode=code,
                     exit_code=code if code >= 0 else 128-code,
                     signal=-code if code < 0 else None,
                     deadline_exceeded=timed_out, cleanup_signals=signals,
                     observed_descendants=list(tracked.values()),
                     live_descendants_after_cleanup=[v for v in tracked.values() if live_same(v)],
                     unexpected_descendant_after_parent_exit=leak_error)
        write(self.folder/(label+'.exit.json'), value)
        if timed_out:
            raise TimeoutError('actual child deadline; preserve ID and exit receipt: '+label)
        require(not leak_error and not value['live_descendants_after_cleanup'],
                'owned descendant leak; preserve real parent exit and stop new TEST')
        return value

    def run(self, label, command, timeout, **cleanup):
        child, expected = self.start(label, command)
        return self.finish(label, child, expected, timeout, **cleanup)
