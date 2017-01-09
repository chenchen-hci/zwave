#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import resource
import openzwave
from Connectors.zwave.sens_zwave import ZWaveNetworkSensors
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption

"""
About:

This module is part of debugging tool for zwave network device connector.

The medodule is used to check whether hub and network devices are paired successfully. All network and nodes meta information will be printed if network is configured successfully.

The module need be ran under super user mode:
sudo python check_match.py.

Credits:

The print_network() and print_nodes() routine is modified based on example demo program of python-zwave library [accessed on Jan 6, 2017].
"""

SEPARATOR_LENGTH = 60

def print_network(network):
	"""
	Print network info.
	The module is modified based on example demo program in openzwave library.

	Args: instance of network
	Return: None
	"""
	print("Current zwave network infomation:")
    print("-" * SEPARATOR_LENGTH)
    print("Use openzwave library : {}".format(network.controller.ozw_library_version))
    print("Use python library : {}".format(network.controller.python_library_version))
    print("Use ZWave library : {}".format(network.controller.library_description))
    print("Network home id : {}".format(network.home_id_str))
    print("Controller node id : {}".format(network.controller.node.node_id))
    print("Controller node version : {}".format(network.controller.node.version))
    print("Nodes in network : {}".format(network.nodes_count))
    print("Controller capabilities : {}".format(network.controller.capabilities))
    print("Controller node capabilities : {}".format(network.controller.node.capabilities))
    print("Nodes in network : {}".format(network.nodes_count))
    print("Driver statistics : {}".format(network.controller.stats))
    print("-" * SEPARATOR_LENGTH)

def print_nodes(network):
	"""
	Print ALL nodes info.
	The module is modified based on example demo program in openzwave library.

	Args: instance of network
	Return: None
	"""
    print("-" * SEPARATOR_LENGTH)
    print("Driver statistics : {}".format(network.controller.stats))
    print("-" * SEPARATOR_LENGTH)
    print("-" * SEPARATOR_LENGTH)
    print("Try to autodetect nodes on the network")
    print("-" * SEPARATOR_LENGTH)
    print("Nodes in network : {}".format(network.nodes_count))
    print("-" * SEPARATOR_LENGTH)
    print("Retrieve switches on the network")
    print("-" * SEPARATOR_LENGTH)
    for node in network.nodes:
        # for each nodes
        print("-" * SEPARATOR_LENGTH)
        print("{} - Name : {}".format(network.nodes[node].node_id, network.nodes[node].name))
        print("{} - Manufacturer name / id : {} / {}".format(network.nodes[node].node_id, network.nodes[node].manufacturer_name, network.nodes[node].manufacturer_id))
        print("{} - Product name / id / type : {} / {} / {}".format(network.nodes[node].node_id, network.nodes[node].product_name, network.nodes[node].product_id, network.nodes[node].product_type))
        print("{} - Version : {}".format(network.nodes[node].node_id, network.nodes[node].version))
        print("{} - Command classes : {}".format(network.nodes[node].node_id,network.nodes[node].command_classes_as_string))
        print("{} - Capabilities : {}".format(network.nodes[node].node_id,network.nodes[node].capabilities))
        print("{} - Neigbors : {}".format(network.nodes[node].node_id,network.nodes[node].neighbors))
        print("{} - Can sleep : {}".format(network.nodes[node].node_id,network.nodes[node].can_wake_up()))
            groups = {}
        for grp in network.nodes[node].groups :
            groups[network.nodes[node].groups[grp].index] = {'label':network.nodes[node].groups[grp].label, 'associations':network.nodes[node].groups[grp].associations}
        print("{} - Groups : {}".format (network.nodes[node].node_id, groups))
        # work through each nodes
        values = {}
        for val in network.nodes[node].values :
            values[network.nodes[node].values[val].object_id] = {
                'label':network.nodes[node].values[val].label,
                'help':network.nodes[node].values[val].help,
                'command_class':network.nodes[node].values[val].command_class,
                'max':network.nodes[node].values[val].max,
                'min':network.nodes[node].values[val].min,
                'units':network.nodes[node].values[val].units,
                'data':network.nodes[node].values[val].data_as_string,
                'ispolled':network.nodes[node].values[val].is_polled}
        # walk through each command classes
        for cmd in network.nodes[node].command_classes:
            print("   ---------   ")
            print("cmd = {}".format(cmd))
            values = {}
            for val in network.nodes[node].get_values_for_command_class(cmd) :
                values[network.nodes[node].values[val].object_id] = {
                    'label':network.nodes[node].values[val].label,
                    'help':network.nodes[node].values[val].help,
                    'max':network.nodes[node].values[val].max,
                    'min':network.nodes[node].values[val].min,
                    'units':network.nodes[node].values[val].units,
                    'data':network.nodes[node].values[val].data,
                    'data_str':network.nodes[node].values[val].data_as_string,
                    'genre':network.nodes[node].values[val].genre,
                    'type':network.nodes[node].values[val].type,
                    'ispolled':network.nodes[node].values[val].is_polled,
                    'readonly':network.nodes[node].values[val].is_read_only,
                    'writeonly':network.nodes[node].values[val].is_write_only,
                    }
            print("{} - Values for command class : {} : {}".format(network.nodes[node].node_id, network.nodes[node].get_command_class_as_string(cmd), values))
            print("-" * SEPARATOR_LENGTH)

def main():
	"""
	Print all network and nodes information.
	This function is used to final check whether the configuration of network is completed.

	Args: None
	Return: None
	"""
	network = ZWaveNetworkSensors()
	network = ZWaveNetworkSensors()
	network.network_init()
	network.network_awake()
	print("network launched successfully!")
	network.print_network(network.network)
	network.print_nodes(network.network)
	network.network_stop()

if __name__ == "__main__":
	main()