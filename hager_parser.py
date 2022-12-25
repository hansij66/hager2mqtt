"""
  Parses Multical telegrams to MQTT messages
  Queue MQTT messages

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

"""

import threading
import copy
import time
import json

# locals
import config as cfg

# Logging
import __main__
import logging
import os
script = os.path.basename(__main__.__file__)
script = os.path.splitext(script)[0]
logger = logging.getLogger(script + "." + __name__)


class ParseTelegrams(threading.Thread):
  """
  """

  def __init__(self, trigger, stopper, mqtt, telegram):
    """
    Args:
      :param threading.Event() trigger: signals that new telegram is available
      :param threading.Event() stopper: stops thread
      :param mqtt.mqttclient() mqtt: reference to mqtt worker
      :param dict() telegram:  telegram
    """
    logger.debug(">>")
    super().__init__()
    self.__trigger = trigger
    self.__stopper = stopper
    self.__telegram = telegram
    self.__mqtt = mqtt
    self.__counter = 0

    logger.debug("<<")
    return

  def __del__(self):
    logger.debug(">>")

  def __publish_telegram(self, json_dict):
    # publish the dictionaries per topic
    logger.debug(">>")

    self.__counter += 1

    # make resilient against double forward slashes in topic
    topic = cfg.MQTT_TOPIC_PREFIX
    topic = topic.replace('//', '/')
    message = json.dumps(json_dict, sort_keys=True, separators=(',', ':'))
    self.__mqtt.do_publish(topic, message, retain=False)
    self.__mqtt.do_publish(cfg.MQTT_TOPIC_PREFIX + "/counter", str(self.__counter), retain=False)

    logger.debug("<<")
    return

  def __decode_telegrams(self, telegram):
    """
    Args:
      :param  telegram:

    Returns:
      :rtype: bool
      True: if change detected wrt previous read value
      False: no change detected wrt previous read value

    """
    logger.debug(">>")

    json_values = dict()

    # epoch, mqtt timestamp
    ts = int(time.time())

    # Build a dict of key:value, for MQTT JSON
    json_values["timestamp"] = ts

    # TODO remove; fix  in telegraf
    if cfg.INFLUXDB:
      json_values["database"] = cfg.INFLUXDB

    for r in telegram:
      json_values[ r['register-name'] ] = r['value']

    self.__publish_telegram(json_values)

    logger.debug("<<")
    return

  def run(self):
    logger.debug(">>")

    while not self.__stopper.is_set():
      # block till event is set, but implement timeout to allow stopper
      self.__trigger.wait(timeout = 1)
      if self.__trigger.is_set():
        if self.__telegram == None:
          logger.warning("self.__telegram == None")
          self.__trigger.clear()
          continue

        # Make copy of the telegram, for further parsing
        telegram = copy.deepcopy(self.__telegram)

        # Clear trigger, serial reader can continue
        self.__trigger.clear()

        self.__decode_telegrams(telegram)

    logger.debug("<<")
