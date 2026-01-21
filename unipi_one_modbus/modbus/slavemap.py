import asyncio
import logging


from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusDeviceContext,
)
from pymodbus.constants import ExcCodes
from pymodbus.exceptions import ParameterException

from pymodbus.pdu import (
    ExceptionResponse, 
)

from ..rpcmethods import DevMeta, get_kwargs, check_dev_type
from .server import ModbusServer


class ModbusSlaveMap(ModbusDeviceContext,metaclass=DevMeta):

    def __init__(self,  name, channel, slaveid=1):
        ModbusDeviceContext.__init__(self)
        self.name = name
        self.slaveid = slaveid
        self.channel = channel
        self.zero_mode = True


    def check(self):
        channel = check_dev_type(self.channel, ModbusServer, 'Modbus server %s'%self.name, 'channel')
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

    async def async_setValues(self, fc_as_hex, address, values):
        """Set the datastore with the supplied values.

        :param fc_as_hex: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        if not self.zero_mode:
            address += 1
        logging.debug(f"setValues[{fc_as_hex}] address={address}: count={len(values)}")
        try:
            await self.store[self.decode(fc_as_hex)].async_setValues(address, values)
        except ParameterException:
            return ExceptionResponse(fc_as_hex, exception_code=ExcCodes.ILLEGAL_ADDRESS)
        except Exception:
            return ExceptionResponse(fc_as_hex, exception_code=ExcCodes.ILLEGAL_VALUE)

    def getValues(self, func_code, address, count=1):
        """Get `count` values from datastore.

        :param func_code: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        if not self.zero_mode:
            address += 1
        logging.debug("getValues: fc-[{func_code}] address={address}: count={count}")
        return self.store[self.decode(func_code)].getValues(address, count)


Foptions = {
    'channel': {'type': 'node', 'help': 'Link to Modbus server' },
    'slaveid':  {'type': int, 'help': 'Modbus slave address for map. Default 1', 'default': 1 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return  ModbusSlaveMap(devname, **kwargs)

