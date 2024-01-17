#!/bin/sh

[ -d /etc/unipi-one-modbus.d ] || exit 0

if [ "$UNIPI_PLATFORM" = "0101" ]; then
    rm -f /etc/unipi-one-modbus.d/5*.yaml
    rm -f /etc/unipi-one-modbus.d/6*.yaml
    ln -s /usr/share/unipi-one-modbus/5-unipi-11.yaml /etc/unipi-one-modbus.d
    rm -f /etc/unipi-one-modbus.d/0-autocal.yaml
    ln -s /usr/share/unipi-one-modbus/0-autocal.yaml /etc/unipi-one-modbus.d

elif [ "$UNIPI_PLATFORM" = "1101" ]; then
    rm -f /etc/unipi-one-modbus.d/5*.yaml
    rm -f /etc/unipi-one-modbus.d/6*.yaml
    ln -s /usr/share/unipi-one-modbus/5-unipi-lite.yaml /etc/unipi-one-modbus.d
    rm -f /etc/unipi-one-modbus.d/0-autocal.yaml

elif [ "$UNIPI_PLATFORM" = "0100" ]; then
    rm -f /etc/unipi-one-modbus.d/5*.yaml
    rm -f /etc/unipi-one-modbus.d/6*.yaml
    ln -s /usr/share/unipi-one-modbus/5-unipi-10.yaml /etc/unipi-one-modbus.d
    rm -f /etc/unipi-one-modbus.d/0-autocal.yaml
    ln -s /usr/share/unipi-one-modbus/0-autocal.yaml /etc/unipi-one-modbus.d
fi

if [ -n "$HAS_EMOR8_1" ]; then
    ln -s /usr/share/unipi-one-modbus/6-emo-r8_1.yaml /etc/unipi-one-modbus.d || true
fi
if [ -n "$HAS_EMOR8_2" ]; then
    ln -s /usr/share/unipi-one-modbus/6-emo-r8_2.yaml /etc/unipi-one-modbus.d || true
fi
if [ -n "$HAS_EMOR8_3" ]; then
    ln -s /usr/share/unipi-one-modbus/6-emo-r8_3.yaml /etc/unipi-one-modbus.d || true
fi
if [ -n "$HAS_EMOR8_4" ]; then
    ln -s /usr/share/unipi-one-modbus/6-emo-r8_4.yaml /etc/unipi-one-modbus.d || true
fi
if [ -n "$HAS_EMOR8_5" ]; then
    ln -s /usr/share/unipi-one-modbus/6-emo-r8_5.yaml /etc/unipi-one-modbus.d || true
fi
if [ -n "$HAS_EMOR8_6" ]; then
    ln -s /usr/share/unipi-one-modbus/6-emo-r8_6.yaml /etc/unipi-one-modbus.d || true
fi
if [ -n "$HAS_EMOR8_7" ]; then
    ln -s /usr/share/unipi-one-modbus/6-emo-r8_7.yaml /etc/unipi-one-modbus.d || true
fi
