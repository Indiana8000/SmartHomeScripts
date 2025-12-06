#!/usr/bin/env python



# ███╗   ███╗ ██████╗ ████████╗████████╗     ██████╗██╗     ██╗███╗   ██╗███████╗████████╗
# ████╗ ████║██╔═══██╗╚══██╔══╝╚══██╔══╝    ██╔════╝██║     ██║████╗  ██║██╔════╝╚══██╔══╝
# ██╔████╔██║██║   ██║   ██║      ██║       ██║     ██║     ██║██╔██╗ ██║█████╗     ██║   
# ██║╚██╔╝██║██║▄▄ ██║   ██║      ██║       ██║     ██║     ██║██║╚██╗██║██╔══╝     ██║   
# ██║ ╚═╝ ██║╚██████╔╝   ██║      ██║       ╚██████╗███████╗██║██║ ╚████║███████╗   ██║   
# ╚═╝     ╚═╝ ╚══▀▀═╝    ╚═╝      ╚═╝        ╚═════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   
#                                                                                         
import paho.mqtt.client as mqtt

# Connection Settings
MQTT_TOPIC_PREFIX     = "openDTU"
MQTT_CONNECT_HOST     = "192.168.5.7"
MQTT_CONNECT_PORT     = 1883

# Optional Username and Password
MQTT_CONNECT_USERNAME = ""
MQTT_CONNECT_PASSWORD = ""

# Define default phase
MQTT_DEFAULT_PHASE    = "l1"

# Set phase per inverter (by Serial Number)
mqtt_data = {}
#mqtt_data['1234'] = {'phase': 'l3'}
#mqtt_data['5678'] = {'phase': 'l1'}
#mqtt_data['9090'] = {'phase': 'l2'}



# Subscribe to OpenDTU Topic
def mqtt_on_connect(client, userdata, flags, reason_code, properties):
    print(f"MQTT connected: {reason_code}")
    client.subscribe(MQTT_TOPIC_PREFIX + "/+/0/+")

# Store messages in global variable
def mqtt_on_message(client, userdata, msg):
    global mqtt_data
    topic = msg.topic.split('/')
    if topic[0] == MQTT_TOPIC_PREFIX:
        if topic[1] not in mqtt_data:
            mqtt_data[topic[1]] = {'phase': MQTT_DEFAULT_PHASE}
        mqtt_data[topic[1]][topic[3]] = float(msg.payload)

# Init global values
def mqtt_init():
    global mqtt_data
    for i in mqtt_data:
        mqtt_data[i]['power'] = 0
        mqtt_data[i]['frequency'] = 0
        mqtt_data[i]['reactivepower'] = 0
        mqtt_data[i]['powerfactor'] = 0
        mqtt_data[i]['voltage'] = 0
        mqtt_data[i]['current'] = 0
        mqtt_data[i]['yieldtotal'] = 0

# Init and connect to MQTT
def mqtt_start():
    print("Starting MQTT")
    mqtt_init()
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_CONNECT_USERNAME != "":
        mqttc.username_pw_set(MQTT_CONNECT_USERNAME, MQTT_CONNECT_PASSWORD)
    mqttc.on_connect = mqtt_on_connect
    mqttc.on_message = mqtt_on_message
    mqttc.connect(MQTT_CONNECT_HOST, MQTT_CONNECT_PORT, 60)
    mqttc.loop_start()

# Aggregate all inverter data into Total & Phase
def mqtt_aggregate():
    global mqtt_data
    aggregate = {
        'power': .0,
        'voltage': .0,
        'current': .0,
        'frequency': .0,
        'reactivepower': .0,
        'powerfactor': .0,
        'yieldtotal': .0,
        'l1_count': 0,
        'l1_power': .0,
        'l1_voltage': .0,
        'l1_current': .0,
        'l1_reactivepower': .0,
        'l1_powerfactor': .0,
        'l1_yieldtotal': .0,
        'l2_count': 0,
        'l2_power': .0,
        'l2_voltage': .0,
        'l2_current': .0,
        'l2_reactivepower': .0,
        'l2_powerfactor': .0,
        'l2_yieldtotal': .0,
        'l3_count': 0,
        'l3_power': .0,
        'l3_voltage': .0,
        'l3_current': .0,
        'l3_reactivepower': .0,
        'l3_powerfactor': .0,
        'l3_yieldtotal': .0,
    }
    for i in mqtt_data:
        aggregate['power']         += mqtt_data[i]['power']
        aggregate['voltage']       += mqtt_data[i]['voltage']
        aggregate['current']       += mqtt_data[i]['current']
        aggregate['frequency']     += mqtt_data[i]['frequency']
        aggregate['reactivepower'] += mqtt_data[i]['reactivepower']
        aggregate['powerfactor']   += mqtt_data[i]['powerfactor']
        aggregate['yieldtotal']    += mqtt_data[i]['yieldtotal']
        aggregate[mqtt_data[i]['phase'] + "_count"]         += 1
        aggregate[mqtt_data[i]['phase'] + "_power"]         += mqtt_data[i]['power']
        aggregate[mqtt_data[i]['phase'] + "_voltage"]       += mqtt_data[i]['voltage']
        aggregate[mqtt_data[i]['phase'] + "_current"]       += mqtt_data[i]['current']
        aggregate[mqtt_data[i]['phase'] + "_reactivepower"] += mqtt_data[i]['reactivepower']
        aggregate[mqtt_data[i]['phase'] + "_powerfactor"]   += mqtt_data[i]['powerfactor']
        aggregate[mqtt_data[i]['phase'] + "_yieldtotal"]    += mqtt_data[i]['yieldtotal']
    if len(mqtt_data) > 0:
        aggregate['frequency']     /= len(mqtt_data)
        aggregate['voltage']       /= len(mqtt_data)
        aggregate['powerfactor']   /= len(mqtt_data)
    if aggregate['l1_count'] > 0:
        aggregate['l1_voltage']     /= aggregate['l1_count']
        aggregate['l1_powerfactor'] /= aggregate['l1_count']
    if aggregate['l2_count'] > 0:
        aggregate['l2_voltage']     /= aggregate['l2_count']
        aggregate['l2_powerfactor'] /= aggregate['l2_count']
    if aggregate['l3_count'] > 0:
        aggregate['l3_voltage']     /= aggregate['l3_count']
        aggregate['l3_powerfactor'] /= aggregate['l3_count']
    aggregate['power']      = round(aggregate['power'], 3)
    aggregate['voltage']    = round(aggregate['voltage'], 3)
    aggregate['current']    = round(aggregate['current'], 3)
    aggregate['frequency']  = round(aggregate['frequency'], 3)
    aggregate['l1_current'] = round(aggregate['l1_current'], 3)
    aggregate['l1_power']   = round(aggregate['l1_power'], 3)
    aggregate['l2_current'] = round(aggregate['l2_current'], 3)
    aggregate['l2_power']   = round(aggregate['l2_power'], 3)
    aggregate['l3_current'] = round(aggregate['l3_current'], 3)
    aggregate['l3_power']   = round(aggregate['l3_power'], 3)
    return aggregate



# ███╗   ███╗ ██████╗ ██████╗ ██████╗ ██╗   ██╗███████╗    ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ 
# ████╗ ████║██╔═══██╗██╔══██╗██╔══██╗██║   ██║██╔════╝    ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
# ██╔████╔██║██║   ██║██║  ██║██████╔╝██║   ██║███████╗    ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝
# ██║╚██╔╝██║██║   ██║██║  ██║██╔══██╗██║   ██║╚════██║    ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗
# ██║ ╚═╝ ██║╚██████╔╝██████╔╝██████╔╝╚██████╔╝███████║    ███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║
# ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝
#                                                                                                           
import asyncio
import struct

from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusServerContext,
    ModbusSparseDataBlock,
)

# Connection Settings
MODBUS_CONNECT_PORT = 502



# Hock into getValues to calculate datablock
class MyDeviceContext(ModbusDeviceContext):
    def getValues(self, fx, address, count=1):
        # print(f"{fx} :: {address} :: {count}")
        if address >= 40071 and address < 40189:
            mb_update(self.store['h'])
        return super().getValues(fx, address, count)

# Init datablock as Fronius Smart Meter 63A-3
def mb_createDatablock():
    datablock = ModbusSparseDataBlock({
        40001:  [21365, 28243],
        40003:  [1],
        40004:  [65],
        40005:  [70,114,111,110,105,117,115,0,0,0,0,0,0,0,0,0,         #Manufacturer "Fronius
                83,109,97,114,116,32,77,101,116,101,114,32,54,51,65,0, #Device Model "Smart Meter
                0,0,0,0,0,0,0,0,                                       #Options N/A
                0,0,0,0,0,0,0,0,                                       #Software Version  N/A
                48,48,48,48,48,48,48,50,0,0,0,0,0,0,0,0,               #Serial Number: 00000 (should be different if there are more Smart Meters)
                240],                                                  #Modbus TCP Address:
        40070: [213],
        40071: [124],
        40072: [0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0,0,0,
                0,0,0,0],
        40196: [65535, 0],
    })
    return datablock

# Init Modbus server
def mb_createContext(datablock):
    slaveStore = MyDeviceContext(
            di=datablock,
            co=datablock,
            hr=datablock,
            ir=datablock,
        )
    context = ModbusServerContext(devices=slaveStore, single=True)
    return context

# Start async Modbus server
async def mb_start():
    print("Starting MODBUS")
    context = mb_createContext(mb_createDatablock())
    await StartAsyncTcpServer(
        context=context,
        address=("", MODBUS_CONNECT_PORT),
    )

# Convert Float into 16-bit hex register
def calculate_register(value_float):
    if value_float == 0:
        int1 = 0
        int2 = 0
    else:
        value_hex = hex(struct.unpack('<I', struct.pack('<f', value_float))[0])
        value_hex_part1 = str(value_hex)[2:6] #extract first register part (hex)
        value_hex_part2 = str(value_hex)[6:10] #extract seconds register part (hex)
        int1 = int(value_hex_part1, 16) #convert hex to integer because pymodbus converts back to hex itself
        int2 = int(value_hex_part2, 16) #convert hex to integer because pymodbus converts back to hex itself
    return [int1, int2]

# Update Modbus register with MQTT data
def mb_update(context):
    mqtt = mqtt_aggregate()
    values = []
    values = values + calculate_register(mqtt['current'])
    values = values + calculate_register(mqtt['l1_current'])
    values = values + calculate_register(mqtt['l2_current'])
    values = values + calculate_register(mqtt['l3_current'])
    values = values + calculate_register(mqtt['voltage'])
    values = values + calculate_register(mqtt['l1_voltage'])
    values = values + calculate_register(mqtt['l2_voltage'])
    values = values + calculate_register(mqtt['l3_voltage'])
    values = values + [0, 0, 0, 0, 0, 0, 0, 0] #Voltage - Phase to Phase [V]
    values = values + calculate_register(mqtt['frequency'])
    values = values + calculate_register(mqtt['power']    * -1.0)
    values = values + calculate_register(mqtt['l1_power'] * -1.0)
    values = values + calculate_register(mqtt['l2_power'] * -1.0)
    values = values + calculate_register(mqtt['l3_power'] * -1.0)
    values = values + [0, 0, 0, 0, 0, 0, 0, 0] #AC Apparent Power [VA]
    values = values + calculate_register(mqtt['reactivepower'])
    values = values + calculate_register(mqtt['l1_reactivepower'])
    values = values + calculate_register(mqtt['l2_reactivepower'])
    values = values + calculate_register(mqtt['l3_reactivepower'])
    values = values + calculate_register(mqtt['powerfactor'])
    values = values + calculate_register(mqtt['l1_powerfactor'])
    values = values + calculate_register(mqtt['l2_powerfactor'])
    values = values + calculate_register(mqtt['l3_powerfactor'])
    values = values + calculate_register(mqtt['yieldtotal'])
    values = values + calculate_register(mqtt['l1_yieldtotal'])
    values = values + calculate_register(mqtt['l2_yieldtotal'])
    values = values + calculate_register(mqtt['l3_yieldtotal'])
    context.setValues(40072, values)



# ███╗   ███╗ █████╗ ██╗███╗   ██╗
# ████╗ ████║██╔══██╗██║████╗  ██║
# ██╔████╔██║███████║██║██╔██╗ ██║
# ██║╚██╔╝██║██╔══██║██║██║╚██╗██║
# ██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
# ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
#                                 
if __name__ == '__main__':
    print("Starting MAIN")
    mqtt_start()
    asyncio.run(mb_start())