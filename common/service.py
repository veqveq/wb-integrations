from asyncio import Event
from signal import signal, SIGTERM


class DebianService:
    close_signal = None
    stop_event = None

    def __init__(self):
        if DebianService.close_signal is None:
            DebianService.close_signal = signal(SIGTERM, self._shutdown)
            DebianService.stop_event = Event()

    def _shutdown(self, signum, frame):
        if self.is_running():
            DebianService.stop_event.set()

    @staticmethod
    def is_running():
        return not DebianService.stop_event.is_set()
