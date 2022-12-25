"""
  Rename to config.py

  Configure:
  - MQTT client
  - Debug level

"""

import minimalmodbus

# [ LOGLEVELS ]
# DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = "DEBUG"

# NROF parameter reads from power meter per hour (60 equals every minute)
READ_RATE = 360 # 360 = every 10sec

# [ MQTT Parameters ]
# Using local dns names was not always reliable with PAHO
MQTT_BROKER = "192.168.1.1"
MQTT_PORT = 1883
MQTT_CLIENT_UNIQ = 'mqtt-hager-wp'
MQTT_QOS = 1
MQTT_USERNAME = "username"
MQTT_PASSWORD = "password"

# Max nrof MQTT messages per second
# Set to 0 for unlimited rate
MQTT_RATE = 100

MQTT_TOPIC_PREFIX = "hager-wp"

# Depends on your Hager power meter
MODBUS_SLAVE_ADDRESS = 1
MODBUS_DEVICE = "/dev/tty-rs485"
MODBUS_REGISTER_MAP = "register.csv"

# Many minimalmodbus defaults are not configurable if they match defaults from Hager
MODBUS_BAUDRATE = 19200 # default
MODBUS_PARITY=minimalmodbus.serial.PARITY_EVEN

# [ InfluxDB ]
# Add a influxdb database tag, for Telegraf processing (database:INFLUXDB)
# This is not required for core functionality of this parser
# Set to None if Telegraf is not used
INFLUXDB = "hager-wp"
