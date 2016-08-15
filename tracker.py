import threading
import time

import rtplot
import openocd
import logging

import cProfile, pstats, io


class VarTracker:
    def __init__(self, tracking_delay = 0.01):
        self.vars = []
        self.oocd = openocd.launch("stm32f4")
        self._stop = 0
        self.thread = threading.Thread(target = self.run)
        self.track_delay = tracking_delay

    def start(self):
        self.thread.start()
        openocd.run_mcu(self.oocd)

    def add_track_var(self, var):
        assert isinstance(var, rtplot.WatchVariable)
        self.vars.append(var)

    def remove_track_var(self, var):
        assert isinstance(var, rtplot.WatchVariable)
        if var in self.vars:
            self.vars.remove(var)

    def run(self):
        while True:
            while not self.oocd:
                self.oocd = openocd.launch("stm32f4")
                time.sleep(3)

            for var in self.vars:

                value = openocd.read_value(self.oocd, var.address, 32)

                if value == None:
                    logging.error("Failed to read variable {}".format(var.name))
                else:
                    var.append_value(value)

            time.sleep(self.track_delay)

            if self._stop:
                break

    def stop(self):
        self._stop = 1
