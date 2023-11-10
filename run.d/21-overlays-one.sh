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
if [ -n "$HAS_EMOR8_21" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x21,noints"
fi
if [ -n "$HAS_EMOR8_22" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x22,noints"
fi
if [ -n "$HAS_EMOR8_23" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x23,noints"
fi
if [ -n "$HAS_EMOR8_24" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x24,noints"
fi
if [ -n "$HAS_EMOR8_25" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x25,noints"
fi
if [ -n "$HAS_EMOR8_26" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x26,noints"
fi
if [ -n "$HAS_EMOR8_27" ]; then
    echo "dtoverlay=mcp23017,mcp23008,addr=0x27,noints"
fi

} >>"${CONFIG_INC}"
