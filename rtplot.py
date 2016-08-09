import PySide as ps
import pyqtgraph as pg

import collections
import time, datetime
import numpy as np
import logging as log
import threading


class WatchVariable:
    def __init__(self, value_buffer_size=100, name='To Be Filled by O. E. M.', address=None):
        self.buf_size = value_buffer_size
        self.name = name

        self.times = collections.deque([0.0] * self.buf_size, self.buf_size)
        self.values = collections.deque([0.0] * self.buf_size, self.buf_size)
        self.address = address

        self.track_start = (datetime.datetime.now(), time.clock())

        self._locked = 0

    def append_value(self, new_data):
        self._locked = 1
        self.times.append(time.clock())
        self.values.append(new_data)
        self._locked = 0

    def is_locked(self):
        return bool(self._locked)


class VariablePlot:

    FROM_NOW = 1
    FROM_START = 2

    def __init__(self, variable, start_time = 0):
        assert isinstance(variable, WatchVariable)

        self.p_widget = pg.PlotWidget(name=variable.name, clickable=False)

        self.p_widget.setLabel('bottom', 'Time', units='s')
        self.p_widget.setLabel('left', variable.name, units='V')
        self._curve = self.p_widget.plot()
        self._var = variable
        self._start_time = start_time
        self._xvals = None
        self._yvals = None

        self.time_mode = VariablePlot.FROM_START

    def calc_display_times(self, time_window=5):
        while self._var.is_locked():
            pass

        sample_times = np.array(self._var.times)
        samples = np.array(self._var.values)

        # check sample times are indeed growing
        samples_ordered = all(sample_times[i] <= sample_times[i + 1] for i in range(len(sample_times) - 1))

        if not samples_ordered:
            log.error("While plotting for variable {}, sample times do not appear to be in correct order. Plotting \
                      aborted.".format(self._var.name))
            return False

        # calculate current time - sample time
        current_time = time.clock()
        deltas = current_time - sample_times

        if (deltas >= 0.0).all():
            pass  # ok
        else:
            comps = list(deltas >= 0.0)

            i = 0
            [i for i, x in enumerate(comps) if x > 0]

            log.error("While plotting for variable {}, sample time {} was encountered which is from the future \
                      (current time is {}). Plotting aborted.".format(self._var.name, sample_times[i], current_time))

            self._yvals = None
            self._xvals = None

            return False

        # cull everything that's older than time_window
        deltas = deltas[deltas < time_window]

        # this is safe to do as culled times are always at the left
        samples = samples[len(samples) - len(deltas):]

        if self.time_mode == VariablePlot.FROM_NOW:
            self._xvals = deltas
            self.p_widget.setRange(xRange=(-time_window, 0))
        elif self.time_mode == VariablePlot.FROM_START:
            self._xvals = (current_time - self._start_time) - deltas
        self._yvals = samples

        return True

    def update_plot(self):
        if (self._xvals is not None) and (self._yvals is not None):
            self._curve.setData(x=self._xvals, y=self._yvals)


class PlotDispatch():
    def __init__(self, base_layout, graph_update_rate=0.1, time_window=5):
        assert isinstance(base_layout, ps.QtGui.QLayout)

        self.plots = {}
        start_time = time.clock()
        self._stop = 0
        self._rate = graph_update_rate
        self._calc_thread = threading.Thread(target=self._calc_display_data)
        self.time_window = time_window
        self._layout = base_layout
        self._working = 0

    def plot_var(self, var):
        while self._working:
            pass

        assert isinstance(var, WatchVariable)

        new_plot = VariablePlot(var, time.clock())
        self.plots[var] = new_plot
        log.info("Started tracking {} at {}".format(var.name, str(var.track_start[0])))
        self._layout.addWidget(new_plot.p_widget)

    def remove_var(self, var):
        while self._working:
            pass

        assert var in self.plots.keys()

        self.plots[var].p_widget.deleteLater()

        log.info("Stopped tracking {} at {}".format(var.name, str(datetime.datetime.now())))
        del self.plots[var]

    def start(self):
        self._calc_thread.start()

    def stop(self):
        self._stop = 1

    def _calc_display_data(self):
        while True:
            if self._stop:
                break
            self._working = 1
            for var in self.plots.keys():
                self.plots[var].calc_display_times(time_window=self.time_window)
                self.plots[var].update_plot()
            self._working = 0

            time.sleep(self._rate)


if __name__ == "__main__":
    import random
    print('rtplot.py testing')
    app = ps.QtGui.QApplication([])
    mw = ps.QtGui.QMainWindow()
    mw.setWindowTitle('pyqtgraph example: PlotWidget')
    mw.resize(800,800)
    cw = ps.QtGui.QWidget()
    mw.setCentralWidget(cw)
    l = ps.QtGui.QVBoxLayout()
    cw.setLayout(l)
    mw.show()

    pd = PlotDispatch(l)
    pd.start()

    var1 = WatchVariable()
    pd.plot_var(var1)
    var2 = WatchVariable()
    pd.plot_var(var2)
    var3 = WatchVariable()
    pd.plot_var(var3)

    def variable_remover():
        global var1
        time.sleep(4)
        pd.remove_var(var1)


    def variable_spammer():
        while True:
            var1.append_value(random.randrange(1, 100))
            var3.append_value(random.randrange(1, 100))
            var2.append_value(random.randrange(1, 100))
            time.sleep(0.1)

    thread = threading.Thread(target = variable_spammer)
    thread.start()

    thread = threading.Thread(target = variable_remover)
    thread.start()

    ps.QtGui.QApplication.instance().exec_()
