#!/bin/sh

[ -d /etc/unipi-one.d ] || exit 0

if [ "$UNIPI_PLATFORM" = "0101" ]; then
    rm -f /etc/unipi-one.d/5*.yaml
    ln -s /usr/share/unipi-one/5-unipi-11.yaml /etc/unipi-one.d
    rm -f /etc/unipi-one.d/0-autocal.yaml
    ln -s /usr/share/unipi-one/0-autocal.yaml /etc/unipi-one.d

elif [ "$UNIPI_PLATFORM" = "1101" ]; then
    rm -f /etc/unipi-one.d/5*.yaml
    ln -s /usr/share/unipi-one/5-unipi-lite.yaml /etc/unipi-one.d
    rm -f /etc/unipi-one.d/0-autocal.yaml

elif [ "$UNIPI_PLATFORM" = "0100" ]; then
    rm -f /etc/unipi-one.d/5*.yaml
    ln -s /usr/share/unipi-one/5-unipi-10.yaml /etc/unipi-one.d
    rm -f /etc/unipi-one.d/0-autocal.yaml
    ln -s /usr/share/unipi-one/0-autocal.yaml /etc/unipi-one.d
fi

if [ -n "$HAS_EMO8_21" ]; then
    ln -s /usr/share/unipi-one/6-emo8_21.yaml /etc/unipi-one.d || true
fi
if [ -n "$HAS_EMO8_22" ]; then
    ln -s /usr/share/unipi-one/6-emo8_22.yaml /etc/unipi-one.d || true
fi
if [ -n "$HAS_EMO8_23" ]; then
    ln -s /usr/share/unipi-one/6-emo8_23.yaml /etc/unipi-one.d || true
fi
