import asyncio
import logging

import six

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
)

from ..rpcmethods import DevMeta, get_kwargs, check_dev_type
from .server import ModbusServer


@six.add_metaclass(DevMeta)
class ModbusSlaveMap(ModbusSlaveContext):

    def __init__(self,  name, channel, slaveid=1):
        ModbusSlaveContext.__init__(self, zero_mode=True)
        self.name = name
        self.slaveid = slaveid
        self.channel = channel


    def check(self):
        channel = check_dev_type(self.channel, ModbusServer, 'Modbus server %s'%self.name, 'channell')
        channel.register_slave(self, self.slaveid)
        self.channel = channel
        self.channel.register_slave(self.slaveid, self)


    def set_datablock(self, blocks, datablock=None):
        """Register a datablock with the slave context.

        :param blocks: set of 'd','h','c','i' 
        :param datablock: datablock to associate with this function code
        """
        if datablock == None: datablock = ModbusSequentialDataBlock.create()
        for block in blocks: 
            self.store[block] = datablock


Foptions = {
    'channel': {'type': 'node', 'help': 'Link to Modbus server' },
    'slaveid':  {'type': int, 'help': 'Modbus slave address for map. Default 1', 'default': 1 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return  ModbusSlaveMap(devname, **kwargs)

