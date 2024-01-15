![unipi logo](https://github.com/UniPiTechnology/evok/raw/master/www/evok/js/jquery/images/unipi-logo-short-cmyk.svg?sanitize=true "UniPi logo")
# unipi-one - Modbus TCP server for Unipi 1.x and Unipi Lite devices
Allows control of individual inputs and outputs on Unipi 1x devices using the Modbus TCP protocol.

### Debian package installation
    sudo su
    echo "deb https://repo.unipi.technology/debian bookworm unipi1-main main" > /etc/apt/sources.list.d/unipi.list
    wget https://repo.unipi.technology/debian/unipi_pub.gpg -O /etc/apt/trusted.gpg.d/unipi_pub.asc
    apt update
    apt install unipi-os-configurator unipi-os-configurator-data
    apt install unipi-one
This installation will install all necessary programs and attempt to automatically configure unipi-one
Configuration is in the directory /etc/unipi-one.d
The Unipi 1x platform does not support automatic configuration of connected modules. When using the EMO-R8 extension,
it is necessary to specify this module in the /etc/unipi-id directory.
The procedure is specified in the '/etc/unipi-id/README.md' file from package 'unipi-os-configurator'.
The default Modbus server runs at the address 127.0.0.1 and port 503. It can be changed in the configuration file.

##  Installation without unipi-os-configurator support and without packages
Requires python3, libiio0 or pigpiod
```bash
pip3 install -r ./requirements.txt
```
Configuration needs to be created according to the template.
It supports configuration via a directory (merges all .yaml files in the directory in alphabetical order)
or the configuration is in one file (/etc/unipi-one.yaml).
The hardware can be communicated either via a kernel module (recommended) or via the pigpiod daemon,
which needs to be installed and started. See examples in the configs directory.
For the kernel module option, overlays need to be added to /boot/config.txt.

```
dtoverlay=pwm,pin=18,2
dtoverlay=mcp342x,mcp3422,addr=0x68
dtoverlay=mcp23017,mcp23008,addr=0x20,noints
```
Alternatively, when using EMO-R8
```
dtoverlay=mcp23017,mcp23008,addr=0x21,noints
dtoverlay=mcp23017,mcp23008,addr=0x22,noints
```


### Removing Debian package installation
    sudo su
    apt-get remove unipi-one
    reboot

## Developer Note
Do you feel like contributing to unipi-one, or perhaps have a neat idea for an improvement to our system? Great!
We are open to all ideas.
Get in touch with us via email to info at unipi DOT technology.

## License
Apache License, Version 2.0

----
Raspberry Pi is a trademark of the Raspberry Pi Foundation
- [api-docs.io](https://evok-14.api-docs.io/1.11/)
- [github repository](https://github.com/UniPiTechnology/unipi-one)
- [OpenSource image](https://files.unipi.technology/s/public?path=%2FSoftware%2FOpen-Source%20Images)
- [IndieGogo](https://www.indiegogo.com/projects/unipi-the-universal-raspberry-pi-add-on-board)
- [NEURON](https://www.unipi.technology/products/unipi-neuron-3?categoryId=2)
- [UniPi 1.1](https://www.unipi.technology/products/unipi-1-1-1-1-lite-19?categoryId=1)
- [Axon](https://www.unipi.technology/products/unipi-axon-135?categoryId=13)
- [PIGPIO](http://abyz.co.uk/rpi/pigpio/)
- [our forum](http://forum.unipi.technology/)
- [instructions below](https://github.com/UniPiTechnology/evok#installing-evok-for-neuron)
