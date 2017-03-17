import os
import subprocess
from pathlib import Path

from .asciicast import Asciicast
from .pty_recorder import PtyRecorder
from .pipe import Pipe


class Recorder:

    def __init__(self, pty_recorder=None, env=None):
        self.pty_recorder = (
            pty_recorder if pty_recorder is not None else PtyRecorder()
        )
        self.env = env if env is not None else os.environ

    def record(self, dir, user_command, title, max_wait):
        command = user_command or self.env.get('SHELL') or 'sh'
        dir = Path(dir)
        pipe = Pipe(dir)
        env = os.environ.copy()
        env['ASCIINEMA_REC'] = '1'

        width = int(subprocess.check_output(['tput', 'cols']))
        height = int(subprocess.check_output(['tput', 'lines']))

        asciicast = Asciicast(
            pipe,
            width,
            height,
            command=user_command,
            title=title,
            term=self.env.get('TERM'),
            shell=self.env.get('SHELL')
        )

        asciicast.save(str(dir / 'info.json'))

        self.pty_recorder.record_command(['sh', '-c', command], pipe, env)
