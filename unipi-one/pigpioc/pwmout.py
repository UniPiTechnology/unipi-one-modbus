import asyncio
import logging

from .bus import PigBus
from .. import rpcmethods as virtual
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type

class PwmOut(virtual.RegisterProvider, metaclass=DevMeta):

    #__devname__  = 'inputs'

    def __init__(self, name, channel, pin, register, frequency_reg):
        self.name = name
        self.circuit = parse_name(name)
        self.channel = channel
        self.pin = pin
        self.register = register
        self.frequency_reg = frequency_reg
        self.value = 0

        self.frequency = 400
        self.running_lock = asyncio.Lock()


    def check(self):
        device = check_dev_type(self.channel, PigBus, 'PwmOut %s'%self.name, 'channel')
        self.channel = device
        #self.set_countermode(self.countermode)
        self.channel.register_start_callback(self.startevent)


    def create_register_map(self, datastore):
        datastore[self.register]   = self.value
        datastore[self.frequency_reg] = self.frequency
        self.rdatastore = datastore
        return dict(((self.register, self.outputr), (self.frequency_reg, self.set_frequency)))


    # modbus -> hardware
    async def outputr(self, register, value):
        assert(register == self.register)
        if type(value) in (list, tuple): value = value[0]
        value = min(max(value,0),1000)
        async with self.running_lock:
            await self.channel.pwm_setduty(self.pin, value)
            self.value = await self.channel.pwm_getduty(self.pin)
        if hasattr(self,'rdatastore'):
            self.rdatastore[self.register] = self.value


    async def set_frequency(self, register, value):
        assert(register == self.frequency_reg)
        if type(value) in (list, tuple): value = value[0]
        async with self.running_lock:
            await self.channel.pwm_setfreq(self.pin, value)
            self.frequency = await self.channel.pwm_getfreq(self.pin)
        if hasattr(self,'rdatastore'):
            self.rdatastore[self.frequency_reg] = self.frequency


    async def startevent(self):
        await self.channel.pwm_setfreq(self.pin, self.frequency)
        await self.channel.pwm_setrange(self.pin, 1000)
        await self.channel.pwm_setduty(self.pin, self.value)
        self.value = await self.channel.pwm_getduty(self.pin)
        self.frequency = await self.channel.pwm_getfreq(self.pin)
        logging.debug(f"PWM event {self.name} {self.value} {self.frequency}")

        if hasattr(self,'rdatastore'):
            self.rdatastore[self.register] = self.value # ToDo: konverze ?
            self.rdatastore[self.frequency_reg] = self.frequency



Foptions = {
    'channel':  {'type': 'node', 'help': 'Link to pigpio bus' },
    'pin':      {'type': int, 'help': 'HW pin number of output', 'default':18 },
    'register':    {'type': int, 'help': 'Register in modbus map containing output value', 'default': 0 },
    'frequency_reg': {'type': int, 'help': 'Register in modbus map containing frequency in Hz', 'default': 1010 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return PwmOut(devname, **kwargs)
