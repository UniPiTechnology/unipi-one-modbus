
import os
import sys

def read_virtual_reg(path:str) -> int:
    with open(path, 'r') as f:
        s = f.readline()
    val = int(s)
    if val < 0: val = 0x10000 + val
    return val & 0xffff

def scan_dir(path:str, min_reg:int, lasttime:int):
    try:
        for entry in os.scandir(path):
            if not entry.is_dir():
                fname = os.path.basename(entry.path)
                try:
                    r = int(fname)
                    if r >= min_reg and r < 0x10000:
                        try:
                            #print(entry.path, entry.stat().st_mtime, file=sys.stderr)
                            mtime = entry.stat().st_mtime
                            if mtime > lasttime:
                                val = read_virtual_reg(entry.path)
                                print(f"{r} {val}")
                            else:
                                print(f"{r} .")
                        except Exception as E:
                            print(f"{r}")
                            print(f"Error reading file {entry.path} {E}", file=sys.stderr)
                except ValueError:
                    pass
    except ValueError as E: #Exception as E:
        print(f"Exception: {E}", file=sys.stderr)

try:
    min_reg = int(sys.argv[2])
except Exception:
    min_reg = 4000

try:
    lasttime = int(sys.argv[3])
except Exception:
    min_reg = 0

scan_dir(sys.argv[1], min_reg, lasttime)
