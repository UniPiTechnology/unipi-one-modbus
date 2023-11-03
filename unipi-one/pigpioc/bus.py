#!/usr/bin/python
import os
import struct
from pigpio import u2i, _u2i
import pigpio
import asyncio
import socket
import logging
from contextlib import suppress

from ..rpcmethods import DevMeta, get_kwargs


class PigBus(metaclass=DevMeta):

    def __init__(self,  name, host='localhost', port=8888):

        self.name = name
        self._host = host
        self._port = port
        self.start_callbacks = []
        self.stop_callbacks = []
        self.connected = False
        self.iolock = asyncio.Lock()


    def register_start_callback(self,callback):
        self.start_callbacks.append(callback)

    def register_stop_callback(self,callback):
        self.stop_callbacks.append(callback)


    async def run(self):
        #await asyncio.sleep(100)
        try:
            sock = socket.create_connection((self._host, self._port), None)
            # Disable the Nagle algorithm.
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except socket.error:
                self.reader, self.writer = await asyncio.open_connection(self._host, self._port)
            else:
                self.reader, self.writer = await asyncio.open_connection(sock = sock)
        except Exception as E:
            logging.error(f"Pipio open: {E}")
            logging.critical("Unable connect to pigpio. Start pigpiod service and try again!")
            #return
            raise

        #atexit.register(self.stop)
        self.connected = True
        await asyncio.gather(*(x() for x in self.start_callbacks))


    async def stop(self):
        """Release pigpio resources.
        """
        logging.debug("Stopping pigpio bus")
        try:
            await asyncio.gather(*(x() for x in self.stop_callbacks))
        except Exception as E:
            logging.debug(f"Stopping pigpio bus error: {E}")
            pass
        try:
            self.writer.close()
        except Exception as E:
            pass
        self.connected = False


    async def _command(self, cmd, p1, p2):
        """
        Runs a pigpio socket command.
        """
        #print ("command: ", cmd)
        async with self.iolock:
            self.writer.write(struct.pack('IIII', cmd, p1, p2, 0))
            await self.writer.drain()
            result = await self.reader.read(16)
        dummy, res = struct.unpack('12sI', result)
        return res


    async def _command_ext(self, cmd, p1, p2, p3, extents):
        """
        Runs a pigpio socket command ext.
        """
        # ext = bytearray(struct.pack('IIII', cmd, p1, p2, p3))
        ext = struct.pack('IIII', cmd, p1, p2, p3)
        for x in extents:  ext += x

        #print ("commandext: ", cmd)
        async with self.iolock:
            self.writer.write(ext)
            await self.writer.drain()
            result = await self.reader.read(16)
        dummy, res = struct.unpack('12sI', result)
        return res


    async def arxbuf(self, count):
        """Returns count bytes from the command socket."""
        async with self.iolock:
            ext = await self.reader.read(count)
            ext = bytearray(ext)
            while len(ext) < count:
                rbytes = await self.reader.read(count - len(ext))
                ext.extend(rbytes)
        return ext


    async def notify_open(self):
        """
        Returns a notification handle (>=0).
        """
        return _u2i(await self._command(pigpio._PI_CMD_NO, 0, 0))

    async def notify_begin(self, handle, bits):
        """
        Starts notifications on a handle.
        """
        return _u2i(await self._command(pigpio._PI_CMD_NB, handle, bits))

    async def notify_pause(self, handle):
        """
        Pauses notifications on a handle.
        """
        return _u2i(await self._command(pigpio._PI_CMD_NB, handle, 0))

    async def notify_close(self, handle):
        """
        Stops notifications on a handle and releases the handle for reuse.
        """
        return _u2i(await self._command(pigpio._PI_CMD_NC, handle, 0))


    async def read_bank_1(self):
        """
        Returns the levels of the bank 1 GPIO (GPIO 0-31).
        """
        return await self._command(pigpio._PI_CMD_BR1, 0, 0)


    async def set_pull_up_down(self, gpio, pud):
        """
        Sets or clears the internal GPIO pull-up/down resistor.
        """
        return _u2i(await self._command(pigpio._PI_CMD_PUD, gpio, pud))


    async def i2c_open(self, i2c_bus, i2c_address, i2c_flags=0):
        """
        Returns a handle (>=0) for the device at the I2C bus address.
        """
        extents = [struct.pack("I", i2c_flags)]
        return _u2i(await self._command_ext(pigpio._PI_CMD_I2CO, 
                                            i2c_bus, i2c_address, 4, extents))

    async def i2c_close(self, handle):
        """
        Closes the I2C device associated with handle.
        """
        return _u2i(await self._command(pigpio._PI_CMD_I2CC, handle, 0))


    async def i2c_writereg(self, device, register, byte_val):
        #write byte
        extents = [struct.pack("I", byte_val)]
        result = await self._command_ext(pigpio._PI_CMD_I2CWB, 
                                         device, register, 4, extents)
        _u2i(result)  # check errors


    async def i2c_readreg(self, device, register):
        #read byte
        result = await self._command( pigpio._PI_CMD_I2CRB, device, register)
        return _u2i(result)


    async def i2c_readdata(self, device, length):
        #read bytes fron i2c device
        async with self.iolock:
            self.writer.write(struct.pack('IIII', pigpio._PI_CMD_I2CRD, device, length, 0))
            await self.writer.drain()
            result = await self.reader.read(16)
            dummy, res = struct.unpack('12sI', result)
            bytes = _u2i(res)
            if bytes <= 0: return bytes
            """Read bytes from the command socket."""
            ext = await self.reader.read(bytes)
            ext = bytearray(ext)
            while len(ext) < bytes:
                rbytes = await self.reader.read(bytes - len(ext))
                ext.extend(rbytes)
        return ext


    async def i2c_writeshort(self, device, data):
        #writw short
        result = await self._command(pigpio._PI_CMD_I2CWS, device, data)
        _u2i(result)


    async def pwm_setduty(self, pin, value):
        return _u2i(await self._command(pigpio._PI_CMD_PWM, pin, value))

    async def pwm_getduty(self, pin):
        return await self._command(pigpio._PI_CMD_GDC, pin, 0)

    async def pwm_setfreq(self, pin, value):
        return _u2i(await self._command(pigpio._PI_CMD_PFS, pin, value))

    async def pwm_getfreq(self, pin):
        return await self._command(pigpio._PI_CMD_PFG, pin, 0)

    async def pwm_setrange(self, pin, value):
        return _u2i(await self._command(pigpio._PI_CMD_PRS, pin, value))


Foptions = {
    'host':    {'type': str, 'help': 'pigpio daemon host. Default localhost', 'default':'localhost' },
    'port':    {'type': int, 'help': 'pigpio daemon tcp port. Default 8888', 'default':8888 },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node)
    return PigBus(devname, **kwargs)
