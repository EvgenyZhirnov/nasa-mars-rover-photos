#!/usr/bin/env python3
"""Install one verified Docker-save image; restore the previous image on failure.

Installed root-owned outside the checkout. CI cannot replace this file or Compose.
Image rollback preserves data; migrations must remain backward-compatible.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

from smoke import check

ROOT = Path('/opt/server/apps/nasarover-delivery')
PORTS = {'production': 5082, 'preview': 5083}


def validate_manifest(archive, image):
    with tarfile.open(archive, 'r:gz') as tar:
        info = tar.getmember('manifest.json')
        if info.size > 65536 or not info.isfile():
            raise ValueError('Invalid image manifest')
        manifest = json.load(tar.extractfile(info))
    if len(manifest) != 1 or manifest[0].get('RepoTags') != [image]:
        raise ValueError('Archive must contain only the requested release tag')


def deploy(target, revision, stream):
    if target not in PORTS or not re.fullmatch('[a-f0-9]{40}', revision):
        raise ValueError('Invalid deployment target or revision')
    location = ROOT / target
    image = 'nasarover-release:' + revision
    with (ROOT / 'deploy.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with tempfile.NamedTemporaryFile(dir=ROOT, suffix='.tar.gz') as archive:
            count = 0
            while chunk := stream.read(1024 * 1024):
                count += len(chunk)
                if count > 2 * 1024**3:
                    raise ValueError('Image archive exceeds 2 GiB')
                archive.write(chunk)
            archive.flush()
            validate_manifest(archive.name, image)
            subprocess.run(['docker', 'load', '-i', archive.name], check=True)
        metadata = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image]))[0]
        if metadata['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != revision:
            raise ValueError('Image revision label mismatch')
        state_file = location / 'state.json'
        previous = json.loads(state_file.read_text()) if state_file.exists() else None
        base_env = {**os.environ, 'APP_PORT': str(PORTS[target])}
        command = ['docker', 'compose', '-p', 'nasarover-' + target + '-cd',
                   '-f', str(location / 'compose.yml'), 'up', '-d', '--pull', 'never']
        try:
            subprocess.run(command, env={**base_env, 'APP_IMAGE': image}, check=True)
            check('http://127.0.0.1:' + str(PORTS[target]), revision)
        except Exception:
            if previous:
                subprocess.run(command, env={**base_env, 'APP_IMAGE': previous['image']}, check=True)
                check('http://127.0.0.1:' + str(PORTS[target]), previous['revision'])
                print('Rolled back to', previous['revision'], flush=True)
            else:
                subprocess.run(command[:-4] + ['down'], env={**base_env, 'APP_IMAGE': image}, check=True)
            raise
        if previous:
            (location / 'previous.json').write_text(json.dumps(previous))
        temporary = location / 'state.next'
        temporary.write_text(json.dumps({'image': image, 'revision': revision}))
        temporary.replace(state_file)
        # Persist the selected image for manual compose operations and reboot recovery.
        (location / '.env').write_text('APP_IMAGE=' + image + '\nAPP_PORT=' + str(PORTS[target]) + '\n')
        print('Deployed', target, revision, flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('Expected target and commit SHA')
    deploy(sys.argv[1], sys.argv[2], sys.stdin.buffer)
