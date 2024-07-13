import asyncio
import logging
import datetime
import sys

from .. import rpcmethods as virtual
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type


async def read_virtual_reg(path):
    pass

class DirectoryRegisters(virtual.CoilProvider, virtual.RegisterProvider, metaclass=DevMeta):

    def __init__(self, name, path, min_reg):
        self.name = name
        self.circuit = parse_name(name)
        self.path = path
        self.min_reg = min_reg
        self.rdatastore = None


    def create_register_map(self, datastore):
        self.rdatastore = datastore
        return dict()

    async def scan_dir(self, lasttime):
        # Create the subprocess; redirect the standard output
        # into a pipe.
        proc = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'unipi_one_modbus.virtuals',self.path, str(self.min_reg), str(lasttime),
            stdout=asyncio.subprocess.PIPE)
        outdata, errordata = await proc.communicate()
        for line in outdata.decode('utf-8').rstrip().split('\n'):
            items = line.split(' ')
            r = int(items[0])
            if len(items) > 1:
                if items[1] != '.':
                    self.rdatastore[r] = int(items[1])
            else:
                    del self.rdatastore[r]

            #print(r,line)
        if errordata:
            logging.debug(errordata.decode('utf-8').rstrip())


    async def run(self):
        lasttime = 0
        while True:
            try:
                atime = int(datetime.datetime.now().timestamp())
                await self.scan_dir(lasttime)
            except Exception as E:
                logging.debug(f"Error scaning dir {self.path} {E}")
                #logging.critical("Error %s %s", sys.exc_info()[0],sys.exc_info()[1])
                #import traceback,sys
                #traceback.print_exc(file=sys.stdout)
            lasttime = atime
            await asyncio.sleep(1)





Foptions = {
    #'channel': {'type': 'node', 'help': 'Link to Pigpio bus' },
    'path': {'type': str, 'help': 'Directory with files containing register values. Default /run/unipi-plc/virtual-regs', 'default':'/run/unipi-plc/virtual-regs' },
    'min_reg': {'type': int, 'help': 'Minimal register number in directory', 'default': 4000 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return DirectoryRegisters(devname, **kwargs)


