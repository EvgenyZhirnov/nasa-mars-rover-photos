#!/usr/bin/env python3
"""Root-owned SSH entrypoint. No shell, forwarding, or arbitrary commands."""
import os
import re
import sys

command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
match = re.fullmatch(r'deploy (preview|production) ([a-f0-9]{40})', command)
if not match:
    sys.exit('Only deploy <preview|production> <commit SHA> is permitted')
os.execv('/usr/bin/sudo', ['sudo', '-n', '/usr/local/lib/nasarover/deploy.py', *match.groups()])
