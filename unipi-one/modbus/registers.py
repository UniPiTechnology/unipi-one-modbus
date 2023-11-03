import asyncio
import logging

import six

from .slavemap import ModbusSlaveMap
from .. import rpcmethods as virtual
from ..rpcmethods import DevMeta, get_kwargs, check_dev_type


@six.add_metaclass(DevMeta)
class ModbusRegisters:

    def __init__(self,  name, channel, mode, devs=[]):
        self.name = name
        self.channel = channel
        self.devs = devs
        if mode not in ('registers', 'coils'):
           raise Exception(f"ModbusRegisters {self.name}: bad mode {self.mode}")
        self.mode = mode

    def check(self):
        channel = check_dev_type(self.channel, ModbusSlaveMap, 'ModbusRegisters %s'%self.name, 'channell')
        self.channel = channel
        self.values = {}
        self.setters = {}
        if self.mode == 'registers':
            for dev in self.devs:
                device = check_dev_type(dev, virtual.RegisterProvider, 'ModbusRegister %s'%self.name, 'Provider device')
                if device:
                    self.setters.update(device.create_register_map(self.values))
            channel.set_datablock(('h','i'), self)
        else:
            for dev in self.devs:
                device = check_dev_type(dev, virtual.CoilProvider, 'ModbusRegister %s'%self.name, 'Provider device')
                if device: self.setters.update(device.create_coil_map(self.values))
            channel.set_datablock(('c','d'), self)


    def validate(self, address, count=1):
        """Check to see if the request is in range.

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        """
        if not count:
            return False
        handle = set(range(address, address + count))
        return handle.issubset(set(iter(self.values.keys())))

    def getValues(self, address, count=1):
        """Return the requested values of the datastore.

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        return [self.values[i] for i in range(address, address + count)]

    def setValues(self, address, values, use_as_default=False):
        """Set the requested values of the datastore.

        :param address: The starting address
        :param values: The new values to be set
        :param use_as_default: Use the values as default
        :raises ParameterException:
        """
        if not isinstance(values, list):
            values = [values]
        coros = []
        leader = None
        for idx in range(len(values)):
            if address + idx not in self.setters:
                raise ParameterException("Offset {address+idx} not in range")
            if self.setters[address] != leader:
                leader = self.setters[address]
                if leader:
                    logging.debug(f'ModbusRegiser: Calling setter {leader} with address={address + idx}, vals={values}')
                    coro = leader(address + idx, values)
                    if asyncio.iscoroutine(coro): coros.append(coro)
        if coros:
            [ asyncio.create_task(coro) for coro in coros ]


Foptions = {
    'channel': {'type': 'node', 'help': 'Link to Modbus slave map' },
    'mode': {'type': str, 'help': 'Kind of map. Can be coils or registers' },
    'devs':  {'types': 'node', 'help': 'List of devices providing some registers. Default empty', 'default': [] },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return  ModbusRegisters(devname, **kwargs)

