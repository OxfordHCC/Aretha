# TODO make requirement of threading lib explicit in documentation,
# since threading lib is optional in python < 3.7
from threading import Event
import signal

# We use the Event class to wait instead of time.sleep() because
# time.sleep does not get interrupted by any signal. I think this
# is true as of python 3.6 or .7

# Inspiration for this taken from a SO answer here:
# https://stackoverflow.com/questions/5114292/break-interrupt-a-time-sleep-in-python
class EvalLoop:
    def __init__(self, interval, on_close, log):
        self.exit = Event()
        self.ring = []
        self.interval = interval
        self.log = log
        self.called_shutdown = False

        def shutdown(sig, _frame):
            if self.called_shutdown is True:
                return
            self.called_shutdown = True
            self.log.debug("Called loop shutdown")
            self.exit.set()
            on_close()
            
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

    def register(self, cb, name=None):
        if not name is None:
            cb.__name__ = name
        self.ring.append(cb)

    def _run_loop(self):
        self.log.debug("Awake!")
        for fn in self.ring:
            if not self.exit.is_set():
                self.log.debug(f"Running {fn.__name__}")
                fn()
        self.log.debug("Sleeping...")

    def start(self):
        self.log.debug(f"Starting eval loop with {self.interval} seconds interval.")
        self.log.debug(f"Registered functions: {len(self.ring)}")
        while not self.exit.is_set():
            self._run_loop()
            self.exit.wait(self.interval)
            
        self.log.debug("Loop stopped")
