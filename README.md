![unipi logo](https://github.com/UniPiTechnology/evok/raw/master/www/evok/js/jquery/images/unipi-logo-short-cmyk.svg?sanitize=true "UniPi logo")

# unipi-one - Modbus TCP server for Unipi 1.x and Unipi Lite devices

Umoznuje ovladani jednotlivych vstupu a vystupu na Unipi 1x zarizenich pomoci protokolu Modbus TCP.


### Debian package installation

    # add /etc/apt/source....
    apt install unipi-os-configurator unipi-os-configurator-data
    apt install unipi-one

Tato instalace nainstaluje vsechny potrebne programy a pokusi se automaticky zkonfigurovat unipi-one
Konfigurace je v adresari /etc/unipi-one.d

Platforma Unipi 1x nepodporuje automatickou konfiguraci pripojenych modulu. Pokud pouzivate extension EMO-R8,
je potreba uvest tento modul do adresare /etc/unipi-id. Postup je uveden v souboru /etc/unipi-id/README.md

Modbus server implicitne bezi na adrese 127.0.0.1 a portu 503. Lze zmenit v konfiguracnim souboru.


##  Instalace bez podpory unipi-os-configuratoru a bez baliku

Vyzaduje python3, libiio0 nebo pigpiod

    pip3 install ....

Konfiguraci je potreba vytvorit podle vzoru.

Je podporovana konfigurace pomoci adresare (slouci se vsechny .yaml soubory v adresari podle abecedniho poradi)
nebo je konfigurace v jednom souboru (/etc/unipi-one/yaml)

S hardware lze komunikovat bud prostrednictvim kernel modulu (doporuceno) nebo prostrednictvim demona pigpiod,
ktery je nutno si nainstalovat a spustit. Viz priklady v adresari configs

Pro variantu kernel moduly je potreba doplnit overlays do /boot/config.txt

    dtoverlay=pwm,pin=18,2
    dtoverlay=mcp342x,mcp3422,addr=0x68
    dtoverlay=mcp23017,mcp23008,addr=0x20,noints

Pripadne pokud pozivate EMO-R8

    dtoverlay=mcp23017,mcp23008,addr=0x21,noints
    dtoverlay=mcp23017,mcp23008,addr=0x22,noints




### Debian package installation

    sudo su
    apt-get remove unipi-one
    reboot

### Script installation

## Developer Note

Do you feel like contributing to unipi-one, or perhaps have a neat idea for an improvement to our system? Great! We are open to all ideas. Get in touch with us via email to info at unipi DOT technology

License
============
Apache License, Version 2.0

----
Raspberry Pi is a trademark of the Raspberry Pi Foundation
[api-docs.io]:https://evok-14.api-docs.io/1.11/
[github repository]:https://github.com/UniPiTechnology/unipi-one
[OpenSource image]:https://files.unipi.technology/s/public?path=%2FSoftware%2FOpen-Source%20Images
[IndieGogo]:https://www.indiegogo.com/projects/unipi-the-universal-raspberry-pi-add-on-board
[NEURON]:https://www.unipi.technology/products/unipi-neuron-3?categoryId=2
[UniPi 1.1]:https://www.unipi.technology/products/unipi-1-1-1-1-lite-19?categoryId=1
[Axon]:https://www.unipi.technology/products/unipi-axon-135?categoryId=13
[PIGPIO]:http://abyz.co.uk/rpi/pigpio/
[our forum]:http://forum.unipi.technology/
[intructions below]:https://github.com/UniPiTechnology/evok#installing-evok-for-neuron
