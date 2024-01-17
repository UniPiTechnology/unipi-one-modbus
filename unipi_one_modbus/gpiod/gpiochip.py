import os
import sys
#import struct
import asyncio
#import socket
import logging

import gpiod
#import select

from gpiod.line import Bias, Edge, Value, Direction

from ..rpcmethods import DevMeta, get_kwargs, check_dev_type

class GpioChip(metaclass=DevMeta):

    def __init__(self, name, chip_path):

        self.name = name
        self.chip_path = chip_path
        self.request = None
        self.pins = set()
        self.notify_callbacks = list()


    def register_callback(self, pins, callback):
        self.pins |= set(pins)
        self.notify_callbacks.append(callback)

    #def check(self):
    #    pass
        #device = check_dev_type(self.channel, PigBus, 'Chip %s'%self.name, 'channel')
        #self.channel = device
        #self.channel.register_start_callback(self._start)
        #self.channel.register_stop_callback(self._stop)

    def _read_ready(self):
        ''' callback from loop 
        '''
        logging.debug(f"Notify data received")
        for event in self.request.read_edge_events():
            if event.event_type is event.Type.RISING_EDGE:
                level = 1
            elif event.event_type is event.Type.FALLING_EDGE:
                level = 0
            else:
                continue
            try:
                fun = self.notify_callbacks.get(event.line_offset, None)
                if fun:
                    coro = fun(level, event.line_offset, event.timestamp_ns)
                    if asyncio.iscoroutine(coro):
                        asyncio.create_task(coro)
                logging.debug(f"gpio.event: {event.line_offset}  type: {level}")
            except Exception as E:
                logging.error(f"Notify data error: {E}")


    async def sendbits(self, values):
        if not self.request:
            raise Exception(f"Gpiochip {self.chip_path} not opened")
        self.values.update(values)
        linedata = dict(((pin, Value.ACTIVE if value else Value.INACTIVE) for pin,value in self.values.items()))
        try:
            await asyncio.to_thread(self.request.set_values,linedata)
        except Exception as E:
            logging.error(f"Gpiochip {self.chip_path} set data error: {E}")
        else:
            try:
                coros = filter(lambda cor: asyncio.iscoroutine(cor),
                               (cb(self.values) for cb in self.notify_callbacks))
                [ asyncio.create_task(coro) for coro in coros ]
            except Exception as E:
                logging.error(f"Gpiochip connect callback error: {str(E)}")


    async def run(self):
        try:
            config = dict(((pin, gpiod.LineSettings(direction=Direction.OUTPUT)
                           ) for pin in self.pins))
            logging.debug(f"Open gpio chip {self.chip_path}")
            self.request = gpiod.request_lines(self.chip_path, consumer="unipi-one-modbus", config=config) #, output_values={0:0,1:0})

            lines = list(self.pins)
            values = await asyncio.to_thread(self.request.get_values, lines)
            self.values = dict(zip(lines, ((1 if value == Value.ACTIVE else 0) for value in values)))
            try:
                coros = filter(lambda cor: asyncio.iscoroutine(cor),
                               (cb(self.values) for cb in self.notify_callbacks))
                [ asyncio.create_task(coro) for coro in coros ]
            except Exception as E:
                logging.error(f"Gpiochip {self.chip_path} connect callback error: {str(E)}")
                #import traceback
                #traceback.print_exc(file=sys.stdout)

        except Exception as E:
            logging.error(f"Gpiochip {self.chip_path} connect error: {str(E)}")
            #logging.critical("Error %s %s", sys.exc_info()[0],sys.exc_info()[1])
            #import traceback
            #traceback.print_exc(file=sys.stdout)


    async def stop(self):
        """Release pigpio resources.
        """
        if self.request:
            logging.debug(f"Close gpiochip {self.chip_path}")
            self.request.release()
            self.request = None


Foptions = {
    #'channel': {'type': 'node', 'help': 'Link to Pigpio bus' },
    'chip_path': {'type': str, 'help': 'Gpiochip device. Default /dev/gpiochip0', 'default':'/dev/gpiochip0' },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return GpioChip(devname, **kwargs)


