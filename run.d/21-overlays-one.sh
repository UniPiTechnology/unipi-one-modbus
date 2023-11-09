#!/bin/sh

[ -f /etc/bootcmd.d/Makefile ] && exit 0

CONFIG_INC=/boot/config_unipi.inc

# append to config file
{
if [ -n "$HAS_PWM" ]; then
    echo "dtoverlay=pwm,pin=18,2"
fi
if [ -n "$HAS_AI" ]; then
    echo "dtoverlay=mcp342x,mcp3422,addr=0x68"
fi
if [ -n "$HAS_RELAYS" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x20,noints"
fi
if [ -n "$HAS_EMO8_21" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x21,noints"
fi
if [ -n "$HAS_EMO8_22" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x22,noints"
fi
if [ -n "$HAS_EMO8_23" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x23,noints"
fi

} >>"${CONFIG_INC}"
