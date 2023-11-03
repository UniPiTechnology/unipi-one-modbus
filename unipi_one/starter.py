#!/usr/bin/python3
import os
import sys
import signal
import asyncio
import yaml
import logging
import logging.handlers
import importlib
from queue import Queue

from .rpcmethods import *

default_log_level = logging.INFO
default_config = "/etc/unipi-one.yaml"
break_on_errors = False

############################## YAML Configuration ###################################
def LoadYamlConfig(path):
    with open(path, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as E:
            logging.critical("Yaml error: %s", str(E))
            raise SystemExit() 


def LoadList(nodelist, parent):
    for node in nodelist:
        if type(node) is dict:
            LoadNode(node, parent)
        else:
            logging.critical("Bad config - has to be dictionary: %s", str(node))
            #return


def LoadNode(node, parent):

    # parse type attribute and Node name
    name = node.get("name", None)
    if name and name.startswith('_'): 
        return  # skip disabled items
    unittype = node.get("type", '')

    (prefix,devicetype) = unittype.split('.',1) if '.' in unittype else ('',unittype)
    try:
        module = importlib.import_module(f".{devicetype}",f"{ __package__}.{prefix}")
    except ImportError:
        logging.critical("Config node '%s': Unknown device type=%s", name, unittype)
        if break_on_errors: raise
        return

    obj = None
    if hasattr(module,'YFactory'):
        try:
            obj = module.YFactory(node, name, parent)
        except (AttributeError, KeyError) as E:
            logging.critical("Config node '%s': Missing required parameter %s",name or unittype, str(E))
            if break_on_errors: raise
        except Exception:
            logging.critical("Config node' %s': %s %s", name or unittype, sys.exc_info()[0],sys.exc_info()[1])
            if break_on_errors: raise

    childs = node.get('childs', None)
    if childs: LoadList(childs, obj)


############################## Queue Logging ###################################
def setup_logging_queue() -> None:
    """Move log handlers to a separate thread.

    Replace handlers on the root logger with a LocalQueueHandler,
    and start a logging.QueueListener holding the original
    handlers.

    """
    queue = Queue()

    handlers: List[logging.Handler] = []

    handler = logging.handlers.QueueHandler(queue)
    logging.getLogger().addHandler(handler)
    logger = logging.getLogger() 
    for h in logger.handlers[:]:
        if h is not handler:
            logger.removeHandler(h)
            handlers.append(h)

    listener = logging.handlers.QueueListener(
        queue, *handlers, respect_handler_level=True
    )
    listener.start()


def setup(args):

    #setup logging
    logger = logging.getLogger()
    logger.setLevel(default_log_level)
    if args.debug: logger.setLevel(logging.DEBUG)

    if args.syslog:
        # add syslog logger in decorated format
        #fh = logging.FileHandler('/var/log/'+Globals.APP_NAME+'.log')
        fh = logging.handlers.SysLogHandler(address='/dev/log',	facility='local0')
        fh.setLevel(default_log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s %(levelname)s: %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        # add console logger in simple message format
        fh = logging.StreamHandler(sys.stdout)
        fh.setLevel(logging.DEBUG if args.debug else logging.INFO)
        formatter = logging.Formatter('%(created)f %(levelname)-8s: %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)


    global break_on_errors
    break_on_errors = args.break_on_error;

    #read config from path specified on command line or from /etc or from program directory
    if args.config:
        path = args.config
    else:
        path = default_config
        if not os.path.isfile(path):
            path = os.path.dirname(os.path.realpath(__file__)) +'/'+\
                   os.path.basename(default_config)

    if not os.path.isfile(path):
        raise Exception('Missing config file %s', path)

    logging.info("Loading config file: %s", path)

    nodelist = LoadYamlConfig(path)
    LoadList(nodelist, None)

    # start Queue logging - to be asyncio compatible
    setup_logging_queue()


async def run():

    # check all units - complete bindings between objects, add start/stop callbacks
    for unit in Units:
        try:
            if hasattr(unit, 'check'): unit.check()
        except:
            logging.critical("Check unit '%s': %s %s", unit.name, sys.exc_info()[0],sys.exc_info()[1])
            if break_on_errors: raise

    tasks = list()
    stop_callback = list()

    # prepare graceful stop on signals
    def sig_handler(sig, frame):
        if sig in (signal.SIGTERM, signal.SIGINT):
            while tasks:
                tasks.pop().cancel()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    # start all units
    try:
        async with asyncio.TaskGroup() as tg:
            for unit in Units:
                if hasattr(unit, 'run'):
                    task = tg.create_task(unit.run())
                    if hasattr(unit, 'stop'): stop_callback.append(unit.stop)
                    tasks.append(task)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    except Exception:
        logging.critical("Running: %s %s", sys.exc_info()[0],sys.exc_info()[1])

    logging.info("*** shutdown ***")
    try:
        coros = filter(lambda cor: asyncio.iscoroutine(cor),
                (callback() for callback in stop_callback))
        await asyncio.gather(*coros)
    except:
        logging.critical("Finishing: %s %s", sys.exc_info()[0],sys.exc_info()[1])


def main():
    import argparse
    a = argparse.ArgumentParser(prog='homevok.py')
    a.add_argument('-l','--syslog',action='store_true', help='use syslog for logging')
    a.add_argument('-d','--debug',action='store_true', help='debug logging on stdout')
    a.add_argument('-b','--break',action='store_true', help='break program on exception (during config)', dest='break_on_error')
    a.add_argument('-c','--config',help='use this config file (default: homevok.conf from /etc or program directory)',
                                   metavar="file")
    args = a.parse_args()
    try:
        setup(args)
        asyncio.run(run(), debug=args.debug)

    except Exception as E:
        logging.critical("Error %s %s", sys.exc_info()[0],sys.exc_info()[1])
        if args.debug:
            import traceback
            traceback.print_exc(file=sys.stdout)

    os._exit(1)
    os.kill(0,1)
