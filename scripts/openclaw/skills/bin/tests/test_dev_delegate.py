"""Behavior tests with isolated repositories and fake CLIs; no API calls."""
from __future__ import annotations
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

WRAPPER = Path(__file__).resolve().parents[1] / 'dev-delegate.sh'
FAKE = r'''#!/usr/bin/env python3
import json, os, pathlib, signal, subprocess, sys, time
agent = pathlib.Path(sys.argv[0]).name
prompt = sys.stdin.read() if agent == 'codex' else sys.argv[sys.argv.index('--prompt') + 1]
pathlib.Path(os.environ['CAPTURE']).write_text(json.dumps({'args': sys.argv[1:], 'prompt': prompt, 'cwd': os.getcwd()}))
print(json.dumps({'type':'thread.started', 'thread_id':'thread-123'} if agent == 'codex' else {'type':'system', 'session_id':'kimi-456'}), flush=True)
print('diagnostic, not JSON', file=sys.stderr, flush=True)
if os.environ.get('MUTATE'):
    pathlib.Path('result.txt').write_text('completed')
if os.environ.get('HANG'):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    child = subprocess.Popen([sys.executable, '-c', 'import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)'])
    pathlib.Path(os.environ['CHILD']).write_text(str(child.pid))
    time.sleep(60)
if os.environ.get('EVENT_FAIL'):
    print(json.dumps({'type':'turn.failed','error':{'message':'test failure'}}), flush=True)
sys.exit(int(os.environ.get('CLI_EXIT','0')))
'''


class DelegateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-test-')
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo space'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        (self.repo / 'initial.txt').write_text('initial')
        self.git('add', '.')
        self.git('commit', '-qm', 'initial')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for agent in ('codex','kimi'):
            p = self.bin / agent
            p.write_text(FAKE)
            p.chmod(0o755)
        self.prompt = self.root / 'prompt.txt'
        self.prompt.write_text('Implement task')
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                        DEV_DELEGATE_STATE_DIR=str(self.root / 'state'),
                        CAPTURE=str(self.root / 'capture.json'), CHILD=str(self.root / 'child.pid'))
        self.tasks = []

    def git(self, *args):
        return subprocess.run(['git','-C',str(self.repo),*args], check=True, capture_output=True)

    def call(self, *args):
        return subprocess.run([str(WRAPPER), *map(str,args)], env=self.env, capture_output=True, text=True)

    def start(self, agent='codex', *options, cwd=None):
        p = self.call('start', agent, cwd or self.repo, self.prompt, *options)
        self.assertEqual(p.returncode, 0, p.stderr)
        task = Path(json.loads(p.stdout)['task_dir'])
        self.tasks.append(task)
        return task

    def wait(self, task, terminal=True):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            state = json.loads(self.call('poll', task).stdout)
            if terminal and state['state'] not in ('QUEUED','STARTING','RUNNING'):
                return state
            if not terminal and state['state'] == 'RUNNING' and (self.root / 'child.pid').exists():
                return state
            time.sleep(.04)
        self.fail(f'task did not reach expected state: {state}')

    def tearDown(self):
        for task in self.tasks:
            if task.exists():
                self.call('cancel', task)
                self.wait(task)
        self.temp.cleanup()

    def test_literal_prompt_and_split_logs_for_both_agents(self):
        marker = self.root / 'INJECTED'
        text = f'quote " newline\n$(touch {marker}) `touch {marker}` \\ $HOME 中文'
        self.prompt.write_text(text)
        for agent, sid in [('codex','thread-123'),('kimi','kimi-456')]:
            task = self.start(agent)
            state = self.wait(task)
            self.assertEqual(state['state'],'SUCCEEDED')
            self.assertEqual(state['session_id'], sid)
            self.assertEqual(json.loads((self.root/'capture.json').read_text())['prompt'],text)
            self.assertFalse(marker.exists())
            self.assertIn('diagnostic', (task/'stderr.log').read_text())
            for line in (task/'events.jsonl').read_text().splitlines():
                json.loads(line)
            self.assertEqual(task.stat().st_mode & 0o777, 0o700)
            self.assertEqual((task/'prompt.txt').stat().st_mode & 0o777, 0o600)

    def test_resume_uses_explicit_session_and_sandbox(self):
        for agent in ('codex','kimi'):
            self.wait(self.start(agent, 'actual-id'))
            args = json.loads((self.root/'capture.json').read_text())['args']
            self.assertIn('actual-id', args)
            if agent == 'kimi':
                self.assertIn('--session', args)
                self.assertNotIn('-r', args)
            else:
                self.assertIn('resume', args)
                self.assertIn('workspace-write', args)

    def test_dirty_rejected_and_explicit_override_preserves_changes(self):
        (self.repo/'initial.txt').write_text('user edit')
        (self.repo/'untracked.txt').write_text('user content')
        result = self.call('start','codex',self.repo,self.prompt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('uncommitted', result.stderr)
        task = self.start('codex','--allow-dirty')
        self.assertEqual(self.wait(task)['state'],'SUCCEEDED')
        self.assertEqual((self.repo/'initial.txt').read_text(),'user edit')
        self.assertIn('untracked.txt', json.loads((task/'before.json').read_text())['status'])

    def test_shared_lock_including_subdirectory(self):
        self.env['HANG']='1'
        task = self.start('codex','--grace','0.15')
        self.wait(task, terminal=False)
        childdir = self.repo/'subdir'
        childdir.mkdir()
        blocked = self.call('start','kimi',childdir,self.prompt)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn('lock', blocked.stderr)
        self.call('cancel',task)
        self.assertEqual(self.wait(task)['state'],'CANCELLED')
        del self.env['HANG']
        self.assertEqual(self.wait(self.start('kimi'))['state'],'SUCCEEDED')

    def test_timeout_kills_process_group_and_records_reason(self):
        self.env['HANG']='1'
        task = self.start('codex','--timeout','0.4','--grace','0.15')
        result = self.wait(task)
        self.assertEqual(result['state'],'TIMEOUT')
        self.assertEqual(result['exit_code'],124)
        self.assertEqual(result['child_returncode'],-signal.SIGKILL)
        pid = (self.root/'child.pid').read_text()
        stat = Path('/proc')/pid/'stat'
        self.assertTrue(not stat.exists() or stat.read_text().rsplit(')',1)[1].split()[0]=='Z')

    def test_cli_failure_124_is_not_timeout(self):
        self.env['CLI_EXIT']='124'
        result = self.wait(self.start())
        self.assertEqual(result['state'],'FAILED')
        self.assertEqual(result['exit_code'],124)

    def test_failure_event_overrides_zero_exit(self):
        self.env['EVENT_FAIL']='1'
        self.assertEqual(self.wait(self.start())['state'],'FAILED')

    def test_worktree_isolation_and_snapshots(self):
        self.env['MUTATE']='1'
        task = self.start('codex','--worktree')
        result = self.wait(task)
        self.assertEqual(result['state'],'SUCCEEDED')
        self.assertEqual(Path(result['cwd']),task/'worktree')
        self.assertTrue((task/'worktree/result.txt').exists())
        self.assertFalse((self.repo/'result.txt').exists())
        self.assertIn('result.txt',json.loads((task/'after.json').read_text())['status'])

    def test_dirty_worktree_source_is_not_silently_ignored(self):
        (self.repo/'initial.txt').write_text('user change')
        p = self.call('start','codex',self.repo,self.prompt,'--worktree','--allow-dirty')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('clean source',p.stderr)

    def test_active_worktree_has_its_own_lock(self):
        self.env['HANG']='1'
        task = self.start('codex','--worktree','--grace','0.15')
        state = self.wait(task, terminal=False)
        blocked = self.call('start','kimi',state['cwd'],self.prompt)
        self.assertNotEqual(blocked.returncode,0)
        self.assertIn('lock',blocked.stderr)

    def test_symlink_alias_cannot_bypass_lock(self):
        self.env['HANG']='1'
        task = self.start('codex','--grace','0.15')
        self.wait(task,terminal=False)
        alias = self.root/'alias'
        alias.symlink_to(self.repo,target_is_directory=True)
        blocked = self.call('start','kimi',alias,self.prompt)
        self.assertNotEqual(blocked.returncode,0)
        self.assertIn('lock',blocked.stderr)

    def test_non_finite_timeout_is_rejected(self):
        for value in ('nan','inf','0','-1'):
            p=self.call('start','codex',self.repo,self.prompt,'--timeout',value)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('finite and positive',p.stderr)

    def test_missing_worker_is_not_reported_as_success(self):
        self.env['HANG']='1'
        task = self.start('codex','--grace','0.15')
        state = self.wait(task,terminal=False)
        try:
            os.kill(state['pid'],signal.SIGKILL)
            result = self.wait(task)
            self.assertEqual(result['state'],'EXITED_UNKNOWN')
            blocked = self.call('start','kimi',self.repo,self.prompt)
            self.assertNotEqual(blocked.returncode,0)
            self.assertIn('lock',blocked.stderr)
        finally:
            os.killpg(state['child_pid'],signal.SIGKILL)

    def test_non_git_requires_explicit_option(self):
        cwd = self.root/'nongit'
        cwd.mkdir()
        self.assertNotEqual(self.call('start','codex',cwd,self.prompt).returncode,0)
        self.assertEqual(self.wait(self.start('codex','--allow-non-git',cwd=cwd))['state'],'SUCCEEDED')
        self.assertIn('--skip-git-repo-check',json.loads((self.root/'capture.json').read_text())['args'])

    def test_missing_cli_fails_before_launch(self):
        (self.bin/'codex').unlink()
        # A PATH containing only dependencies prevents finding the real Codex.
        for executable in ('bash','python3','dirname','git'):
            import shutil
            (self.bin/executable).symlink_to(shutil.which(executable))
        self.env['PATH']=str(self.bin)
        p=self.call('start','codex',self.repo,self.prompt)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('not available',p.stderr)


if __name__ == '__main__':
    unittest.main()
