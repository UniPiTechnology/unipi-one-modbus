import six
import logging
import asyncio
from pigpio import error as EPigpio

from .bus import PigBus
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type


MCP23008_IODIR = 0x00  # direction 1=inp, 0=out
MCP23008_IPOL = 0x01  # reversed input polarity.
MCP23008_GPPU = 0x06  # pullup
MCP23008_GPIO = 0x09  # input/output
MCP23008_OLAT = 0x0A  # latch output status


@six.add_metaclass(DevMeta)
class Mcp230xx:

    def __init__(self, name, channel, i2cbus, address, num_gpios):
        self.name = name
        self.circuit = parse_name(name)
        self.channel = channel
        self.i2cbus = i2cbus
        self.address = address
        self.num_gpios = num_gpios
        self.callbacks = []
        self.maskcallbacks = {}
        self.lock = asyncio.Lock()
        self.starting_mask = 0
        self.starting_value = 0
        #self.running_lock = asyncio.Lock()


    def check(self):
        device = check_dev_type(self.channel, PigBus, 'Chip %s'%self.name, 'channel')
        self.channel = device
        self.channel.register_start_callback(self.start_event)

    def register_relay(self, mask, callback):
        self.maskcallbacks[str(mask)] = callback

    def register_callback(self, callback):
        self.callbacks.append(callback)

    async def start_event(self):
        #print('startup')
        #if False: # To Remove - Simulation
        while True:
            try:
                async with self.lock:
                    self.channel.register_stop_callback(self.stop_event)
                    self._i2c_handle = await self.channel.i2c_open(self.i2cbus, self.address)
                    await self.channel.i2c_writereg(self._i2c_handle, MCP23008_IODIR, 0x00)  # all output !
                    await self.channel.i2c_writereg(self._i2c_handle, MCP23008_GPPU,  0x00)  # no pullup, not req on output
                    self.value = await self.channel.i2c_readreg(self._i2c_handle, MCP23008_OLAT)
                    if self.starting_mask: 
                        self.value = (self.value & (~self.starting_mask)) | self.starting_value
                        self.starting_mask = 0
                        await self.channel.i2c_writereg(self._i2c_handle, MCP23008_GPIO,  self.value)
            except EPigpio as E:
                logging.error(f"{self.name} Mcp230xx/pigpio: {E}")
                await asyncio.sleep(15)
            else:
                break;
        #else:
        #   await asyncio.sleep(0.1)
        #   self.value = 0x22

        await asyncio.gather(*(callback(self.value & int(mask)) for (mask, callback) in self.maskcallbacks.items()))
        coros = filter(lambda cor: asyncio.iscoroutine(cor), (cb(self.value) for cb in self.callbacks))
        await asyncio.gather(*coros)


    async def stop_event(self):
        await self.channel.i2c_close(self._i2c_handle)


    async def send(self, mask, boolvalue):
        if not hasattr(self, 'value'):
            self.starting_mask |= mask
            if boolvalue:
                 self.starting_value |= mask 
            else:
                 self.starting_value &= (~mask)
            return
        async with self.lock:
            if boolvalue:
                self.value |=  mask
            else:
                self.value &=  (~mask)
            await self.channel.i2c_writereg(self._i2c_handle, MCP23008_GPIO,  self.value)
        try:
            await self.maskcallbacks[str(mask)](boolvalue)
        except KeyError:
            pass

    async def sendbits(self, mask, bitsvalue):
        if not hasattr(self, 'value'):
            self.starting_mask |= mask
            self.starting_value &= mask 
            self.starting_value |= bitsvalue 
            return
        async with self.lock:
            self.value &=  (~mask)
            self.value |=  bitsvalue
            await self.channel.i2c_writereg(self._i2c_handle, MCP23008_GPIO,  self.value)
        try:
            coros = filter(lambda cor: asyncio.iscoroutine(cor), (cb(self.value) for cb in self.callbacks))
            await asyncio.gather(*coros)
            #await asyncio.gather(*(callback(self.value) for callback in self.callbacks))
        except KeyError:
            pass


Foptions = {
    'channel': {'type': 'node', 'help': 'Link to Pigpio bus' },
    'i2cbus':  {'type': int, 'help': 'Bus number. Default 1', 'default': 1 },
    'address': {'type': int, 'help': 'I2C address of chip', 'default' : 0x20 },
    'num_gpios'  : {'type': int, 'help': 'Number of gpios on chip. Default 8', 'default' : 8 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return Mcp230xx(devname, **kwargs)

