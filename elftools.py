import subprocess as sp
import os, re, random

def get_var_names(elf_file_path):

    def run_readelf(file_path):
        temp_file_name = str(random.randint(100000, 999999)) + '.out'
        file = open(temp_file_name, mode='w')
        if not file:
            print('[ERROR] Failed to open file for writing:', temp_file_name)
        try:
            sp.check_call(['readelf', '-s', file_path], stdout=file)
        except sp.CalledProcessError as err:
            print('[ERROR] readelf failed with code ', err.returncode)
            return None
        except BrokenPipeError as bpe:
            print('[ERROR] Some weird pipe seems broken somewhere, exiting')
            return None
        return temp_file_name

    def var_parameters(temp_file_path):

        def addr_in_sram(addr):
            sram_base = 0x20000000
            sram_size = 0x1000
            return sram_base <= addr <= sram_base + sram_size

        # num, address, size, type, bin, vis, Ndx, name (total = 8)
        # 1     2       3       4   5     6     7   8
        var_symbols = {}
        with open(temp_file_path, 'r') as file:
            if not file:
                print('[ERROR] failed to open({})'.format(temp_file_path))
                return None
            for line in file:
                split_line = re.split('[ \t]+', line)
                if len(split_line) != 9:
                    continue
                else:
                    try:
                        var_addr = int(split_line[2], 16)
                    except ValueError:
                        continue

                    var_name = str(split_line[8])
                    sym_type = str(split_line[4])
                    var_name = var_name.replace('\r', '')
                    var_name = var_name.replace('\n', '')
                    # at least try to filter out crap that isn't variables
                    if sym_type in ('NOTYPE', 'OBJECT') and not var_name.startswith('$') and addr_in_sram(var_addr) \
                            and not '.' in var_name:
                        var_symbols[var_name] = var_addr

        if 0 == len(var_symbols):
            print('[ERROR] Empty symbol table read from ', temp_file_path)
            return None
        else:
            print ('[INFO] readelf: found {} entries'.format(len(var_symbols)))
            return var_symbols

    readelf_out_path = run_readelf(elf_file_path)
    if not readelf_out_path:
        print('[ERROR] Readelf failed')
        return None
    rt = var_parameters(readelf_out_path)
    os.remove(readelf_out_path)
    return rt


