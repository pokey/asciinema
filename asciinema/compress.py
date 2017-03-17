import gzip
import shutil
import threading


class CompressThread(threading.Thread):
    def __init__(self, path):
        threading.Thread.__init__(self)
        self.path = path

    def run(self):
        gz_path = self.path.with_suffix('.json.gz')
        with self.path.open('rb') as f_in:
            with gzip.open(str(gz_path), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        self.path.unlink()
