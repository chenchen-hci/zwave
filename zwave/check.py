#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import resource
import openzwave
import sys
import time
from config.setting import Setting
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption

"""
    About:

    This module is part of debugging tool for zwave network device connector.

    The medodule is used to check whether hub and network devices are paired 
    successfully. All network and nodes meta information will be printed if 
    network is configured successfully.

    The module need be ran under super user mode:
    sudo python check_match.py.

    Credits:

    The print_network() and print_nodes() routine is modified based on example 
    demo program of python-zwave library [accessed on Jan 6, 2017].
"""

CONFIG = "zwave"
SEPARATOR_LENGTH = 60

class ZwaveNetworkDebug:
    """
        Class of zwavenetwork:
        In the context of the instance of ZwaveNetwork the instance of zwave 
        sensor and zwave actuator is able to proceeded.
    """
    def __init__(self):
        """
            Initialize using zwave.json config file defined in CONFIG variable
        """
        multisensor_cred = Setting(CONFIG)
        self.device = str(multisensor_cred.setting["device"])
        self.log = str(multisensor_cred.setting["log"])
        self.log_file = str(multisensor_cred.setting["log_file"])
        self.write_file = bool(multisensor_cred.setting["write_log_file"])
        self.output_console = bool(multisensor_cred.setting["write_console"])
        # format config dict

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
            print("Zwave initialization failed!")
            print("Please check the USB port of Zwave Stick")
            print(e)
            sys.exit(-1)

        # create a network instance
        self.network = ZWaveNetwork(options, log=None)

    def network_awake(self):
        """
            Awake zwave network.
            Terminated program if awake failed! 
        """
        print("INFO: Waiting for network awaked :")

        for i in range(0, 300):
            if self.network.state >= self.network.STATE_AWAKED:
                break
            else:
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(1.0)

        if self.network.state < self.network.STATE_AWAKED:
            sys.exit("Network is not awake, program abort!")

        for i in range(0, 300):
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

    def network_stop(self):
        """
            Stop network.
        """
        self.network.stop()
        print("INFO: Network stopped")

    def check_node_connection(self, node_id):
        """ 
            This function aims to check whether the node (specified by 
            node_id) is connected in network. If not, the value, which is old 
            historical data, will be abandoned.

            Args: node id of specified nodes in network
            Return: ture if node is still connected in the network, or 
            otherwise 

            Note: this function is used for debugging purpose
        """
        if self.network.manager.isNodeFailed(self.network.home_id, node_id):
            return False
        return True

    def check_all_nodes_connection(self):
        for node in self.network.nodes:
            if not self.check_node_connection(node):
                return False
        return True

    def print_network(self):
        """
            Print network info.
            The module is modified based on example demo program in openzwave 
            library.

            Args: instance of network
            Return: None
        """
        print("Network home id : {}".format(self.network.home_id_str))
        print("Controller node id : {}" \
            .format(self.network.controller.node.node_id))
        print("Nodes in network : {}".format(self.network.nodes_count))
        print("Controller capabilities : {}" \
            .format(self.network.controller.capabilities))
        print("Controller node capabilities : {}" \
            .format(self.network.controller.node.capabilities))
        print("Nodes in network : {}".format(self.network.nodes_count))
        print("-" * SEPARATOR_LENGTH)

    def print_nodes(self):
        """
            Print ALL nodes info.
            The module is modified based on example demo program in openzwave 
            library.

            Args: instance of network
            Return: None
        """
        for node in self.network.nodes:
            print("-" * SEPARATOR_LENGTH)
            print("{} - Name : {}" \
                .format(self.network.nodes[node].node_id, \
                    self.network.nodes[node].name))
            print("{} - Manufacturer name / id : {} / {}" \
                .format(self.network.nodes[node].node_id, \
                    self.network.nodes[node].manufacturer_name, \
                    self.network.nodes[node].manufacturer_id))
            print("{} - Product name / id / type : {} / {} / {}" \
                .format(self.network.nodes[node].node_id, \
                    self.network.nodes[node].product_name, \
                    self.network.nodes[node].product_id, \
                    self.network.nodes[node].product_type))
            # work through each nodes
            for val in self.network.nodes[node].values:
                print("{} - value id: {}" .format(node, val))
                print("{} - value label: {}" \
                    .format(node, self.network.nodes[node].values[val].label))
                print("{} - value max: {}" \
                    .format(node, self.network.nodes[node].values[val].max))
                print("{} - value min: {}" \
                    .format(node, self.network.nodes[node].values[val].min))
                print("{} - units: {}" \
                    .format(node, self.network.nodes[node].values[val].units))
                print("-" * int(SEPARATOR_LENGTH/2))
            print("-" * SEPARATOR_LENGTH)

def main():
    """
        Print all network and nodes information.
        This function is used to final check whether the configuration of 
        network is completed.

        Args: None
        Return: None
    """
    network = ZwaveNetworkDebug()
    network.network_init()
    network.network_awake()
    print("INFO: Network Launched Successfully!")
    network.print_network()
    network.print_nodes()
    # check the connection of each nodes in network
    if not network.check_all_nodes_connection():
        print("WARN: Dead node detected!")
    else:
        print("INFO: Pass node connection check!")
    network.network_stop()

if __name__ == "__main__":
    main()