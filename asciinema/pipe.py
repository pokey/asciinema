import time
import codecs
import ujson

from asciinema.compress import CompressThread

STDIN = 0
STDOUT = 1
MAX_LINES_IN_FILE = 30000


class Pipe:

    def __init__(self, dir):
        dir.mkdir(parents=True, exist_ok=True)
        self.dir = dir

        self.decoder = codecs.getincrementaldecoder('UTF-8')('replace')

        self.out_file_idx = 0
        self._set_out_file_path()
        while (self.out_file_path.exists() or
               self.out_file_path.with_suffix('.json.gz').exists()):
            self.out_file_idx += 1
            self._set_out_file_path()

        self._init_file()

    def _set_out_file_path(self):
        self.out_file_path = (
            self.dir / 'log_{}.json'.format(self.out_file_idx)
        )

    def _init_file(self):
        self.lines_since_rotate = 0
        self.out_file = self.out_file_path.open('w')
        self.out_file.write('[\n')
        self.delim = ''

    def _finish_file(self):
        self.out_file.write('\n]\n')
        self.out_file.close()
        thread = CompressThread(self.out_file_path)
        thread.start()
        return thread

    def _write(self, data, fdno):
        text = self.decoder.decode(data)
        if text:
            frame = [time.time(), text, fdno]

            if self.lines_since_rotate > MAX_LINES_IN_FILE:
                self._finish_file()
                self.out_file_idx += 1
                self._set_out_file_path()
                self._init_file()

            self.out_file.write(self.delim)
            self.delim = ',\n'
            self.out_file.write(ujson.dumps(frame, ensure_ascii=False))
            self.out_file.flush()
            self.lines_since_rotate += 1

        return len(data)

    def write_stdin(self, data):
        return self._write(data, STDIN)

    def write_stdout(self, data):
        return self._write(data, STDOUT)

    def close(self):
        self._finish_file().join()
