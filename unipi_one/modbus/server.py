import asyncio
import logging
from contextlib import suppress

from .. import __version__ as unipi_one_version
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import ModbusTcpServer
#from pymodbus.server import StartAsyncTcpServer

from ..rpcmethods import DevMeta, get_kwargs

#_logger = Globals.logger
#logging.basicConfig()
#_logger = logging.getLogger(__file__)
#_logger.setLevel(logging.INFO)


class ModbusServer(metaclass=DevMeta):

    info_name={
        "VendorName": "Unipi Technology",
        "ProductCode": "Unipi1Tcp",
        "VendorUrl": "https://unipi.technology/",
        "ProductName": "Unipi1 Modbus Server",
        "ModelName": "Unipi 1.1/Unipi Lite",
        "MajorMinorRevision": unipi_one_version,
    }

    def __init__(self,  name, host='localhost', port=503):

        self.name = name
        self._host = host
        self._port = port
        self.start_callbacks = []
        self.stop_callbacks = []
        self.slaves = {}


    def register_slave(self, context, slaveid):
        self.slaves[slaveid] = context

    def add_stop_callback(self, callback):
        self.stop_callbacks.append(callback)

    async def run(self):

        address = (self._host, self._port)
        txt = f"*** start Modbus server, listening on {address}"
        logging.info(txt)

        identity = ModbusDeviceIdentification(info_name=self.info_name)
        context  = ModbusServerContext(slaves=self.slaves, single=False)

        self.server = ModbusTcpServer(context, ModbusSocketFramer, identity, address)
        with suppress(asyncio.exceptions.CancelledError):
            try:
                await self.server.serve_forever()
            except Exception as E:
                logging.error(f"Modbus server: {E}")

        delattr(self, 'server')
        await asyncio.gather(*(x() for x in self.stop_callbacks))


    async def stop(self):
        """Release pigpio resources.
        """
        if hasattr(self, 'server'):
            self.server.shutdown()
        await asyncio.sleep(0.1)



Foptions = {
    'host':    {'type': str, 'help': 'Listening host/address. Default localhost', 'default':'localhost' },
    'port':     {'type': int, 'help': 'Listening tcp port. Default 503',  'default':503 },
#    'rpc_port': {'type': int, 'help': 'Listening tcp port. Default 8080' },
}

def YFactory(Node, devname, parent = None):
    kwargs = get_kwargs(Foptions, Node)
    obj = ModbusServer(devname, **kwargs)
    #from .. import modbus
    #modbus.instance = obj
    return obj


