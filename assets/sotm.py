import sys

import itertools
import subprocess

for iteration in itertools.count():
    args = [sys.executable, 'test-rs.py', '--release', '--no-emu', '--no-plando', '--cosmetics', '--preset=fenhl_tootr']
    if iteration > 0:
        args.append('--no-rebuild')
    if subprocess.run(args).returncode == 0:
        break
