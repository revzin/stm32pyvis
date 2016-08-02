import subprocess as sp
import time
import telnetlib as tl
import re

SIGNED = 0
UNSIGNED = 1

def pkill():
    sp.call(['pkill', 'openocd'])

def run_mcu(connection):
    assert isinstance(connection, tl.Telnet)
    output = command(connection, 'reset run')
    return None

def read_value(connection, address, size_bits, signedness = SIGNED):
    assert isinstance(connection, tl.Telnet)
    assert isinstance(address, int)
    assert signedness in (SIGNED, UNSIGNED)
    size2cmd = {8 : 'mdb', 16 : 'mhw', 32 : 'mdw'}
    assert size_bits in size2cmd.keys()

    output = command(connection, size2cmd[size_bits] + ' ' + hex(address))
    if not output:
        print ('[WARNING] Failed to read at address {}'.format(hex(address)))
    else:
        return int(re.split(': ', output)[-1], 16)


def command(connection, text):
    assert isinstance(connection, tl.Telnet)
    assert isinstance(text, str)

    text += '\n'
    try:
        connection.write(text.encode())
        connection.read_until('\r\n'.encode(), 1) # don't echo the command itself back
        result = connection.read_until('> '.encode(), 1)
    except EOFError as eoe:
        print('[WARNING] OpenOCD: Telnet connection terminated by host!')
        return None
    except BrokenPipeError as bpe:
        print('[INFO] some pipe is broke, so what')
        return None
    if not result:
        print ('[WARNING] OpenOCD: Command timeout!')
        return None

    result = str(result)
    if 'invalid command name' in result:
        print ('[WARNING] OpenOCD: Bad command name!')
        return None
    result = result.replace(' \\r\\n\\r> ', '') # delete trail
    result = result.replace("b'", '') # delete b'
    result = result.replace("'", '')  # delete trailing ' crap
    return result


def launch(target_name):
    openocd_script_path = '/usr/local/share/openocd/scripts/'

    def target2config(target_name):
        t2c_kv = {'stm32f4': 'stm32f4x.cfg',
                    'stm32f3': 'stm32f3x.cfg',
                    'stm32f2': 'stm32f2x.cfg',
                    'stm32f1': 'stm32f1x.cfg',
                    'stm32f0': 'stm32f0x.cfg'}

        if target_name not in t2c_kv.keys():
            print('[ERROR] Invalid target name', target_name)
            print('must be stm32fX, where X = series')
            return None
        else:
            return openocd_script_path + 'target/' + t2c_kv[target_name]

    def openocd_telnet_connect():
        host = 'localhost'
        port = 4444
        try:
            oocd_conn = tl.Telnet(host=host, port=port, timeout=1)
        except ConnectionRefusedError as cre:
            return None

        hello = str(oocd_conn.read_very_eager())

        if 'Open On-Chip Debugger' not in hello:
            print('[ERROR] Unexpected response from TELNET 4444.')
            return None

        return oocd_conn

    config_file_target = target2config(target_name)

    conf_file_stlink2 = openocd_script_path + 'interface/' + 'stlink-v2.cfg'
    conf_file_stlink21 = openocd_script_path + 'interface/' + 'stlink-v2-1.cfg'

    print('[INFO] Launching OpenOCD...')

    oocd = sp.Popen(['openocd', '-f', conf_file_stlink2, '-f', config_file_target])

    print ("[INFO] Waiting 1 second for OpenOCD to do its' own stuff...")
    time.sleep(1)

    print ("[INFO] Connecting to OpenOCD TELNET...")
    oocd_conn = openocd_telnet_connect()

    if not oocd_conn:
        print ('[ERROR] OpenOCD connection failed -- see output...')
        return None

    return oocd_conn

def stop(id):
    pass
