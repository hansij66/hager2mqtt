"""
  Rename to config.py

  Configure:
  - MQTT client
  - Hager ModBus devices
  - Debug level

"""

import minimalmodbus

# [ LOGLEVELS ]
# DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = "DEBUG"

# NROF parameter reads from power meter per hour (60 equals every minute)
# If rate is too high for numer of devices connected, parser might "collapse"
# No safety checks build in for too high read_rate
# Extreme: with eg more that 200 devices on the modbus, a READ_RATE of 3600 might not work.
READ_RATE = 360  # 360 = every 10sec

# [ MQTT Parameters ]
# Using local dns names was not always reliable with PAHO
MQTT_BROKER = "192.168.1.1"
MQTT_PORT = 1883
MQTT_CLIENT_UNIQ = 'mqtt-hager'
MQTT_QOS = 1
MQTT_USERNAME = "username"
MQTT_PASSWORD = "password"

# Max nrof MQTT messages per second
# Set to 0 for unlimited rate
MQTT_RATE = 100

MQTT_TOPIC_PREFIX = "hager"

# Depends on your Hager power meter
MODBUS_RS485_DEVICE = "/dev/tty-rs485"

# Specify the Hager power meters on the RS485 bus
# name: used as MQTT label
# modbus_address: modbus slave address of hager power meter
MODBUS_HAGER_DEVICES = [
{'name': 'wp', 'modbus_address': 1, 'register_map': 'registermap_ecr380D.csv'},
{'name': 'jacuzzi', 'modbus_address': 2, 'register_map': 'registermap_ecr180D.csv'}
]

# Many minimalmodbus defaults are not configurable if they match defaults from Hager
# Assumption is that all devices have same RS485 settings
# Only parity default has to be changed
MODBUS_PARITY=minimalmodbus.serial.PARITY_EVEN

# Minimalmodbus defaults
# baudrate = 19200
# bytesize = 8
# parity   = serial.PARITY_NONE
# stopbits = 1
# timeout  = 0.05          # seconds
# minimalmodbus.MODE_RTU   # rtu or ascii mode
# clear_buffers_before_each_transaction = True

# INFLUXDB
# All power meters are read in a single sequential burst
# Generate same time stamp for all meters read in one sequential burst
# Drawback: if you have multiple (eg 4++ power meters @ 19200 baud), timestamp might deviate a bit from actual time measerement is done
# Reading burst for the 2 power meters used in this example takes about 0.5 seconds
# Timestamp is with 1sec accuracy; if you need more, adapt code a bit
SYNC_TIMESTAMP = True
