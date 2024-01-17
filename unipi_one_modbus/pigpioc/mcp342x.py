######################################

# Analog Inputs on MCP 342x

import logging
import asyncio

from .bus import PigBus
from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type


class Mcp342x(metaclass=DevMeta):

    BIT_MASKS = (
        (  0x7ff, 3, 1.0 / 240), #12bit including sign: maxvalue, datalength, waittime (= 1 / sample rate)
        ( 0x1fff, 3, 1.0 / 60),  #14bit including sign
        ( 0x7fff, 3, 1.0 / 15),  #16bit including sign
        (0x1ffff, 4, 1.0 / 3.75) #18bit including sign
    )

    def __init__(self, name, channel, i2cbus, address):
        self.name = name
        self.circuit = parse_name(name)
        self.channel = channel
        self.i2cbus = i2cbus
        self.address = address
        self.ports = []
        self.lock = asyncio.Lock()

    def check(self):
        device = check_dev_type(self.channel, PigBus, 'Chip %s'%self.name, 'channel')
        self.channel = device
        self.channel.register_start_callback(self.start_event)


    def register_port(self, port):
        self.ports.append(port)


    async def start_event(self):
        #print('startup')
        self.channel.register_stop_callback(self.stop_event)
        self._i2c_handle = await self.channel.i2c_open(self.i2cbus, self.address)
        async def run():
            try:
                await self.measure_loop()
            except Exception as E:
                logging(f"ADC loop {self.name} error: {str(E)}")

        logging.debug(f"Starting ADC loop for {self.name}")
        self._task = asyncio.create_task(run(), name="ADC loop")
        #await asyncio.gather(*(callback(self.value & int(mask)) for (mask, callback) in self.callbacks)))

    async def stop_event(self):
        logging.debug(f"Stopping ADC loop for {self.name}")
        if hasattr(self,'_task'): self._task.cancel()
        await self.channel.i2c_close(self._i2c_handle)


    def calc_mode(self, port, bits, gain):
        #if not (port in range(4)): raise Exception("Bad channel number")
        port = port & 0x3
        #mode = mode | (bool(continuous) << 4) | ((not bool(continuous)) << 7)  # from one-shoot must be bit7 set
        """ sample rate and resolution
            12 = 12 bit (240 SPS max)  3.5 cifry
            14 = 14 bit (60 SPS max)   4 cifry
            16 = 16 bit (15 SPS max)   5 cifer 
            18 = 18 bit (3.75 SPS max) 5.5 cifry
        """
        bits = next((i for i,b in enumerate((12,14,16,18)) if b==bits), 3)
        """ PGA gain selection, default 1
                1 = 1x
                2 = 2x
                4 = 4x
                8 = 8x
        """
        gain = next((i for i,g in enumerate((1,2,4,8)) if g==gain), 0)
        return (port << 5) | (bits << 2) | gain


    async def measure_loop(self):
        i = 0
        while True:
            cnt = len(self.ports)
            if cnt > 0:
                if i >= cnt: i = 0
                try:
                    await self.ports[i]()
                except Exception as E:
                    logging.error(f"ADC measure error: {str(E)}")
                i += 1
            else:
                await asyncio.sleep(1)


    async def measure_port(self, port, bits, gain):

        mode = self.calc_mode(port, bits, gain)
        resolution = (mode >> 2) & 0x03
        maxval, readlen, waittime = self.BIT_MASKS[resolution]
        async with self.lock:
            # set bit7 to start one-shot measure
            await self.channel.i2c_writeshort(self._i2c_handle, mode | 0x80)
            for _ in range(3):
                await asyncio.sleep(waittime)
                data = await self.channel.i2c_readdata(self._i2c_handle, readlen)
                status = data[readlen - 1]
                if status == mode:
                    value = int.from_bytes(data[:-1], byteorder='big', signed=True)
                    return (float(value) / maxval) # * 11.419)
                     #2.048)
                #if status & 0x80: # print("Converting in progress")


Foptions = {
    'channel': {'type': 'node', 'help': 'Link to Pigpio bus' },
    'i2cbus':  {'type': int, 'help': 'Bus number. Default 1', 'default': 1 },
    'address': {'type': int, 'help': 'I2C address of chip', 'default' : 0x20 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return Mcp342x(devname, **kwargs)

