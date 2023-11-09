#!/usr/bin/python
import os
import struct
from pigpio import u2i, _u2i
import pigpio
import asyncio
import socket
import logging

from ..rpcmethods import DevMeta, get_kwargs, check_dev_type
from .bus import PigBus

pipe_name_n = '/dev/pigpio%d'

class NotifyPipeProtocol(asyncio.BaseProtocol):

    def __init__(self, mask, callbacks, bank):
        self.bank1 = bank
        self.notify_mask = mask #0xffffffff
        self.notify_callbacks = callbacks #[]

    def connection_made(self, transport):
        if not (self.bank1 is None):
            try:
                coros = filter(lambda cor: asyncio.iscoroutine(cor),
                        (cb(self.bank1 & mask, 0, 0)
                         for mask, cb in self.notify_callbacks.items()))
                [ asyncio.create_task(coro) for coro in coros ]
            except Exception as E:
                logging.error(f"Pigpio notify connect callback error: {str(E)}")

    def connection_lost(self, exc):
        logging.debug(f"Pigpio notify connection closed")

    def data_received(self, data):
        ''' callback from loop 
            reading data in 12 bytes chunks
        '''
        logging.debug(f"Pigpio notify data received {len(data)} {repr(data)}")
        position = 0
        length = len(data)
        while position+12 <= length:
            seq, flag, tick, level = struct.unpack('HHII', data[position:position+12])
            position += 12
            if flag & 0x20:
                # watchdog on pin
                pin = flag & 0x1f
                continue

            if self.bank1 is None: 
                changes = self.notify_mask
            else:
                level &= self.notify_mask
                changes = level ^ self.bank1
            self.bank1 = level
            try:
                coros = filter(lambda cor: asyncio.iscoroutine(cor),
                        (cb(level & mask, tick, seq) for mask, cb in self.notify_callbacks.items() if changes & mask))
                [ asyncio.create_task(coro) for coro in coros ]

            except Exception as E:
                logging.debug(f"Notify data error: {E}")


class GpioChip(metaclass=DevMeta):

    def __init__(self, name, channel):

        self.name = name
        self.channel = channel
        self.notify_pipe = None
        self.notify_callbacks = {}
        self.notify_mask = 0


    def register_callback(self, mask, callback):
        self.notify_callbacks[mask] = callback
        self.notify_mask |= mask


    def check(self):
        device = check_dev_type(self.channel, PigBus, 'Chip %s'%self.name, 'channel')
        self.channel = device
        self.channel.register_start_callback(self._start)
        self.channel.register_stop_callback(self._stop)


    async def _start(self):

        await self.multiset_pull_up_down(self.notify_mask, pigpio.PUD_UP)

        self.notify_handle = await self.channel.notify_open()
        self.notify_pipe = open(pipe_name_n % self.notify_handle, mode='rb')
        loop = asyncio.get_running_loop()

        # load startup values, send it to notifikator
        bank1 = await self.channel.read_bank_1()
        #_, self.notify_protocol = 
        await loop.connect_read_pipe(lambda: NotifyPipeProtocol(self.notify_mask, self.notify_callbacks, bank1),
                                     self.notify_pipe)
        await self.channel.notify_begin(self.notify_handle, self.notify_mask)


    async def _stop(self):
        """Release pigpio resources.
        """
        logging.debug("Close gpiochip notify")
        if not (self.notify_pipe is  None):
            try:
                self.notify_pipe.close()
            except Exception as E:
                pass
            try:
                await self.channel.notify_close(self.notify_handle)
            except Exception as E:
                pass

    async def multiset_pull_up_down(self, mask, mode):
        return [ await self.channel.set_pull_up_down(i, mode) for i in range(32) if mask & (1 << i) ]


Foptions = {
    'channel': {'type': 'node', 'help': 'Link to Pigpio bus' },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node, parent)
    return GpioChip(devname, **kwargs)
