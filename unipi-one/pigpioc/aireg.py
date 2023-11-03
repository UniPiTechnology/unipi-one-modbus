import asyncio
import logging

from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian

from .mcp342x import Mcp342x
from .bus import PigBus
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type
from .. import rpcmethods as virtual

class AiReg(virtual.RegisterProvider, metaclass=DevMeta):

    #__devname__  = 'inputs'

    def __init__(self, name, channel, port, resolution, gain, calibration, register, resolution_reg):
        self.name = name
        self.circuit = parse_name(name)
        self.channel = channel
        self.port = port
        self.resolution = resolution
        self.gain = gain
        self.calibration = calibration
        self.register = register
        self.resolution_reg = resolution_reg
        self.value = 0


    def check(self):
        device = check_dev_type(self.channel, Mcp342x, 'AiReg %s'%self.name, 'chip Mcp342x')
        self.channel = device
        self.channel.register_port(self.event)


    def create_register_map(self, datastore):
        datastore[self.register]   = 0
        datastore[self.register+1] = 0
        datastore[self.resolution_reg] = self.resolution
        self.rdatastore = datastore
        return dict(((self.register, None), (self.resolution_reg, self.set_resolution)))


    # modbus -> hardware
    def set_resolution(self, register, value):
        assert(register == self.resolution_reg)
        if type(value) in (list, tuple): value = value[0]
        if value not in (12,14,16,18):
            return
        self.resolution = value
        if hasattr(self,'rdatastore'):
            self.rdatastore[self.resolution_reg] = self.resolution


    async def event(self):
        try:
            result = await self.channel.measure_port(self.port, self.resolution, self.gain)
            if (result is not None) and hasattr(self,'rdatastore'):
                builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
                builder.add_32bit_float(result * self.calibration)
                regs = builder.to_registers()
                self.rdatastore[self.register] = regs[0]
                self.rdatastore[self.register+1] = regs[1]

        except Exception as E:
            logging.error(f"ADC measure on {self.name}: {E.__class__.__name__} {E.args[-1]}")



Foptions = {
    'channel':    {'type': 'node', 'help': 'Link to pigpio bus' },
    'port':       {'type': int, 'help': 'Port number of input channel. 0-1', 'default':0 },
    'resolution': {'type': int, 'help': 'ADC resolution in bits. 12,14,16 or 18', 'default':18 },
    'gain':       {'type': int, 'help': 'Amplifier gain. 1,2,4 or 8, default 1', 'default':1 },
    'calibration':{'type': float, 'help': 'Calibration konstant to convert ADC result to Voltage, default 11.419', 'default':11.419 },
    'register':       {'type': int, 'help': 'Register in modbus map containing Ai value in [V]', 'default': 0 },
    'resolution_reg': {'type': int, 'help': 'Register in modbus map containing resolution in bits', 'default': 1010 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return AiReg(devname, **kwargs)
