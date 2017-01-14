#!/usr/bin/env python
# -*- coding: utf-8 -*-

# abhijit

import re
import urllib2
import json
import time
import sys
from Connectors.zwave.post_bd import get_json    # use another higher level connector
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
import socket
from threading import Thread
from SocketServer import ThreadingMixIn


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
threads = []
exit = False
network = None

class ZwaveNetwork:
	def __init__(self):
		"""
			Initialize using zwave.json config file defined in CONFIG variable
		"""
		# check will not be changed once it is initialized
		global MAX_THREAD
		multisensor_cred = Setting(CONFIG)
		self.device = str(multisensor_cred.setting["device"])
		self.log = str(multisensor_cred.setting["log"])
		self.log_file = str(multisensor_cred.setting["log_file"])
		self.write_file = bool(multisensor_cred.setting["write_log_file"])
		self.output_console = bool(multisensor_cred.setting["write_console"])

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
		for node_id in self.network.nodes:
			config_node(node_id)

	def network_stop(self):
		"""
			Stop network.
		"""
		self.network.stop()
		print("INFO: Network stopped")

	@staticmethod
	def check_node_connection(network, node_id):
		""" 
			This function aims to check whether the node (specified by node_id) is connected in network. If not, the value, which is old historical data, will be abandoned.

			Args: node id of specified nodes in network
			Return: ture if node is still connected in the network, or otherwise 

			Note: this function is used for debugging purpose
		"""
		if network.manager.isNodeFailed(network.home_id, node_id):
			print("WARN: Node [{}] is failed!" .format(node_id))
			return False
		return True


class ZwaveSensor:
	def __init__(self, network):
		multisensor_cred = Setting(CONFIG)
		self.network = network   # nethwork instance
		self.config = {}
		self.check = {}
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
			self.check[int(k)] = item 

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

	def read_sensor_value(self, node_id, value_id):
		# get sensor value
		node = self.network.nodes[node_id]
		value = node.values[value_id]
		if node_id in self.check and \
			 value.label in self.check[node_id] and\
			 ZwaveNetwork.check_node_connection(self.network, node_id):
			value.refresh()
			sdata = {}
			sdata["mac_id"] = ZwaveSensor.get_mac_id(node)
			sdata["quantity"] = value.label
			sdata["units"] = value.units
			sdata[value.label] = value.data_as_string
			# get sensor data
			sdata[value.label] = node.get_sensor_value(value_id)
			# assemble data
			data = {"sensor_data":{}}
			data["sensor_data"].update(sdata)
			# post data
			print(data)
			return get_json(json.dumps(data))   # return a string
		return "value abandoned!"

	def snes_all_nodes(self):
		for node_id in self.network.nodes:
			self.sens_one_node(node_id)

	def sens_one_node(self, node_id):
		for val_id in self.network.nodes[node_id].values:
			self.read_sensor_value(node_id, val_id)

class ZwaveActuator:
	def __init__(self, network):
		self.network = network

	def search_switch(self, node_id, label):   # make sure the switch exit!!
		for val in self.network.nodes[node_id].get_switches():
			if self.network.nodes[node_id].values[val].label == label:
				return val
		print("WARN: Cannot find target switch")
		return -1

	def on(self, node_id, label):
		val = self.search_switch(node_id, label)
		return self.network.nodes[node_id].set_switch(val,True)

	def off(self, node_id, label):
		val = self.search_switch(node_id, label)
		return self.network.nodes[node_id].set_switch(val,False)

	def toggle(self, node_id, label):
		if self.status(node_id, label):
			return self.off(node_id,label)
		else:
			return self.on(node_id, label)

	def status(self, node_id, label):
		val = self.search_switch(node_id, label)
		return self.network.nodes[node_id].get_switch_state(val) 

class ClientThread(Thread):
    def __init__(self, ip, port, conn, sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        self.sock = sock
 
    def run(self):
    	global network
    	global exit
        cmds = str(self.conn.recv(2048)).strip().split()
        print(cmds)
        try:
        	node_id = int(cmds[1])
        	if cmds[0] == "-r":
        		sensor = ZwaveSensor(network.network)
        		if node_id == -1:
        			sensor.snes_all_nodes()
        		elif node_id > 1:
        			sensor.sens_one_node(node_id)
        		else:
        			print("Bad Arguments")
        	elif cmds[0] == "-w":
        		assert (node_id > 1), "Node ID cannot smaller than 1!"
        		actuator = ZwaveActuator(network.network)
        		if actuator.search_switch(node_id, cmds[2]) is not -1:
        			if cmds[3] == "on":
        				actuator.on(node_id, cmds[2])
        			elif cmds[3] == "off":
        				actuator.off(node_id, cmds[2])
        			elif cmds[3] == "toggle":
        				actuator.toggle(node_id, cmds[2])
        			else:
        				print("Bad switch command")
        		else:
        			print("switch cannot be found!")
        	else:
        		print("Bad Arguments")
        except Exception as e:
        	print("Current thread abort!" + str(e))
        finally:
        	self.conn.close()

def get_socket():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
	host = socket.gethostname() # Get local machine name
	port = 12345                # Reserve a port for your service.
	s.bind((host, port))        # Bind to the port
	s.listen(5)                 # Now wait for client connection.
	return s

def main():
	"""
	"""	
	global threads
	global exit
	global network
	network = ZwaveNetwork()
	network.network_init()
	network.config_all_nodes()
	network.network_awake()

	sock = get_socket()
	while not exit:
		(conn, (ip, port)) = sock.accept()
		if len(threads) > MAX_THREAD:
			conn.close()
		else:
			newthread = ClientThread(ip, port, conn, sock)
    		newthread.start()
    		threads.append(newthread)
    # wait until all threads is done
	for th in threads:
		th.join()
    # stop zwave network
	sock.close()
	network.network_stop()

if __name__ == "__main__":
	main()



