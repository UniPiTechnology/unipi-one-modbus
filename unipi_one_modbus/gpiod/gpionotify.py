#!/usr/bin/python
import os
import sys
#import struct
import asyncio
#import socket
import logging

import gpiod
#import select

from datetime import timedelta
from gpiod.line import Bias, Edge, Value, Direction

from ..rpcmethods import DevMeta, get_kwargs, check_dev_type
#from .bus import PigBus

#pipe_name_n = '/dev/pigpio%d'


class GpioChip(metaclass=DevMeta):

    def __init__(self, name, chip_path):

        self.name = name
        self.chip_path = chip_path
        self.request = None
        self.notify_callbacks = {}
        self.debounces = {}


    def register_callback(self, pin, callback, debounce):
        self.notify_callbacks[pin] = callback
        self.debounces[pin] = debounce


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


    async def stop(self):
        """Release pigpio resources.
        """
        if self.request:
            logging.debug(f"Close gpio notify {self.chip_path}")
            self.request.release()
            self.request = None

    async def set_debounce(self, pin, debounce):
        self.debounces[pin] = debounce
        config = dict(((pin,
                        gpiod.LineSettings(
                            direction=Direction.INPUT,
                            edge_detection=Edge.BOTH,
                            bias=Bias.PULL_UP,
                            debounce_period=timedelta(milliseconds=self.debounces.get(pin,5))
                        )
                    ) for pin in self.notify_callbacks))
        await asyncio.to_thread(self.request.reconfigure_lines, config)


Foptions = {
    #'channel': {'type': 'node', 'help': 'Link to Pigpio bus' },
    'chip_path': {'type': str, 'help': 'Gpiochip device. Default /dev/gpiochip0', 'default':'/dev/gpiochip0' },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return GpioChip(devname, **kwargs)
