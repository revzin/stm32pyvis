import PySide as ps

import elftools
import rtplot
import tracker as trk

# ------------------------------------------------------------------------ #
# Global stuff

# a list of rtplot.PlotVariables
all_vars = []

# gui_list_item[QListWidgetItem] = associated variable
gui_list_item = {}

# Qt list
var_list_widget = None

# rtplot.PlotDispatch
plotter = None

# tracker.VarTracker
tracker = None

# Parent layout for PlotDistach
right_layout = None

def elf_path_dialog():
    import os
    path, _ = ps.QtGui.QFileDialog.getOpenFileName()
    on_elf_load(path)


def on_shutdown():
    global plotter, tracker
    if plotter:
        plotter.stop()
    if tracker:
        tracker.stop()


def elf_to_vars(elf_path):
    global all_vars
    var_symbols = elftools.get_vars_name_address(elf_path)

    if not var_symbols:
        return False

    for var_name in var_symbols:
        all_vars.append(rtplot.WatchVariable(name=var_name, address=var_symbols[var_name]))

    return True


def remove_item(list_widget, widget_item):
    list_widget.takeItem(list_widget.row(widget_item))


def all_list_items(q_list_widget):
    for i in range(q_list_widget.count()):
        yield q_list_widget.item(i)

def vars_to_gui():
    global all_vars, gui_list_item, var_list_widget

    for item in all_list_items(var_list_widget):
        remove_item(var_list_widget, item)

    for variable in all_vars:
        new_item = ps.QtGui.QListWidgetItem(variable.name, var_list_widget)


def on_track_changed():
    global all_vars, gui_list_item, var_list_widget, \
        plotter, tracker, all_vars, oocd_conn

    def list_item_to_var(list_item):
        global all_vars

        for variable in all_vars:
            if variable.name == list_item.text():
                return variable

        return None

    if not plotter or not tracker:
        return

    prev_vars = set(tracker.vars)
    curr_vars = set([list_item_to_var(list_item) for list_item in var_list_widget.selectedItems()])

    track_remove = prev_vars - curr_vars
    track_add = curr_vars - prev_vars

    for var in list(track_remove):
        plotter.remove_var(var)
        tracker.remove_track_var(var)

    for var in list(track_add):
        tracker.add_track_var(var)
        plotter.plot_var(var)

    return True


def on_elf_load(elf_path):
    global plotter, tracker, all_vars, oocd_conn, right_layout

    if plotter:
        plotter.stop()
        del plotter
    if tracker:
        tracker.stop()
        del tracker

    all_vars = []
    rc = elf_to_vars(elf_path)

    if not rc or len(all_vars) == 0:
        print("[INFO] Empty or malformed ELF file!")
        return False

    # plotter startup
    plotter = rtplot.PlotDispatch(right_layout)
    plotter.start()

    # tracker startup
    tracker = trk.VarTracker(0.05)
    tracker.start()

    vars_to_gui()

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
elf_loader_widget.setLayout(elf_loader_layout)

left_layout.addWidget(elf_loader_widget)

load_elf_button = ps.QtGui.QPushButton("&Load ELF")
load_elf_button.clicked.connect(elf_path_dialog)
elf_loader_layout.addWidget(load_elf_button)

update_tracklist_button = ps.QtGui.QPushButton("&Update tracking set")
update_tracklist_button.clicked.connect(on_track_changed)
elf_loader_layout.addWidget(update_tracklist_button)

var_list_widget = ps.QtGui.QListWidget()
var_list_widget.setSelectionMode(ps.QtGui.QAbstractItemView.ExtendedSelection)

elf_loader_layout.addWidget(var_list_widget)

center_widget.dumpObjectTree()

# Qt Main Loop
mw.show()
ps.QtGui.QApplication.instance().exec_()
