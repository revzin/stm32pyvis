import threading
import time

import rtplot
import openocd
import logging


class VarTracker:
    def __init__(self, oocd_conn, tracking_delay = 0.1):
        assert isinstance(oocd_conn, openocd.tl.Telnet)
        assert oocd_conn

        self.vars = []
        self.oocd = oocd_conn
        self._stop = 0
        self.thread = threading.Thread(target = self.run)
        self.track_delay = tracking_delay

    def start(self):
        self.thread.start()

    def add_track_var(self, var):
        assert isinstance(var, rtplot.WatchVariable)
        self.vars.append(var)

    def remove_track_var(self, var):
        assert isinstance(var, rtplot.WatchVariable)
        if var in self.vars:
            self.vars.remove(var)

    def run(self):
        while True:
            for var in self.vars:
                value = openocd.read_value(self.oocd_conn, var.address)
                if not value:
                    logging.error("Failed to read variable {}".format(var.name))
                else:
                    var.append(value)

            time.sleep(self.tracking_delay)

            if self._stop:
                break

    def stop(self):
        self._stop = 1
