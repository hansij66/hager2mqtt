"""
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.

Description
-----------

"""

import threading
import time
import csv
import minimalmodbus
import json

# Local imports
import config as cfg

# Logging
import __main__
import logging
import os

script = os.path.basename(__main__.__file__)
script = os.path.splitext(script)[0]
logger = logging.getLogger(script + "." + __name__)


class TaskReadPowerMeter(threading.Thread):
  def __init__(self, name, modbus_address, register_map, modbus_semaphore, t_readrate, t_mqtt, t_threads_stopper):
    """
    Assumption is that processing the serial data for MQTT is done ....TODO

    :param name:
    :param modbus_address:
    :param register_map:
    :param modbus_semaphore:
    :param t_readrate:
    :param t_mqtt:
    :param t_threads_stopper:
    """

    logger.debug(f">> {name}")
    super().__init__()
    self.__name = name
    self.__modbus_address = modbus_address
    self.__register_map = register_map
    self.__modbus_semaphore = modbus_semaphore
    self.__t_readrate = t_readrate
    self.__t_mqtt = t_mqtt
    self.__t_threads_stopper = t_threads_stopper

    self.__telegram = list()

    self.__json_values = dict()

    # Handle to minimalmodbus Instrument
    self.__modbusclient = None

    # Is the Modbus connection with power meter established?
    self.__is_connected = False

    # Keep count of nr of reads since start of parser
    self.__counter = 0

    # Bookkeeping for throttling read rate
    self.__lastreadtime = 0
    self.__interval = 3600/cfg.READ_RATE

    logger.debug(f"<< {self.__name}")
    return

  def __del__(self):
    logger.debug(f">> {self.__name}")

  def __publish_telegram(self):
    """
    Publish the dictionaries per topic

    :param json_dict:
    :return:
    """

    logger.debug(f">> {self.__name}")

    # make resilient against double forward slashes in topic
    topic = cfg.MQTT_TOPIC_PREFIX + "/" + self.__name
    topic = topic.replace('//', '/')

    # Only when power meter is connected, publish values
    # TODO....is  this called if power meter is not connected?
    if self.__is_connected:
      message = json.dumps(self.__json_values, sort_keys=True, separators=(',', ':'))
      self.__t_mqtt.do_publish(topic, message, retain=False)

    self.__t_mqtt.do_publish(topic + "/counter", str(self.__counter), retain=False)

    # Indicate whether power meter is connected (or not)
    status = "power on" if self.__is_connected else "power off"
    self.__t_mqtt.do_publish(topic + "/status", status, retain=True)

    logger.debug(f"<< {self.__name}")
    return

  def __read_modbus(self):
    """
    1. wait till ReadRateTimer event fires
    2. Read power meter
    3. Indicate that reading finished to ReadRateTimer
    4. Wait till all tasks have read power meter
    5. start over
    """
    logger.debug(f">> {self.__name}; MODBUS={self.__modbusclient}")

    # Clear the dict where we store all Kamstrup meter values
    self.__json_values.clear()

    while not self.__t_threads_stopper.is_set():
      # wait till time-out
      if not self.__t_readrate.wait(0.2):
        continue
      else:
        try:
          t = time.time()
          self.__modbus_semaphore.acquire()
          logger.debug(f"{self.__name}: Acquired modbus semapahore after t = {round(time.time() - t, 2)} seconds")

          # Build a dict of key:value, for MQTT JSON
          # Get timestamp from ReadRateTimer thread
          ts = self.__t_readrate.timestamp()
          self.__json_values["timestamp"] = ts

          # Read modbus registers
          for r in self.__telegram:
            if r['type'] == 'U16':
              r['value'] = self.__modbusclient.read_register(int(r['address']), number_of_decimals=int(r['decimals']), signed=False)
            elif r['type'] == 'S16':
              r['value'] = self.__modbusclient.read_register(int(r['address']), number_of_decimals=int(r['decimals']), signed=True)
            elif r['type'] == 'U32':
              r['value'] = self.__modbusclient.read_long(int(r['address']), signed=False) / (10 ** int(r['decimals']))
            elif r['type'] == 'S32':
              r['value'] = self.__modbusclient.read_long(int(r['address']), signed=True) / (10 ** int(r['decimals']))
            elif r['type'] == 'STR':
              r['value'] = self.__modbusclient.read_string(int(r['address']), number_of_registers=16)
            else:
              logger.error(f"{self.__name}: Register type {r['value']} is not supported")

        except Exception as e:
          logger.debug(f"{self.__name}: {e}")
          self.__is_connected = False

          ## chnaged in v2.0.3
          #self.__decode_telegrams()
        else:
          # We are still connected to Hager Power meter
          self.__is_connected = True

          # We did read values; increment counter
          self.__counter += 1

          # Start parsing
          ## chnaged in v2.0.3
          #self.__decode_telegrams()
        finally:
          # Start parsing
          ## chnaged in v2.0.3
          self.__modbus_semaphore.release()
          self.__t_readrate.release(self.__name)

          # Parse values
          if self.__is_connected:
            for r in self.__telegram:
              self.__json_values[r['register-name']] = r['value']

          self.__publish_telegram()

      # As __t_readrate is still set, and to prevent that we will read again the power meter;
      # wait till __t_readrate gets cleared; After __t_readrate is cleared, start from top
      while self.__t_readrate.is_set():
        logger.debug(f"{self.__name}: Wait till all tasks are done")
        time.sleep(1.0)

    logger.debug(f"<< {self.__name}")
    return

  def run(self):
    logger.debug(f">> {self.__name}")

    current_dir = os.path.dirname(os.path.realpath(__file__))
    register_map_file = current_dir + "/" + self.__register_map

    # Read modbus register file definitions and store in __modbus_register_map
    try:
      with open(register_map_file, 'r') as csvfile:

        # remove comments lines
        reader = csv.DictReader(filter(lambda row: row[0] != '#', csvfile))

        # strip white spaces
        register_map = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]

        # Append every csv line with registers key:values to telegram list
        for r in register_map:
          self.__telegram.append(r)
    except FileNotFoundError:
      logger.error(f"File {self.__register_map} not found")
      self.__t_threads_stopper.set()
      return
    except Exception as e:
      logger.warning(f"{self.__name}: {e}")
      self.__t_threads_stopper.set()
      return

    # Setup connection with modbus power meter
    while not (self.__t_threads_stopper.is_set() or self.__is_connected):
      try:
        logger.debug(f"{self.__name}: Setup connection to device with address {self.__modbus_address}")
        # modbus rs485 configuration
        self.__modbusclient = minimalmodbus.Instrument(port=cfg.MODBUS_RS485_DEVICE, slaveaddress=self.__modbus_address, mode="rtu")
        self.__modbusclient.serial.parity = cfg.MODBUS_PARITY
        self.__modbusclient.debug = False
        logger.debug(f"{self.__name}: RS485 = {self.__modbusclient}")
      except Exception as e:
        logger.warning(f"{self.__name}: {e}")
        logger.warning(f"{self.__name}: Wait to reconnect")
        time.sleep(5)
      else:
        logger.debug(f"{self.__name}: Connection to device with address {self.__modbus_address} is successfull")
        self.__is_connected = True

    try:
      self.__read_modbus()
    except Exception as e:
      logger.error(f"{self.__name}: {e}")
    finally:
      self.__t_threads_stopper.set()

    logger.debug(f"<< {self.__name}")
    return
