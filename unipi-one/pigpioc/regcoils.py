import asyncio
import logging

from .mcp230xx import Mcp230xx
from .bus import PigBus
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type
from .. import rpcmethods as virtual


class RegCoils(virtual.CoilProvider, virtual.RegisterProvider, metaclass=DevMeta):

    def __init__(self, name, channel, pins, register, start_coil):
        self.name = name
        self.circuit = parse_name(name)
        self.chip = channel
        self.pins = pins
        #self.value = None
        self.register = register
        self.start_coil = start_coil
        self._mask = sum((1 << pin) for pin in pins)
        self.running_lock = asyncio.Lock()

    def check(self):
        device = check_dev_type(self.chip, Mcp230xx, 'Output %s'%self.name, 'chip')
        self.chip = device
        self.chip.register_callback(self.event0)

    def create_register_map(self, datastore):
        datastore[self.register] = 0
        self.rdatastore = datastore
        return dict(((self.register, self.outputr),))

    def create_coil_map(self, datastore):
        for i in range(len(self.pins)): datastore[self.start_coil+i] = 0
        self.cdatastore = datastore
        d=dict(((self.start_coil+i, self.outputc) for i in range(len(self.pins))))
        return d

    # modbus -> hardware
    async def outputr(self, register, value):
        assert(register == self.register)
        if type(value) in (list, tuple): value = value[0]
        chip_value = sum(((1<<pin) if (value & (1<<i)) else 0 for i, pin in enumerate(self.pins)))
        async with self.running_lock:
            await self.chip.sendbits(self._mask, chip_value)

    async def outputc(self, coil, values):
        assert(coil >= self.start_coil)
        start = coil - self.start_coil
        if not(type(values) in (list, tuple)): values = (values,)
        chip_value = sum(((1<<self.pins[start+i]) if value else 0 for i, value in enumerate(values)))
        mask = sum(((1<<self.pins[start+i]) for i, value in enumerate(values)))
        async with self.running_lock:
            logging.debug(f'Regcoils - set coils {"%02x" % chip_value}/{"%02x" % mask}')
            await self.chip.sendbits(mask, chip_value)

    # hardware -> modbus
    def event0(self, item):
        if hasattr(self,'rdatastore') and hasattr(self,'cdatastore'):
            logging.debug(f'Regcoils - event0 {item}')
            self.rdatastore[self.register] = sum(((1<<i) if (item & (1<<pin)) else 0 for i, pin in enumerate(self.pins)))
            for i,pin in enumerate(self.pins):
                self.cdatastore[self.start_coil+i] = 1 if (item & (1<<pin)) else 0
            #self.chip.register_relay(self._mask, self.event)

    def event(self, item):
        logging.debug(f'Regcoils - event {item}')
        self.rdatastore[self.register] = sum(((1<<i) if (item & (1<<pin)) else 0 for i, pin in enumerate(self.pins)))
        for i,pin in enumerate(self.pins):
            self.cdatastore[self.start_coil+i] = 1 if (item & (1<<pin)) else 0



Foptions = {
    'channel': {'type': 'node', 'help': 'Link to mcp230xx chip' },
    'pins':     {'types': int, 'help': 'Array of bit number in chip register' },
    'register': {'type': int, 'help': 'Register in modbus map containing relays', 'default': 0 },
    'start_coil': {'type': int, 'help': 'First coil in modbus map containing relays', 'default': 0 },
}


def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return RegCoils(devname, **kwargs)

