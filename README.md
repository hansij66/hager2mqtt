# Hager ECR380D MQTT
MQTT client/parser for Hager ECR180D/ECR380D family kWh/power meters.
- Not all registers are implemented; adapt registermap.csv for your own needs
- Can be adapted for other Hager kWh meters, eg ECR180D.
- Use 190724_MODBUS_TABLE_FOR_ENERGY_METERS.XLS to adapt register.cv
- Supports multiple Hager power meters on one single RS485 bus
- Ensure that RS485 bus is properly terminated with 120 0hm resistor
- MQTT Parser has been tested with one device (I did not own more Hager power devices). It should work with multiple devices; Let me know if it works (or not)
- Timestamps (used for influxdb) are generated with 1sec accuracy
- All power meters are read in a single sequential burst

## Usage:
* Copy `systemd/hager-mqtt.service` to `/etc/systemd/system`
* Adapt path in `hager-mqtt.service` to your install location (default: `/opt/iot/hager`)
* Copy `config.rename.py` to `config.py` and adapt for your configuration (minimal: mqtt ip, username, password, RS485)
* `sudo systemctl enable hager-mqtt`
* `sudo systemctl start hager-mqtt`

Use
http://mqtt-explorer.com/
to test & inspect MQTT messages

## Requirements
* paho-mqtt
* minimalmodbus
* pyserial
* python 3.x

Tested under Linux; there is no reason why it does not work under Windows.

## InfluxDB
* Use `telegraf-hager-powermeters.conf` as Telegraf configuration file to get Hager MQTT data into InfluxDB

## Licence
GPL v3

## Versions
1.0.0
* Initial version
* Supports only single power meter

2.0.0
* Support multiple Hager power meters on one single RS485 bus

