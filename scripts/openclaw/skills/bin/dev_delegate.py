#!/usr/bin/env python3
"""Local CLI delegation using argv arrays, workspace locks and persistent state."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time


def save(path: Path, value: dict) -> None:
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace').strip())
    return result.stdout.decode(errors='replace')


def snapshot(cwd: Path) -> dict:
    return {'status': git(cwd, 'status', '--porcelain=v1', '--untracked-files=all'),
            'diff': git(cwd, 'diff', 'HEAD', '--binary')}


def identity(pid: int) -> str | None:
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return None if fields[0] == 'Z' else fields[19]
    except (OSError, IndexError):
        return None


def acquire_lock(state_root: Path, root: Path) -> int:
    path = state_root / (hashlib.sha256(os.fsencode(root)).hexdigest() + '.lock')
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise ValueError('another delegation holds the workspace lock')
    return fd


def events(task: Path, agent: str) -> dict:
    found = {}
    with (task / 'events.jsonl').open(errors='replace') as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            if agent == 'codex' and event.get('type') == 'thread.started':
                found['session_id'] = event.get('thread_id')
            elif agent == 'kimi':
                for obj in (event, event.get('data'), event.get('session')):
                    if isinstance(obj, dict):
                        sid = obj.get('session_id') or obj.get('sessionId')
                        if isinstance(sid, str):
                            found['session_id'] = sid
            if event.get('type') == 'turn.failed':
                found['agent_error'] = event.get('error', 'turn.failed')
    return found


def terminate_group(process: subprocess.Popen, grace: float) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def worker(task: Path, lock_fd: int) -> None:
    state_path = task / 'status.json'
    state = json.loads(state_path.read_text())
    process = None
    worktree_lock = None
    cancelled = False

    def cancel(_signum, _frame):
        nonlocal cancelled
        cancelled = True

    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    state.update(pid=os.getpid(), process_identity=identity(os.getpid()), state='STARTING')
    save(state_path, state)
    try:
        cwd = Path(state['source_cwd'])
        if state['worktree']:
            destination = task / 'worktree'
            git(cwd, 'worktree', 'add', '--detach', str(destination), 'HEAD')
            worktree_lock = acquire_lock(task.parent, destination.resolve())
            cwd = destination / state['relative_cwd']
        state['cwd'] = str(cwd)
        if state['is_git']:
            save(task / 'before.json', snapshot(cwd))
        executable, session = state['executable'], state['resume']
        if state['agent'] == 'codex':
            command = [executable, 'exec', '--sandbox', 'workspace-write']
            if session:
                command += ['resume']
            command += ['--json']
            if not state['is_git']:
                command += ['--skip-git-repo-check']
            command += ['--'] + ([session] if session else []) + ['-']
        else:
            command = [executable, '--output-format', 'stream-json']
            if session:
                command += ['--session', session]
            command += ['--prompt', (task / 'prompt.txt').read_text()]
        with (task / 'prompt.txt').open('rb') as prompt, \
                (task / 'events.jsonl').open('wb') as stdout, \
                (task / 'stderr.log').open('wb') as stderr:
            process = subprocess.Popen(command, cwd=cwd,
                stdin=prompt if state['agent'] == 'codex' else subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, start_new_session=True,
                pass_fds=(lock_fd,) + ((worktree_lock,) if worktree_lock is not None else ()))
            state.update(state='RUNNING', child_pid=process.pid, started_at=time.time())
            save(state_path, state)
            deadline = time.monotonic() + state['timeout']
            reason = None
            while process.poll() is None:
                if cancelled or (task / 'cancel.request').exists():
                    reason = 'CANCELLED'
                elif time.monotonic() >= deadline:
                    reason = 'TIMEOUT'
                if reason:
                    terminate_group(process, state['grace'])
                    break
                time.sleep(0.1)
            # Also reap descendants left behind by a normally exited CLI.
            if reason is None:
                terminate_group(process, state['grace'])
            result = process.wait()
            state.update(state=reason or ('SUCCEEDED' if result == 0 else 'FAILED'),
                exit_code=124 if reason == 'TIMEOUT' else 130 if reason == 'CANCELLED'
                else (128 - result if result < 0 else result), child_returncode=result)
        state.update(events(task, state['agent']))
        if state.get('agent_error') and state['state'] == 'SUCCEEDED':
            state.update(state='FAILED', exit_code=1)
        if state['is_git']:
            save(task / 'after.json', snapshot(cwd))
    except Exception as exc:
        if process is not None:
            terminate_group(process, state['grace'])
        state.update(state='FAILED', exit_code=1, error=str(exc))
    finally:
        state['finished_at'] = time.time()
        save(state_path, state)
        if worktree_lock is not None:
            os.close(worktree_lock)
        os.close(lock_fd)


def start(args: argparse.Namespace) -> dict:
    cwd = Path(args.workdir).expanduser().resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError('workdir must be a directory')
    prompt = Path(args.prompt_file).read_text()
    if not prompt.strip():
        raise ValueError('prompt file is empty')
    if args.resume and args.resume.startswith('-'):
        raise ValueError('session ID must not start with a dash')
    if args.resume and args.worktree:
        raise ValueError('resume in the existing worktree; do not create another worktree')
    if any(not math.isfinite(v) or v <= 0 for v in (args.timeout, args.grace)):
        raise ValueError('timeout and grace must be finite and positive')
    executable = shutil.which(args.agent)
    if not executable:
        raise ValueError(f'{args.agent} is not available on PATH')
    try:
        root = Path(git(cwd, 'rev-parse', '--show-toplevel').strip()).resolve()
        is_git = True
    except RuntimeError:
        if not args.allow_non_git or args.worktree:
            raise ValueError('not a Git worktree; use --allow-non-git only intentionally')
        root, is_git = cwd, False
    state_root = Path(os.environ.get('DEV_DELEGATE_STATE_DIR',
        str(Path.home() / '.local/state/dev-delegate'))).resolve()
    state_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if state_root.stat().st_uid != os.getuid():
        raise ValueError('state directory must belong to the current user')
    state_root.chmod(0o700)
    lock_fd = acquire_lock(state_root, root)
    try:
        if is_git:
            dirty = git(root, 'status', '--porcelain=v1', '--untracked-files=all')
            if dirty and (not args.allow_dirty or args.worktree):
                raise ValueError('workspace has uncommitted changes; inspect before using '
                    '--allow-dirty. A new worktree requires a clean source.')
        task = Path(tempfile.mkdtemp(prefix=args.agent + '-', dir=state_root))
        (task / 'prompt.txt').write_text(prompt)
        (task / 'events.jsonl').touch()
        (task / 'stderr.log').touch()
        state = dict(state='QUEUED', agent=args.agent, executable=executable,
            source_cwd=str(cwd), cwd=str(cwd), is_git=is_git,
            relative_cwd=str(cwd.relative_to(root)), worktree=args.worktree,
            resume=args.resume, session_id=args.resume, timeout=args.timeout,
            grace=args.grace, created_at=time.time(), task_dir=str(task))
        save(task / 'status.json', state)
        with (task / 'worker.log').open('wb') as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                '_worker', str(task), str(lock_fd)], stdin=subprocess.DEVNULL,
                stdout=log, stderr=log, start_new_session=True, pass_fds=(lock_fd,))
        save(task / 'launch.json', {'pid': process.pid,
                                   'process_identity': identity(process.pid)})
        return {'task_dir': str(task), 'pid': process.pid,
            'status_file': str(task / 'status.json'), 'events': str(task / 'events.jsonl'),
            'stderr': str(task / 'stderr.log')}
    finally:
        # No LOCK_UN: the child owns the same open file description.
        os.close(lock_fd)


def poll(task: Path, cancel: bool = False) -> dict:
    task = task.expanduser().resolve(strict=True)
    state = json.loads((task / 'status.json').read_text())
    active = state['state'] in {'QUEUED', 'STARTING', 'RUNNING'}
    if active and not state.get('pid') and (task / 'launch.json').exists():
        state.update(json.loads((task / 'launch.json').read_text()))
    if active and state.get('pid') and identity(state['pid']) != state.get('process_identity'):
        state['state'] = 'EXITED_UNKNOWN'
        state['error'] = 'worker disappeared; inspect logs and child processes before retrying'
    elif active and cancel:
        (task / 'cancel.request').touch(mode=0o600)
        state['cancel_requested'] = True
    state.update(events(task, state['agent']))
    return state


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    launch = commands.add_parser('start')
    launch.add_argument('agent', choices=['codex', 'kimi'])
    launch.add_argument('workdir')
    launch.add_argument('prompt_file')
    launch.add_argument('resume', nargs='?')
    launch.add_argument('--allow-dirty', action='store_true')
    launch.add_argument('--allow-non-git', action='store_true')
    launch.add_argument('--worktree', action='store_true')
    launch.add_argument('--timeout', type=float, default=600)
    launch.add_argument('--grace', type=float, default=15)
    for name in ('poll', 'cancel'):
        commands.add_parser(name).add_argument('task_dir')
    internal = commands.add_parser('_worker')
    internal.add_argument('task_dir')
    internal.add_argument('lock_fd', type=int)
    args = parser.parse_args()
    try:
        if args.command == '_worker':
            worker(Path(args.task_dir), args.lock_fd)
            return 0
        result = start(args) if args.command == 'start' else poll(
            Path(args.task_dir), args.command == 'cancel')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
