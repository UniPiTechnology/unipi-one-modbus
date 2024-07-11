import asyncio
import logging

from .. import rpcmethods as virtual
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type

class DirectoryRegisters(virtual.CoilProvider, virtual.RegisterProvider, metaclass=DevMeta):

    def __init__(self, name, path, min_reg):
        self.name = name
        self.circuit = parse_name(name)
        self.path = path
        self.min_reg = min_reg
        self.rdatastore = None


    def create_register_map(self, datastore):
        self.rdatastore = datastore
        return dict(((self.register, None),
                     (self.counter_reg, self.set_counter),
                     (self.counter_reg+1, self.set_counter),
                     (self.debounce_reg, lambda reg, values: self.set_debounce(values[0])),
                     ))

    async def run(self):
        try:
            config = dict(((pin,
                        gpiod.LineSettings(
                            direction=Direction.INPUT,
                            edge_detection=Edge.BOTH,
                            bias=Bias.PULL_UP,
                            debounce_period=timedelta(milliseconds=self.debounces.get(pin,5))
                        )
                    ) for pin in self.notify_callbacks))
            logging.debug(f"Open gpio notify {self.chip_path}")
            self.request = gpiod.request_lines(self.chip_path, consumer="unipi-one-modbus", config=config)
            values = self.request.get_values()
            try:
                coros = filter(lambda cor: asyncio.iscoroutine(cor),
                        (cb(1 if values[i] == Value.ACTIVE else 0, pin, 0)
                         for i,(pin, cb) in enumerate(self.notify_callbacks.items())))
                [ asyncio.create_task(coro) for coro in coros ]
            except Exception as E:
                logging.error(f"Gpio notify connect callback error: {str(E)}")
                #import traceback,sys
                #traceback.print_exc(file=sys.stdout)

            loop = asyncio.get_running_loop()

            os.set_blocking(self.request.fd, False)
            loop.call_soon(loop._add_reader, self.request.fd, self._read_ready)

        except Exception as E:
            logging.error(f"Gpio notify connect error: {str(E)}")
            #logging.critical("Error %s %s", sys.exc_info()[0],sys.exc_info()[1])
            #import traceback,sys
            #traceback.print_exc(file=sys.stdout)

    def check(self):
        device = check_dev_type(self.channel, GpioChip, 'Input %s'%self.name, 'channel')
        self.channel = device
        self.set_reversed(False)
        self.set_countermode(self.countermode)
        self.channel.register_callback(self.pin, self.event0, self.debounce)

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


    async def set_debounce(self, debounce):
        try:
            self.debounce = int(round(debounce/10, 0))
            await self.channel.set_debounce(self.pin, self.debounce)
            self.rdatastore[self.debounce_reg] = self.debounce * 10
        except Exception as E:
            logging.error(f"DI {self.name} set_debounce to {debounce}: {str(E)}")
            #import traceback, sys
            #traceback.print_exc(file=sys.stdout)

    def set_counter(self, register, values):
        try:
            if (register != self.counter_reg) or (len(values) < 2):
                raise ValueError('Required 2 register values')
            self.counter = values[0] + (values[1] << 16)
            if hasattr(self,'rdatastore'):
                self.rdatastore[register] = values[0]
                self.rdatastore[register+1] = values[1]
        except Exception as E:
            logging.error(f"DI {self.name} set_counter to {values[:2]}: {str(E)}")
            raise E

    def event0(self, level, tick, seq):
        self.value = self.to_value(level)
        logging.debug(f'Input Event0: {self.name} {"%08x"%level}')
        if hasattr(self,'rdatastore') and hasattr(self,'cdatastore'):
            self.rdatastore[self.counter_reg] = self.counter
            if self.value:
                self.rdatastore[self.register] |= (1<<self.reg_bit)
            else:
                self.rdatastore[self.register] &= ~(1<<self.reg_bit)
            self.cdatastore[self.input] = self.value
            self.rdatastore[self.debounce_reg] = self.debounce * 10
            self.channel.register_callback(self.pin, self.event, self.debounce)

    def event(self, level, tick, seq):
        value = self.to_value(level)
        logging.debug(f'Input Event: {self.name} {"%08x"%value} {self.value} {tick} {seq}')
        if self.value != value:
            self.value = value
            if value == self._counter_mode:
                self.counter += 1
            if value:
                self.rdatastore[self.register] |= (1<<self.reg_bit)
            else:
                self.rdatastore[self.register] &= ~(1<<self.reg_bit)
            self.rdatastore[self.counter_reg] = self.counter & 0xffff
            self.rdatastore[self.counter_reg+1] = self.counter >> 16
            self.cdatastore[self.input] = self.value


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
    return GpiodInput(devname, **kwargs)


Foptions = {
    #'channel': {'type': 'node', 'help': 'Link to Pigpio bus' },
    'path': {'type': str, 'help': 'Directory with files containing register values. Default /run/unipi-plc/virtual-regs', 'default':'/run/unipi-plc/virtual-regs' },
    'min_reg': {'type': int, 'help': 'Minimal register number in directory', 'default': 4000 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return DirectoryRegisters(devname, **kwargs)


