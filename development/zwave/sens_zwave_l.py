#!/usr/bin/env python
# -*- coding: utf-8 -*-

# abhijit

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
import copy
from threading import Thread
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
from louie import dispatcher, All

"""
	About:
	Device Connector - Zwave Product [listening]

	Descriptions:
	This module is a device connector to connect zwave products such as Aeotec   Multisensor6 integrated sensors etc. During runtime, an instance of zwave network will be created and set to listning mode. At any time when any nodes in mesh network send value updated notification, the program will receive a value and start a new thread to post values to BuildingDepot.

	Configurations:
	$ Find usb port of zwave stick:
	To do this, run find_port.sh script with super user permission in same directory (sudo bash find_port.sh), and find the file path, which normally shall be "/dev/ttyACM<x>".

	$ Modify zwave.json file:
	Modify the device path according to previous steps, as well as the log level and log file name(or path). In addition, the check item in json file indicates what value of which nodes in mesh network will be listened. Finally, the MAX_THREAD item defines the maximum number of thread that allows to process simultaneously.

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
MAX_THREAD = 1
thread_counter = 1
check = {}               # define the item to be listened

class ZwaveNetwork:
	def __init__(self):
		"""
			Initialize using zwave.json config file defined in CONFIG variable
		"""
		# check will not be changed once it is initialized
		global check
		global MAX_THREAD
		multisensor_cred = Setting(CONFIG)
		self.device = str(multisensor_cred.setting["device"])
		self.log = str(multisensor_cred.setting["log"])
		self.log_file = str(multisensor_cred.setting["log_file"])
		self.write_file = bool(multisensor_cred.setting["write_log_file"])
		self.output_console = bool(multisensor_cred.setting["write_console"])

		self.config = {}
		# format config dict
		for config_k, config_v in multisensor_cred.setting["config"].items():
			item = {}
			for k, v in config_v.iteritems():
				item[int(k)] = int(v)	
			self.config[int(config_k)] = item
		# format check item
		for k, v in multisensor_cred.setting["check"].items():
			item = []
			for node in v:
				item.append(str(node))
			check[int(k)] = item 
		MAX_THREAD = int(multisensor_cred.setting["MAX_THREAD"])

	def network_init(self):
		"""
			Zwave network initialization.
			Terminate program if initialization failed.
		"""
		logging.basicConfig(level=logging.INFO)
		logger = logging.getLogger('openzwave')

		# option initialization, abort if initialization failed
		try:
			options = ZWaveOption(self.device, \
			 config_path="../openzwave/config", \
			 user_path=".", cmd_line="")
			options.set_log_file(self.log_file)
			options.set_append_log_file(self.write_file)
			options.set_console_output(self.output_console)
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
			Terminated program if awake failed! """
		print("INFO: Waiting for network awaked : ")

		for i in range(0,300):
			if self.network.state >= self.network.STATE_AWAKED:
				break
			else:
				sys.stdout.write('.')
				sys.stdout.flush()
				time.sleep(1.0)

		if self.network.state < self.network.STATE_AWAKED:
			sys.exit("Network is not awake, program abort!")

		for i in range(0,300):
			if self.network.state >= self.network.STATE_READY:
				break
			else:
				sys.stdout.write(".")
				sys.stdout.flush()
				time.sleep(1.0)

		if not self.network.is_ready:
			sys.exit("Network is not ready, program abort!")
		print("\nINFO: Network [{}] awaked!" .format(self.network.home_id_str))
		print("INFO: Number of nodes: [{}]" .format(self.network.nodes_count))

	def config_node(self, node_id):
		"""
			config a node specified by node id.

			Args: node id of specific node
			Return: None
		"""
		if node_id in self.config:
			for k, v in self.config[node_id]:
				print("key = " + str(k) + " value = " + str(v))
				self.networks.nodes[node_id].set_config_param(k, v)

	def config_all_nodes(self):
		"""
			config all nodes using parameter and value specified in zwave.json

			Args: None
			Return: None
		"""
		for ndoe_id in self.network.nodes:
			config_node(node_id)

	def network_stop(self):
		"""
			Stop network.
		"""
		self.network.stop()
		print("INFO: Network stopped")

	def check_node_connection(self, node_id):
		""" 
			This function aims to check whether the node (specified by node_id) is connected in network. If not, the value, which is old historical data, will be abandoned.

			Args: node id of specified nodes in network
			Return: ture if node is still connected in the network, or otherwise 

			Note: this function is used for debugging purpose
		"""
		if self.network.manager.isNodeFailed(self.network.home_id, node_id):
			print("WARN: Node [{}] is failed!" .format(node_id))
			return False
		return True

	def check_all_nodes_connection(self):
		""" 
			This function aims to check whether ALL nodes is connected in network. If any 'dead' node is detected, the function will return false.

			Args: None
			Return: ture if all node is still connected in the network, or otherwise

			Note: this function is used for debugging purpose
		"""
		for node in self.network.nodes:
			if not self.check_node_connection(node):
				return False
		return True

	@staticmethod
	def get_mac_id(node):
		"""
			Assemble manufacturer id, product type and product id to standard mac assress format.

			Args: instance of a node
			Return: String of standard mac address format
		"""
		mac_str= node.manufacturer_id[2:] + \
			node.product_type[2:] + \
			node.product_id[2:]
		return ':'.join(mac_str[i:i+2] for i in range(0, len(mac_str), 2))

def thread_post_bd(data):
	"""
		a thread routine to post the passed in data to building depot
	
		Args: snesed data:
			sensor_data: {
				mac_id: <node id (48bits)>,
				<All other sensor data>
			}
	"""
	global thread_counter
	print(data)
	print(get_json(json.dumps(data)))   # has some issues here!
	thread_counter -= 1

def louie_network_ready():
	"""
		initial signal handler
	"""
	dispatcher.connect(louie_value_update, ZWaveNetwork.SIGNAL_VALUE)

def louie_value_update(network, node, value):
	"""
		signal handler when value is received
	"""
	global MAX_THREAD
	global thread_counter
	if node.node_id in check \
		and value.label in check[node.node_id] \
		and thread_counter < MAX_THREAD:
		data = {"sensor_data":{}}
		sdata = {}
		sdata["mac_id"] = ZwaveNetwork.get_mac_id(node)
		sdata["quantity"] = value.label
		sdata["units"] = value.units
		sdata[value.label] = value.data_as_string
		data["sensor_data"].update(sdata)
		thread_counter += 1
		Thread(target=thread_post_bd, args=(copy.deepcopy(data),)).start()

def main(cmd):
	"""
		Accept command to either read or actuate (not implemented) the nodes in zwave network.

		Args:
			[-r/w]: -r indicates read from all sensors, while -w indicates write to sensor;
	
		Returns:
			1. If the args is to read
				{
					"success": "True" 
					"HTTP Error 400": "Bad Request"
				} 
	"""	
	if cmd == '-r':
		# parse input args
		network = ZwaveNetwork()
		network.network_init()
		network.config_all_nodes()
		dispatcher.connect(louie_network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)
		network.network_awake()

		while True:
			time.sleep(1000)

		network.network_stop()
	else:
		sys.exit("Not implemented")

if __name__ == "__main__":
	if len(sys.argv) < 2:
		sys.exit("Bad number of arguments!")
	else:
		main(sys.argv[1])



