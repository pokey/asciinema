import time
import codecs
import ujson

from asciinema.compress import CompressThread

STDIN = 0
STDOUT = 1
MAX_LINES_IN_FILE = 30000


def get_file_path(dir, idx):
    return dir / 'log_{}.json'.format(idx)


class Pipe:

    def __init__(self, dir, max_wait=None):
        dir.mkdir(parents=True, exist_ok=True)
        self.dir = dir
        self.out_file_idx = 0
        self.out_file_path = get_file_path(self.dir, self.out_file_idx)
        while (self.out_file_path.exists() or
               self.out_file_path.with_suffix('.json.gz').exists()):
            self.out_file_idx += 1
            self.out_file_path = get_file_path(self.dir, self.out_file_idx)
        self.out_file = self.out_file_path.open('w')
        self.out_file.write('[\n')
        self.delim = ''
        self.frames = []
        self.max_wait = max_wait
        self.last_write_time = time.time()
        self.lines_since_rotate = 0
        self.duration = 0
        self.decoder = codecs.getincrementaldecoder('UTF-8')('replace')

    def write_stdin(self, data):
        return self.write(data, STDIN)

    def write_stdout(self, data):
        return self.write(data, STDOUT)

    def write(self, data, fdno):
        text = self.decoder.decode(data)
        if text:
            delay = self._increment_elapsed_time()
            frame = [delay, text, fdno]
            if self.lines_since_rotate > MAX_LINES_IN_FILE:
                self.out_file.write('\n]\n')
                self.out_file.close()
                CompressThread(self.out_file_path).start()
                self.out_file_idx += 1
                self.out_file_path = get_file_path(self.dir, self.out_file_idx)
                self.out_file = self.out_file_path.open('w')
                self.lines_since_rotate = 0
                self.out_file.write('[\n')
                self.delim = ''
            self.out_file.write(self.delim)
            self.delim = ',\n'
            self.out_file.write(ujson.dumps(frame, ensure_ascii=False))
            self.out_file.flush()
            self.lines_since_rotate += 1

        return len(data)

    def close(self):
        self._increment_elapsed_time()

        if len(self.frames) > 0:
            last_frame = self.frames[-1]
            if last_frame[1] == "exit\r\n" or last_frame[1] == "logout\r\n":
                self.frames = self.frames[0:-1]
                self.duration -= last_frame[0]

    def _increment_elapsed_time(self):
        # delay = int(delay * 1000000) / 1000000.0 # millisecond precission
        now = time.time()
        delay = now - self.last_write_time

        if self.max_wait and delay > self.max_wait:
            delay = self.max_wait

        self.duration += delay
        self.last_write_time = now

        return now
