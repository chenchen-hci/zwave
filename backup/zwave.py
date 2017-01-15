#!/usr/bin/env python
# -*- coding: utf-8 -*-

# abhijit

import re
import urllib2
import json
import time
import sys
from Connectors.zwave.post_bd import get_json
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
import socket
from threading import Thread
from SocketServer import ThreadingMixIn
import threading
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
		# format config dict
		self.config = {}
		for config_k, config_v in multisensor_cred.setting["config"].items():
			item = {}
			for k, v in config_v.iteritems():
				item[int(k)] = int(v)	
			self.config[int(config_k)] = item

		self.mapping  = {int(k): str(v) for k, v in multisensor_cred.setting["mapping"].iteritems()}
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
		print("INFO: Waiting for network awaked :")

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
			for k, v in self.config[node_id].iteritems():
				self.network.nodes[node_id].set_config_param(k, v)

	def config_all_nodes(self):
		"""
			config all nodes using parameter and value specified in zwave.json

			Args: None
			Return: None
		"""
		for node_id in self.network.nodes:
			self.config_node(node_id)
			self.update_node_name(node_id)

	def update_node_name(self, node_id):
		if node_id in self.mapping:
			self.network.nodes[node_id].name = self.mapping[node_id]

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
			return False
		return True

class ZwaveSensor:
	def __init__(self, network):
		multisensor_cred = Setting(CONFIG)
		self.network = network.network   # nethwork instance

		self.listen = {}
		# format check item
		for k, v in multisensor_cred.setting["listen"].items():
			item = []
			for node in v:
				item.append(str(node))
			self.listen[int(k)] = item 

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
		if node_id in self.listen and \
			 value.label in self.listen[node_id] and\
			 ZwaveNetwork.check_node_connection(self.network, node_id):
			value.refresh()
			sdata = {}
			sdata["node_name"] = self.network.nodes[node_id].name
			sdata["home_id"] = str(self.network.home_id)
			sdata["node_id"] = str(node_id)
			sdata["mac_id"] = ZwaveSensor.get_mac_id(node)
			sdata["quantity"] = value.label
			sdata["units"] = value.units
			sdata["identifier"] = sdata["home_id"] + ":" + sdata["node_id"] + \
									"[" + sdata["node_name"] + "]:" + \
									sdata["quantity"]			
			# get sensor data
			sdata[value.label] = node.get_sensor_value(value_id)
			# assemble data
			data = {"sensor_data":{}}
			data["sensor_data"].update(sdata)
			# post data
			print(data)
			return str(get_json(json.dumps(data)))   # return a string
		return ""

	def snes_all_nodes(self):
		msg = ""
		for node_id in self.network.nodes:
			tmp = self.sens_one_node(node_id)
			if not tmp.isspace():
				msg = msg + tmp + "\n"
		return msg

	def sens_one_node(self, node_id):
		msg = ""
		for val_id in self.network.nodes[node_id].values:
			tmp = self.read_sensor_value(node_id, val_id)
			if not tmp.isspace():
				msg = msg + tmp + "\n"
		return msg

class ZwaveActuator:
	def __init__(self, network):
		self.network = network.network

	def search_switch(self, node_id, label):   # make sure the switch exit!!
		for val in self.network.nodes[node_id].get_switches():
			if self.network.nodes[node_id].values[val].label == label:
				return val
		return -1

	def on(self, node_id, label):
		val = self.search_switch(node_id, label)
		if self.network.nodes[node_id].set_switch(val,True):
			return "on/off : success\n"
		else:
			return "Device Not Found/Error in fetching data\n"

	def off(self, node_id, label):
		val = self.search_switch(node_id, label)
		if self.network.nodes[node_id].set_switch(val,False):
			return "on/off : success\n"
		else:
			return "Device Not Found/Error in fetching data\n"

	def toggle(self, node_id, label):
		if self.status(node_id, label):
			return self.off(node_id,label)
		else:
			return self.on(node_id, label)

	def status(self, node_id, label):
		val = self.search_switch(node_id, label)
		return self.network.nodes[node_id].get_switch_state(val) 

class ClientThread(Thread):
	def __init__(self, ip, port, conn, sock, network):
		Thread.__init__(self)
		self.ip = ip
		self.port = port
		self.conn = conn
		self.sock = sock
		self.network = network
 	
	def run(self):
		global threads
		exit = False
		cmds = str(self.conn.recv(2048)).strip().split()
		print(cmds)
		msg = ""
		try:
			if cmds[0] == "r":
				node_id = int(cmds[1])
				sensor = ZwaveSensor(self.network)
				if node_id == -1:
					msg = msg + sensor.snes_all_nodes()
				elif node_id > 1:
					msg = msg + sensor.sens_one_node(node_id)
			elif cmds[0] == "w":
				node_id = int(cmds[1])
				actuator = ZwaveActuator(self.network)
				if node_id > 1 and actuator.search_switch(node_id, cmds[2]) is not -1:
					if cmds[3] == "on":
						msg = msg + actuator.on(node_id, cmds[2])
					elif cmds[3] == "off":
						msg = msg + actuator.off(node_id, cmds[2])
					elif cmds[3] == "toggle":
						msg = msg + actuator.toggle(node_id, cmds[2])
					else:
						msg = msg + "Switch Command Not Found\n"
				else:
					msg = msg + "Device Not Found\n"
			elif cmds[0] == "q":
				MAX_THREAD = 0  # dosen't allow any more thread to come 
				msg = "Bye"
				exit = True
		except Exception as e:
			msg += "Bad Arguments"
		finally:
			self.conn.send(msg)
			self.conn.close()
			if exit:
				for th in threads:
					if th != threading.current_thread():
						th.join()
				self.sock.shutdown(socket.SHUT_RDWR)
			if threading.current_thread() in threads:
				threads.remove(threading.current_thread())

def socket_init():
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
		host = socket.gethostbyname(socket.gethostname())  # restrict to listen localhost only                      # Get local machine name
		port = int(Setting(CONFIG).setting["port"])     # Reserve a port for your service.
		s.bind((host, port))        # Bind to the port
		s.listen(5)                 # Now wait for client connection.
		return s
	except Exception as e:
		sys.exit("Socket Creation Failed\n" + str(e))

def main():
	"""
	"""	
	global threads
	network = ZwaveNetwork()
	network.network_init()
	network.network_awake()
	network.config_all_nodes()

	sock = socket_init()

	try:
		while True:
			(conn, (ip, port)) = sock.accept()
			if len(threads) > MAX_THREAD:
				conn.close()
			else:
				newthread = ClientThread(ip, port, conn, sock, network)
    			newthread.start()
    			threads.append(newthread)
	except Exception as e:
		print("Socket Closed, Program Exited")
		sock.close()  # clean up all  other thread
		network.network_stop()
		sys.exit("Bye")

if __name__ == "__main__":
	main()



