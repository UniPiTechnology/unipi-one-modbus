import six
import asyncio
import logging

from .gpiochip import GpioChip
from .. import rpcmethods as virtual
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type

@six.add_metaclass(DevMeta)
class PigInput(virtual.CoilProvider, virtual.RegisterProvider):

    #__devname__  = 'inputs'

    def __init__(self, name, channel, pin, debounce, countermode, input, register, reg_bit, debounce_reg, counter_reg):
        self.name = name
        self.circuit = parse_name(name)
        self.channel = channel
        self.pin = pin
        self.value = None
        self.debounce = debounce
        self.countermode = countermode
        self.input = input
        self.register = register
        self.reg_bit = reg_bit
        self.debounce_reg = debounce_reg
        self.counter_reg = counter_reg
        self.reverse = False
        self.counter = 0
        self.mask = 1 << pin
        self.pending = None

    def check(self):
        device = check_dev_type(self.channel, GpioChip, 'Input %s'%self.name, 'channel')
        self.channel = device
        self.set_reversed(False)
        self.set_countermode(self.countermode)
        self.channel.register_callback(self.mask, self.event0)

    def create_register_map(self, datastore):
        datastore[self.register]  = 0
        datastore[self.counter_reg]   = 0
        datastore[self.counter_reg+1] = 0
        datastore[self.debounce_reg]  = 0
        self.rdatastore = datastore
        return dict(((self.register, None), 
                     (self.counter_reg, None), (self.counter_reg+1, None), 
                     (self.debounce_reg, lambda reg,deb: self.set_debounce(deb[0]))))

    def create_coil_map(self, datastore):
        datastore[self.input] = 0
        self.cdatastore = datastore
        return dict(((self.input,None),))

    def set_reversed(self, reverse=True):
        '''  values from pigpio/rpi/unipi1 are default REVERSED
        ''' 
        self.reverse = reverse
        if reverse:
            self.to_value = lambda x: 0 if x==0 else 1
        else:
            self.to_value = lambda x: 1 if x==0 else 0

    def set_countermode(self, countermode):
        self._counter_mode = 1 if countermode == 'rising' else 0

    def set_debounce(self, debounce):
        self.debounce = int(round(debounce/10, 0))
        self.rdatastore[self.debounce_reg] = self.debounce * 10
        if self.debounce:
            self.channel.register_callback(self.mask, self.debounce_event)
        else:
            self.channel.register_callback(self.mask, self.event)

    def event0(self, level, tick, seq):
        self.value = self.to_value(level)
        logging.debug(f'Input Event0: {self.name} {"%08x"%level}')
        if hasattr(self,'rdatastore') and hasattr(self,'cdatastore'):
            self.rdatastore[self.counter_reg] = self.counter
            if self.value:
                self.rdatastore[self.register] &= (1<<self.reg_bit)
            else:
                self.rdatastore[self.register] |= (1<<self.reg_bit)
            self.cdatastore[self.input] = self.value
            self.set_debounce(self.debounce * 10)

    def event(self, level, tick, seq):
        value = self.to_value(level)
        logging.debug(f'Input Event: {self.name} {"%08x"%level} {tick} {seq}')
        if self.value != value:
            self.value = value
            if value == self._counter_mode:
                self.counter += 1
            if value:
                self.rdatastore[self.register] &= (1<<self.reg_bit)
            else:
                self.rdatastore[self.register] |= (1<<self.reg_bit)
            self.rdatastore[self.counter_reg] = self.counter
            self.cdatastore[self.input] = self.value


    def debounce_event(self, level, tick, seq):

        async def debcallback():
            await asyncio.sleep(self.debounce/1000.0)
            await self.event(level, tick, seq)
            self.pending = None

        logging.debug(f'Input Debounce: {self.name} {"%08x"%level} {tick} {seq}')
        if self.pending:
            self.pending.cancel()
            self.pending = None
        value = self.to_value(level)
        if value != self.value:
            self.pending = asyncio.create_task(debcallback())



Foptions = {
    'channel':  {'type': 'node', 'help': 'Link to pigpio bus' },
    'pin':      {'type': int, 'help': 'HW pin number of input' },
    'debounce': {'type': int, 'help': 'Debouncing time in ms. default not set', 'default': 0},
    'countermode': {'type': str, 'help': 'How to count pulses. Allowed rising, falling. Default rising' ,'default': 'rising'},
    'input':    {'type': int, 'help': 'Input in modbus map containing input', 'default': 0 },
    'register': {'type': int, 'help': 'Register in modbus map containing combined inputs value', 'default': 0 },
    'reg_bit':  {'type': int, 'help': 'Bit number in combined inputs value', 'default': 0 },
    'debounce_reg': {'type': int, 'help': 'Register in modbus map containing debounce value', 'default': 1010 },
    'counter_reg': {'type': int, 'help': 'Register in modbus map containing counter value', 'default': 0 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return PigInput(devname, **kwargs)
