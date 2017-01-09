#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib2
import json
import time
import sys
from zwave.post_bd import get_json    # use another higher level connector
from config.setting import Setting
import logging
import os
import resource
import openzwave
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption

"""
About:
Device Connector - Zwave Product

Descriptions:
This module is a device connector to connect zwave products such as Aeotec   Multisensor6 integrated sensors etc. During runtime, an instance of zwave network will be created which would collect the data in each nodes and publish to BuildingDepot stack.

Configurations:
$ Find usb port of zwave stick:
To do this, run find_port.sh script with super user permission in same directory (sudo bash find_port.sh), and find the file path, which normally shall be "/dev/ttyACM<x>".

$ Modify zwave.json file:
Modify the device path according to previous steps, as well as the log level and log file name(or path).

$ Set the file name/path in this program:
This can be retrived from CONFIG variable in this program, which is the file name of json config file.

$ Add python seach path to /etc/sudoers
In addition, the python seach paths need be added for super users as well. This can be done by adding env_keep += "PYTHONPATH" to /etc/sudoers (it is recommended to use "pkexec visudo" to modify sudoers config file).

$ copy the openzave library to Connectors directory.

How to Start?
As the program will communicate with zwave hub controller (zwave stick), it need be launched with sudo permission:
    sudo python sens_zwave.py

"""

CONFIG = "zwave"         # zwave.json file

class ZwaveNetwork:
    def __init__(self):
        """
        Initialize using zwave.json config file defined in CONFIG variable
        """
        multisensor_cred = Setting(CONFIG)
        self.device = str(multisensor_cred.setting["device"])
        self.log = str(multisensor_cred.setting["log"])
        self.log_file = str(multisensor_cred.setting["log_file"])
        self.sdata = {} # sdata is used to bufer sensed data

    def network_init(self):
    	"""
    	Zwave network initialization.
    	Terminate program if initialization failed.
    	"""
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('openzwave')

        # option initialization
        try:
        	options = ZWaveOption(self.device, \
          	 config_path="../openzwave/config", \
          	 user_path=".", cmd_line="")
        	options.set_log_file(self.log_file)
        	options.set_append_log_file(False)
        	options.set_console_output(False)
        	options.set_save_log_level(self.log)
        	options.set_logging(False)
        	options.lock()
        except Exception as e:
        	print("Zwave initialization failed! \nPlease check the USB port of zwave stick!")
        	print(e)
        	sys.exit(-1)

        # create a network instance
        self.network = ZWaveNetwork(options, log=None)

    def network_awake(self):
    	"""
    	Awake zwave network.
    	Terminated program if awake failed!
    	"""
        self.time_started = 0
        print("INFO: Waiting for network awaked : ")
        
        for i in range(0,300):
            if self.network.state >= self.network.STATE_AWAKED:
                break
            else:
                sys.stdout.write('.')
                sys.stdout.flush()
                self.time_started += 1
                time.sleep(1.0)

        if self.network.state < self.network.STATE_AWAKED:
            sys.exit("Network is not awake, program abort!")

        for i in range(0,300):
            if self.network.state >= self.network.STATE_READY:
                break
            else:
                sys.stdout.write(".")
                self.time_started += 1
                sys.stdout.flush()
                time.sleep(1.0)

        if not self.network.is_ready:
            sys.exit("Network is not ready, program abort!")
        print("\nINFO: Network [{}] awaked!" .format(self.network.home_id_str))

    def network_stop(self):
    	"""
    	Stop network.
    	"""
        self.network.stop()
        print("INFO: Network stopped")

    def get_nodes(self):
    	"""
    	Return number of network nodes (sleep/awake)
    	"""
        return self.network.nodes


    def node_info(self, node_id):
    	"""
    	Obtain the mac_id of specified nodes. The mac_id will be represented byproduct id (16bits).
    	
    	Arg: the node id which is larger or equal to 1
    	Return: None
    	"""
        node = self.network.nodes[node_id]
        self.sdata["mac_id"] = node.product_id

    def sensor_info(self, node_id):
        """
        Obtain sensed data which will be stored into sdata dict.
        An example of multisensor 6 are:
        { 
            'Luminance': 173.0, 
            'Ultraviolet': 0.0, 
            'Sensor': True, 
            'Relative Humidity': 8.0, 
            'Temperature': 66.4000015258789
        }

    	Arg: the node id which is larger or equal to 1
    	Return: None
        """
        node = self.network.nodes[node_id]
        for val in node.get_sensors():
            self.sdata[node.values[val].label] = node.get_sensor_value(val)
    
    def battery_info(self, node_id):
    	"""
    	Obtain battery information, which will be stored in sdata dict.

    	Arg: the node id which is larger or equal to 1
    	Return: None    	
    	"""
        node = self.network.nodes[node_id]
        for val in node.get_battery_levels():
            self.sdata[node.values[val].label] = node.get_battery_level(val)

    def get_device_data(self, node_id):
        """
        Obtain all sensor/meta data using node_info(), sensor_info() and battery_info().

        Args: the node id which is larger or equal to 1
        Return: Formated dictionary:
        {
			"sensor_data":
			{
				<All sensor data>
			}
        }
        """
        self.node_info(node_id) 
        self.sensor_info(node_id)
        self.battery_info(node_id)
        # update the data format
        data = {"sensor_data": {}}
        data["sensor_data"].update(self.sdata)
        self.sdata = {}  # reset buffer
        return data

def main(arguments):
	"""
	Accept command to either read or actuate (not implemented) the nodes in zwave network.

	Args:
		1. r/w: r indicates read from sensor, while w indicates write to sensor
	
	Returns:
        1. If the args is to read energy data from Wemo
           {
                "success": "True" 
                "HTTP Error 400": "Bad Request"
           }
	"""
	if len(arguments) < 2:
		sys.exit("Error: one argument is required")
	
	cmd = arguments[1]
	if cmd == 'r':
		network = ZwaveNetwork()
		network.network_init()
		network.network_awake()

		for node in network.get_nodes():
			data = network.get_device_data(node)
			print(data)
			print(get_json(json.dumps(data)))
		network.network_stop()
	else:
		sys.exit("Not implemented")

if __name__ == "__main__":
    main(sys.argv)



