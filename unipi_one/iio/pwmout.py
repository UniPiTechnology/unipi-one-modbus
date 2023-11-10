import asyncio
import logging

from .. import rpcmethods as virtual
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type

class PwmOut(virtual.RegisterProvider, metaclass=DevMeta):

    #__devname__  = 'inputs'

    def __init__(self, name, path, frequency, register, frequency_reg, falling ):
        self.name = name
        self.circuit = parse_name(name)
        self.register = register
        self.frequency_reg = frequency_reg
        self.falling = falling
        self.value = 0

        self.frequency = frequency
        self.offset = -3.3
        self.running_lock = asyncio.Lock()
        self.path = path


    #def check(self):
    #    device = check_dev_type(self.channel, PigBus, 'PwmOut %s'%self.name, 'channel')
    #    self.channel = device
        #self.set_countermode(self.countermode)
    #    self.channel.register_start_callback(self.startevent)


    def create_register_map(self, datastore):
        datastore[self.register]   = self.value
        datastore[self.frequency_reg] = self.frequency
        self.rdatastore = datastore
        #return dict(((self.register, self.outputr),))
        return dict(((self.register, self.outputr), (self.frequency_reg, self.set_frequency)))


    # modbus -> hardware
    async def outputr(self, register, value):
        try:
            assert(register == self.register)
            if type(value) in (list, tuple): value = value[0]
            value = min(max(value,0),1000)
            async with self.running_lock:
                rvalue = value if not self.falling else 1000-value
                await self.write_attr('duty_cycle', max(int(round(((rvalue)+self.offset)*self.mul, 0)), 0))
                self.value = value #await self.channel.pwm_getduty(self.pin)
            if hasattr(self,'rdatastore'):
                self.rdatastore[self.register] = self.value
        except Exception as E:
            logging.error(f"Pwm set_frequency to {value}: {str(E)}")


    async def set_frequency(self, register, value):
        try:
            assert(register == self.frequency_reg)
            if type(value) in (list, tuple): value = value[0]
            async with self.running_lock:
                period = int(1000000000 / value)
                await self.write_attr('period', period)
                self.frequency = value
                self.mul = period / 1000.0
            if hasattr(self,'rdatastore'):
                self.rdatastore[self.frequency_reg] = self.frequency
        except Exception as E:
            logging.error(f"Pwm set_frequency to {value}: {str(E)}")

    async def write_attr(self, attr, value):
        def write_it(fpath, val):
            with open(fpath, 'w') as f:
               f.write(val)
        await asyncio.to_thread(write_it, self.path+attr, str(value))


    async def run(self):
        try:
            period = int(1000000000 / self.frequency)    # period = 1GHz / f
            self.mul = period / 1000.0
            rvalue = self.value if not self.falling else 1000-self.value
            await self.write_attr('period', period)
            await self.write_attr('duty_cycle', max(int(round((rvalue+self.offset)*self.mul, 0)), 0))
            await self.write_attr('enable', 1)
            logging.debug(f"PWM event {self.name} {self.value} {self.frequency}")

            if hasattr(self,'rdatastore'):
                self.rdatastore[self.register] = self.value # ToDo: konverze ?
                self.rdatastore[self.frequency_reg] = self.frequency
        except Exception as E:
            logging.error(f"Pwm start error: {str(E)}")



Foptions = {
    #'channel':  {'type': 'node', 'help': 'Link to pigpio bus' },
    'path':      {'type': str, 'help': 'Sysfs path to pwm channel', 'default':'/sys/class/pwm/pwmchip0/pwm0/' },
    'frequency': {'type': int, 'help': 'Frequency of PWM in Hz. Default 1000Hz', 'default': 1000 },
    'register':  {'type': int, 'help': 'Register in modbus map containing output value', 'default': 0 },
    'frequency_reg': {'type': int, 'help': 'Register in modbus map containing frequency in Hz', 'default': 1010 },
    'falling': {'type': int, 'help': 'Set it to 1 for Unipi 1.0 board', 'default': 0 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return PwmOut(devname, **kwargs)
