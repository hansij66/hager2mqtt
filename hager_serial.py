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
import serial
import threading
import time
import csv
import minimalmodbus

# Local imports
import config as cfg

# Logging
import __main__
import logging
import os

script = os.path.basename(__main__.__file__)
script = os.path.splitext(script)[0]
logger = logging.getLogger(script + "." + __name__)

class TaskReadSerial(threading.Thread):

  def __init__(self, trigger, stopper, telegram):
    """

    Args:
      :param threading.Event() trigger: signals that new telegram is available
      :param threading.Event() stopper: stops thread
      :param csv reader object telegram: telegram with lines of dict key:value pairs
    """

    logger.debug(">>")
    super().__init__()
    self.__trigger = trigger
    self.__stopper = stopper
    self.__telegram = telegram

    self.__lastreadtime = 0
    self.__interval = 3600/cfg.READ_RATE

    logger.debug("<<")
    return

  def __del__(self):
    logger.debug(">>")

  def __read_serial(self):
    """
    """
    logger.debug(">>")

    while not self.__stopper.is_set():
      # wait till parser has copied telegram content
      # ...we need the opposite of trigger.wait()...block when set; not available
      while self.__trigger.is_set():
        time.sleep(0.1)

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
          logger.error(f"Register type {r['value']} is not supported")

        logger.debug(f"VALUE = {r}")

      self.__trigger.set()

      # wait based set rate
      while not self.__stopper.is_set():
        t_elapsed = int(time.time()) - self.__lastreadtime
        if t_elapsed > self.__interval:
            self.__lastreadtime = int(time.time())
            break
        else:
          # wait...
          time.sleep(1)
          logger.debug("Wait to satisfy READ_RATE")

    logger.debug("<<")
    return

  def run(self):
    logger.debug(">>")

    # Read modbus register file definitions and store in __modbus_register_map
    with open(cfg.MODBUS_REGISTER_MAP, 'r') as csvfile:

      # remove comments lines
      reader = csv.DictReader(filter(lambda row: row[0]!='#', csvfile))

      # strip white spaces
      register_map = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]

      # This does not work!
      #self.__telegram = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]
      #self.__telegram = copy.deepcopy(map)

      # This does work :)
      for r in register_map:
        self.__telegram.append(r)

    try:
      # modbus rs485 configuration
      self.__modbusclient = minimalmodbus.Instrument(port=cfg.MODBUS_DEVICE, slaveaddress=cfg.MODBUS_SLAVE_ADDRESS, mode="rtu")
      self.__modbusclient.serial.baudrate = cfg.MODBUS_BAUDRATE
      self.__modbusclient.serial.parity = cfg.MODBUS_PARITY
      self.__modbusclient.serial.stopbits = serial.STOPBITS_ONE
      self.__modbusclient.serial.timeout = 1
      self.__modbusclient.debug = False
      logger.debug(f"RS485 = {self.__modbusclient}")
    except Exception as e:
      logger.error(f"{e}")
      logger.error(f"EXIT")
      self.__stopper.set()
      return

    try:
      self.__read_serial()
    except Exception as e:
      logger.error(f"{e}")
    finally:
      self.__stopper.set()

    logger.debug("<<")
    return
