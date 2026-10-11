"""Serial local Docker task runtime. No Docker socket or verifier in agent."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT/'.eval'
DOCKER = ['docker', '--config', str(LOCAL/'docker-config'), '-H', 'unix:///Users/huntharo/.docker/run/docker.sock']


def command(args, *, timeout=900, log=None, check=True):
    if log:
        with Path(log).open('a') as f:
            result = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
    else:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f'command failed ({result.returncode}): {args[0:3]}; inspect sanitized local log')
    return result


def docker(*args, **kwargs):
    return command([*DOCKER, *map(str,args)], **kwargs)


def mount(source, target, readonly=False):
    return ['--mount', f'type=bind,src={Path(source).resolve()},dst={target}'+(',readonly' if readonly else '')]


class Runtime:
    def __init__(self, run_id, image, input_data, auth='/Users/huntharo/.codex/auth.json', portable=False):
        self.name = 'fh-'+run_id
        self.root = LOCAL/'runs'/run_id
        self.image = image
        self.input = input_data
        self.portable = portable
        if self.root.exists():
            raise ValueError('existing runtime evidence: reconcile, never overwrite')
        self.root.mkdir(parents=True)
        for d in ['profile','codex','output','verifier']:
            (self.root/d).mkdir(mode=0o700)
        (self.root/'input.json').write_text(json.dumps(input_data,indent=2)+'\n')
        self.auth = auth

    def start(self):
        mounts = []
        for src,dst,ro in [
            (self.root/'profile','/eval/profile',False),
            (self.root/'codex','/eval/codex',False),
            (self.root/'output','/eval/output',False),
            (self.auth,'/eval/codex/auth.json',True),
            (LOCAL/('cache/portable/managed' if self.portable else 'cache/managed'),'/opt/managed',True),
            (LOCAL/('runtime-portable.json' if self.portable else 'runtime.json'),'/eval/runtime.json',True),
            (self.root/'input.json','/eval/input.json',True),
            (LOCAL/'cache/current-driver/apps/desktop/eval','/opt/pwragent/apps/desktop/eval',True),
        ]:
            mounts.extend(mount(src,dst,ro))
        if self.portable:
            mounts.extend(mount(LOCAL/'cache/portable/glibc','/opt/pwragent-glibc',True))
        docker('run','-d','--name',self.name,'--platform','linux/arm64','--user','0:0','--cpus','2','--memory','6g','--shm-size','512m','--entrypoint','/usr/bin/tini',*mounts,self.image,'--','sleep','infinity')
        # Host uid retains auth.json's 0600 protection and read-only mount;
        # using uid1000 would require widening permissions or a credential copy.
        uid,gid = os.getuid(),os.getgid()
        setup = f'mkdir -p /app /logs/verifier && chown -R {uid}:{gid} /app'
        docker('exec',self.name,'sh','-c',setup)
        docker('exec','--user',f'{uid}:{gid}',self.name,'sh','-c','if ! git -C /app rev-parse HEAD >/dev/null 2>&1; then git -C /app init -q && git -C /app -c user.name=Eval -c user.email=eval@localhost add -A && git -C /app -c user.name=Eval -c user.email=eval@localhost commit --allow-empty -qm fixture; fi')

    def agent(self):
        uid,gid = os.getuid(),os.getgid()
        return docker('exec','--user',f'{uid}:{gid}','--workdir','/opt/pwragent',self.name,'xvfb-run','-a','node','apps/desktop/eval/run-headless.mjs','--input','/eval/input.json','--output','/eval/output',timeout=self.input['timeoutMs']/1000+120,log=self.root/'driver.log',check=False)

    def grade_terminal(self, tests):
        # Only after the PwrAgent/Electron process has exited.
        docker('cp',str(tests),f'{self.name}:/tests')
        result = docker('exec','--user','0:0','--workdir','/app',self.name,'bash','/tests/test.sh',timeout=900,log=self.root/'verifier.log',check=False)
        docker('cp',f'{self.name}:/logs/verifier/.',self.root/'verifier',check=False)
        reward = self.root/'verifier/reward.txt'
        if not reward.exists():
            return {'status':'infra_invalid','exit_code':result.returncode,'success':None}
        value=float(reward.read_text().strip())
        return {'status':'graded' if value in (0,1) else 'infra_invalid','exit_code':result.returncode,'reward':value,'success':value==1 if value in (0,1) else None}

    def close(self):
        docker('rm','-f',self.name,check=False)
