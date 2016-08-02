# Based on https://github.com/ap--/python-live-plotting,
# thanks Andreas! Getting MPL to work rendered me powerless to code that myself

from gi.repository import Gtk, GLib

import collections
import random
import time
import math

class mpl:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

class DynamicPlotter(Gtk.Window):

    def __init__(self, sampleinterval=0.01, timewindow=5., size=(600,350)):
        # Gtk stuff
        Gtk.Window.__init__(self, title='Dynamic Plotting with Matplotlib + Gtk3')
        self.connect("destroy", lambda x : Gtk.main_quit())
        self.set_default_size(*size)
        # Data stuff
        self._interval = int(sampleinterval*1000)
        self._bufsize = int(timewindow/sampleinterval)
        self.databuffer = collections.deque([0.0]*self._bufsize, self._bufsize)
        self.new_data_value = 0
        self.x = [sampleinterval*i for i in range(-self._bufsize+1,1)]
        # MPL stuff
        self.figure = mpl.Figure()
        self.ax = self.figure.add_subplot(1, 1, 1)
        self.ax.grid(True)
        self.canvas = mpl.FigureCanvas(self.figure)
        self.line, = self.ax.plot(self.x, self.databuffer)
        # Gtk stuff
        self.add(self.canvas)
        self.canvas.show()
        self.show_all()

    def append(self, new_data):
        self.new_data_value = new_data

    def getdata(self):
        return self.new_data_value

    def reset(self):
        self.databuffer.clear()

    def updateplot(self):
        self.databuffer.append( self.getdata() )
        self.line.set_ydata(self.databuffer)
        self.ax.relim()
        self.ax.autoscale_view(False, False, True)
        self.canvas.draw()
        return True

    def run(self):
        GLib.timeout_add(self._interval, self.updateplot )
        Gtk.main()
