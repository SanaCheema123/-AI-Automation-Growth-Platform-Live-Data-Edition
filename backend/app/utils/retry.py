import time

def retry(fn, attempts=3, delay=1.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last = exc
            if i < attempts - 1:
                time.sleep(delay * (2 ** i))
    raise last
