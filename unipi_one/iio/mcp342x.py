######################################

# Analog Inputs on MCP 342x

import logging
import asyncio
import iio

from ..rpcmethods import DevMeta, get_kwargs, parse_name, check_dev_type


class Mcp342x(metaclass=DevMeta):

    BIT_MASKS = (
        (  0x7ff, 3, 1.0 / 240), #12bit including sign: maxvalue, datalength, waittime (= 1 / sample rate)
        ( 0x1fff, 3, 1.0 / 60),  #14bit including sign
        ( 0x7fff, 3, 1.0 / 15),  #16bit including sign
        (0x1ffff, 4, 1.0 / 3.75) #18bit including sign
    )

    def __init__(self, name, iioname):
        self.name = name
        self.circuit = parse_name(name)
        self.iioname = iioname
        self.ports = []
        self.scale = [1.0,1.0]

    #def check(self):
    #    pass
        #self.channel.register_start_callback(self.start_event)


    def register_port(self, port):
        self.ports.append(port)


    def prepare_device(self):
        context = iio.LocalContext()
        device = context.find_device(self.iioname)
        return device


    async def set_sample_frequency(self, freq):
        def doit(device, value, scale):
            device.channels[0].attrs['sampling_frequency'].value = str(value)
            device.channels[1].attrs['sampling_frequency'].value = str(value)
            scale[0] = float(device.channels[0].attrs['scale'].value)
            scale[1] = float(device.channels[1].attrs['scale'].value)

        await asyncio.to_thread(doit, self.device, freq, self.scale)


    async def run(self):
        logging.debug(f"Starting ADC loop for {self.name}")
        try:
            self.device = await asyncio.to_thread(self.prepare_device)
            await self.set_sample_frequency(3)
        except Exception as E:
            logging.error(f"IIOchip connect error: {str(E)}")
            #import traceback
            #traceback.print_exc(file=sys.stdout)
            raise

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

        def getit(device, port):
            return float(device.channels[port].attrs['raw'].value)

        await asyncio.sleep(0.5)
        return await asyncio.to_thread(getit, self.device, port) * self.scale[port]


Foptions = {
    'iioname': {'type': str, 'help': 'IIO name of chip', 'default' : '1-0068' },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return Mcp342x(devname, **kwargs)

