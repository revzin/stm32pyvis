import sys
import tkinter as tk
import time
import threading

import openocd
import elftools
import plotter

# --------------------------------------------------------------------------- #
# main logic

stuff_doer = None
dynplotter = None
connection = None
var_dict = None
var_name = None
var_value = None
interval = 0.01


def stuff_doer_thread():
    global connection, var_dict, var_name, var_value, interval, dynplotter
    while True:
        if var_dict and var_name and connection:
            if var_name in var_dict.keys():
                var_value = openocd.read_value(connection, var_dict[var_name], 32)
                print(var_name + ' = {}'.format(var_value))
                if dynplotter:
                    dynplotter.append(var_value)
        else:
            if not connection:
                print ('[INFO] No OpenOCD connection, Stuff Doer Thread exits...')
                return
        time.sleep(interval)


def cleanup_everything():
    global connection
    stuff_doer.join(1)
    connection = None
    openocd.pkill()
    exit(0)

# --------------------------------------------------------------------------- #
# tk crap

master = None
var_value_tkvar = None

def update_value():
    global master, var_value, var_name, var_value_tkvar
    var_value_tkvar.set(str(var_name) + ' = ' + str(var_value))

    master.after(int(interval * 1000), update_value)


def build_var_dropdown():
    global var_dict
    dropdown_names = []
    for key in var_dict.keys():
        dropdown_names.append(key)
    return dropdown_names


def on_var_dropdown_change(current_value):
    global var_name
    print('Set tracking to', current_value)
    var_name = current_value


def tk_build():
    global var_value_tkvar
    global master
    master = tk.Tk()
    master.geometry("480x360")
    master.after(int(interval * 1000), update_value)
    master.protocol('WM_DELETE_WINDOW', cleanup_everything)

    view_name = tk.StringVar(master)
    view_name.set("None")  # default value
    dropdown_items = build_var_dropdown()

    var_selector = tk.OptionMenu(master, view_name, command=on_var_dropdown_change, *dropdown_items)
    var_selector.pack()

    var_value_tkvar = tk.StringVar()
    var_value_tkvar.set("No track")

    var_value_label = tk.Label(master, textvariable=var_value_tkvar)
    var_value_label.pack()


# --------------------------------------------------------------------------- #
# entry
print('stm32pyvis')

if len(sys.argv) < 2:
    print('[INFO] Usage: python3 main.py elf_file_name')
    print('[ERROR] Malformed arguments, exiting...')
    exit(-1)

file_name = sys.argv[1]

print('[INFO] loading ELF {}'.format(file_name))
var_dict = elftools.get_var_names(file_name)

if not var_dict:
    print("[ERROR] Weren't able to open {}".format(file_name))
    exit(-4)

if 0 == len(var_dict):
    print('[ERROR] Empty or invalid ELF file, exiting')
    exit(-2)

openocd.pkill()
connection = openocd.launch('stm32f4')

if not connection:
    print('[ERROR] OpenOCD connection failed, exiting')
    exit(-3)

openocd.run_mcu(connection)

stuff_doer = threading.Thread(target=stuff_doer_thread)
stuff_doer.start()

dynplotter = plotter.DynamicPlotter()
plot_thread = threading.Thread(target = dynplotter.run)
plot_thread.start()

print('[INFO] GUI start...')
tk_build()
tk.mainloop()
