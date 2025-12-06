# OpenDTU to ModBus TCP (Fronius Smart Meter 63A-3)

Thanks to all who worked hard to reverse engeniere the protocol!

My script is based on:

https://github.com/tichachm/fronius_smart_meter_modbus_tcp_emulator/blob/main/froniussimulator_3_noCheckMK.py

Wich is based on:

https://www.photovoltaikforum.com/thread/185108-fronius-smart-meter-tcp-protokoll


# Installation

## Operating System

### Debian/Ubuntu
    apt install python3

### Alphine
    apk add python3

## Python

### venv (Recommended)
    mkdir ~/o2mb
    python3 -m venv ~/o2mb
    source ~/o2mb/bin/activate

### Required libs
    pip install -r requirements.txt

Or install manually

    pip install paho-mqtt pymodbus

### Run as root
Need to run as root because Port 502 is required

Example how to start the script into a screen session with crontab

    @reboot screen -dmS MyScreen ~/o2mb/bin/python ~/o2mb/DTU2MB.py
