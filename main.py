import PySide as ps
import threading

import elftools
import rtplot
import tracker
import openocd

# ------------------------------------------------------------------------ #
# Global stuff

# a list of rtplot.PlotVariables
all_vars = []

# rtplot.PlotDispatch thread
plotter = None

# tracker.VarTracker thread
tracker = None

# OpenOCD telnet connection
oocd_conn = None

def elf_path_dialog():
    import os
    path, _ = ps.QtGui.QFileDialog.getOpenFileName()


def on_shutdown():
    global plotter, tracker
    plotter.stop()
    tracker.stop()


def elf_to_vars(elf_path):
    global all_vars
    var_symbols = elftools.get_vars_name_address(elf_path)

    for var_name in var_symbols:
        all_vars.append(rtplot.WatchVariable(name=var_name, address=var_symbols[var_name]))

# layout stuff
app = ps.QtGui.QApplication([])
app.aboutToQuit.connect(on_shutdown)

mw = ps.QtGui.QMainWindow()
mw.setWindowTitle('STM32PyVis')
mw.resize(800, 800)

center_widget = ps.QtGui.QWidget()
center_layout = ps.QtGui.QHBoxLayout()
mw.setCentralWidget(center_widget)
left_widget = ps.QtGui.QWidget()
right_widget = ps.QtGui.QWidget()
center_layout.addWidget(left_widget)
center_layout.addWidget(right_widget)
center_widget.setLayout(center_layout)

left_layout = ps.QtGui.QVBoxLayout()
right_layout = ps.QtGui.QVBoxLayout()

left_widget.setLayout(left_layout)
right_widget.setLayout(right_layout)

elf_loader_widget = ps.QtGui.QWidget()
elf_loader_layout = ps.QtGui.QVBoxLayout()


left_layout.addWidget(elf_loader_widget)





# OpenOCD connection
oocd_conn = openocd.launch('stm32f4')

# plotter startup
plotter = rtplot.PlotDispatch(right_layout)
plotter.start()

# tracker startup
reader = tracker.VarTracker()

# Qt Main Loop
mw.show()
ps.QtGui.QApplication.instance().exec_()

