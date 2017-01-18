#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import sys
from bd_connect.connect_bd import get_json
from config.setting import Setting
import logging
import os
import resource
import openzwave
import copy
import threading
import socket
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
from louie import dispatcher, All

"""
    About:
    Device Connector - ZWave Network Engine

    Descriptions:
    This module is the core engine of zwave device connector. The
     initialization and establish of zwave network will be processed by this 
     module. Within the context of created zwave network, the reading of 
     sensed data and control of zwave device is able to be conducted. Idealy, 
     this is a long running program, i.e. the program should not be terminated 
     as long as there are no nodes being added or removed. Therefore, the 
     control and of reading of zwave devce should be conducted via 
     sens_zwave.py program.

    Configurations:
    $ Find usb port of zwave stick:
    To do this, run find_port.sh script with super user permission in same 
    directory (sudo bash find_port.sh), and find the file path, which normally 
    shall be "/dev/ttyACM<x>".

    $ Modify zwave.json file:
    a. Modify the device path according to previous steps, as well as the log 
    level and log file name(or path);
    b. the MAX_THREAD item defines the maximum number of thread that allows to 
    process concurrently;
    c. the port item defines the port number by which this module will use to 
    communicate with sens_zwave.py program;

    $ Set the file name/path in this program:
    This can be retrived from CONFIG variable in this program, which is the 
    file name of json config file.

    $ Add python seach path to /etc/sudoers
    In addition, the python seach paths need be added for super users as well. 
    This can be done by adding env_keep += "PYTHONPATH" to /etc/sudoers (it is 
    recommended to use "pkexec visudo" to modify sudoers config file).

    $ Copy the openzave library to Connectors directory.
    The path of openzwave library shoulb be /Connectors/openzwave/

    How to Start?
    As the program will communicate with zwave hub controller (zwave stick),
    it need be launched with sudo permission:
        sudo python zwave.py
"""

CONFIG = "zwave"         # zwave.json file
MAX_THREAD = 1
threads = []             # thread pool
listen = {}

class ZwaveNetwork:
    """
        Class of zwavenetwork:
        In the context of the instance of ZwaveNetwork the instance of zwave 
        sensor and zwave actuator is able to proceeded.
    """
    def __init__(self):
        """
            Initialize using zwave.json config file defined in CONFIG variable
        """
        global MAX_THREAD
        global listen
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

        for k, v in multisensor_cred.setting["listen"].items():
            item = []
            for node in v:
                item.append(str(node))
            listen[int(k)] = item

        self.mapping  = {int(k): str(v) \
            for k, v in multisensor_cred.setting["mapping"].iteritems()}
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
            set all nodes using parameter and value specified in zwave.json.
            And update node name according to zwave.json file.

            Args: None
            Return: None
        """
        for node_id in self.network.nodes:
            self.config_node(node_id)
            self.update_node_name(node_id)

    def update_node_name(self, node_id):
        """
            update the nodes' name according to zwave.json config file

            Args: node_id the id of node (a positive integer)
            Return: None
        """
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
            This function aims to check whether the node (specified by 
            node_id) is connected in network. If not, the value, which is old 
            historical data, will be abandoned.

            Args: node id of specified nodes in network
            Return: ture if node is still connected in the network, or 
            otherwise 

            Note: this function is used for debugging purpose
        """
        if network.manager.isNodeFailed(network.home_id, node_id):
            return False
        return True

class ZwaveSensor:
    """
        Class of ZwaveSensor: the instance of this class is used to read value 
        from sensor nodes and publish data to BuildingDepot using RESTful API.

        The zwave sensor is only able to proceeded in the contextual of a 
        valid ZwaveNetwork
    """
    def __init__(self, network):
        """
            the zwave sensor is able to be launched in contextual of instance 
            of ZwaveNetwork

            Args: network the instance of ZwaveNetwork
            Return: None
        """
        multisensor_cred = Setting(CONFIG)
        self.network = network.network   # nethwork instance

    @staticmethod
    def get_mac_id(node, value):
        """
            Assemble manufacturer id, product type and product id to standard 
            mac assress format.

            Args: instance of a node
            Return: String of standard mac address format
        """
        mac_str= node.manufacturer_id[2:] + \
            node.product_type[2:] + \
            node.product_id[2:]
        mac_str = ':'.join(mac_str[i:i+2] for i in range(0, len(mac_str), 2))
        return mac_str + '_' + value.label

    @staticmethod
    def get_source_name(network, node, value):
        """
            build src name for each sensor points
        """
        src = []
        src.append(hex(network.home_id))
        src.append(node.name)
        src.append(value.label)
        if not value.units == '':
            src.append(value.units)
        return '_'.join(src)

    def read_power_level(self, node_id, value_id):
        """
            Read one power level value from a specified node, after which the 
            data will be posted to BuildingDepot using RESTful api.

            Note: The sensor points will be skipped once the value is not 
            specified in zwave.json (listen item) or the node is not connected 
            property.

            Args:
                node_id: the id of sepcified node
                value_id: the id of value (sensor point) on the specified node
            Return:
                status string indicates the sensing and posting process
        """
        global listen
        node = self.network.nodes[node_id]
        value = node.values[value_id]
        if node_id in listen and \
             value.label in listen[node_id] and\
             ZwaveNetwork.check_node_connection(self.network, node_id) and\
             value_id in node.get_power_levels():
            sdata = {}
            sdata["mac_id"] = ZwaveSensor.get_mac_id(node, value)         
            # get sensor data
            sdata[ZwaveSensor.get_source_name(self.network, node, value)] = \
                node.get_power_level(value_id)
            # assemble data
            data = {"sensor_data":{}}
            data["sensor_data"].update(sdata)
            # post data
            print(data)
            return str(get_json(json.dumps(data)))   # return a string
        return ""                   

    def read_rgbbulbs_value(self, node_id, value_id):
        """
            Read one rgb bulbs level value from a specified node, after which the data will be posted to BuildingDepot using RESTful api.

            Note: The sensor points will be skipped once the value is not 
            specified in zwave.json (listen item) or the node is not connected 
            property.

            Args:
                node_id: the id of sepcified node
                value_id: the id of value (sensor point) on the specified node
            Return:
                status string indicates the sensing and posting process
        """
        global listen
        node = self.network.nodes[node_id]
        value = node.values[value_id]
        if node_id in listen and \
             value.label in listen[node_id] and\
             ZwaveNetwork.check_node_connection(self.network, node_id) and\
             value_id in node.get_rgbbulbs():
            sdata = {}
            sdata["mac_id"] = ZwaveSensor.get_mac_id(node, value)          
            # get sensor data
            sdata[ZwaveSensor.get_source_name(self.network, node, value)] = \
                node.get_dimmer_level(value_id)
            # assemble data
            data = {"sensor_data":{}}
            data["sensor_data"].update(sdata)
            # post data
            print(data)
            return str(get_json(json.dumps(data)))   # return a string
        return ""           

    def read_dimmer_value(self, node_id, value_id):
        """
            Read one dimmer level value from a specified node, after which the 
            data will be posted to BuildingDepot using RESTful api.

            Note: The sensor points will be skipped once the value is not 
            specified in zwave.json (listen item) or the node is not connected 
            property.

            Args:
                node_id: the id of sepcified node
                value_id: the id of value (sensor point) on the specified node
            Return:
                status string indicates the sensing and posting process
        """
        global listen
        node = self.network.nodes[node_id]
        value = node.values[value_id]
        if node_id in listen and \
             value.label in listen[node_id] and\
             ZwaveNetwork.check_node_connection(self.network, node_id) and\
             value_id in node.get_dimmers():
            sdata = {}
            sdata["mac_id"] = ZwaveSensor.get_mac_id(node, value)          
            # get sensor data
            sdata[ZwaveSensor.get_source_name(self.network, node, value)] = \
                node.get_dimmer_level(value_id)
            # assemble data
            data = {"sensor_data":{}}
            data["sensor_data"].update(sdata)
            # post data
            print(data)
            return str(get_json(json.dumps(data)))   # return a string
        return ""       

    def read_battery_value(self, node_id, value_id):
        """
            Read one battery level value from a specified node, after which the data will be posted to BuildingDepot using RESTful api.

            Note: The sensor points will be skipped once the value is not 
            specified in zwave.json (listen item) or the node is not connected 
            property.

            Args:
                node_id: the id of sepcified node
                value_id: the id of value (sensor point) on the specified node
            Return:
                status string indicates the sensing and posting process
        """
        global listen
        node = self.network.nodes[node_id]
        value = node.values[value_id]
        if node_id in listen and \
             value.label in listen[node_id] and\
             ZwaveNetwork.check_node_connection(self.network, node_id) and\
             value_id in node.get_battery_levels():
            sdata = {}
            sdata["mac_id"] = ZwaveSensor.get_mac_id(node, value)          
            # get sensor data
            sdata[ZwaveSensor.get_source_name(self.network, node, value)] = \
                node.get_battery_level(value_id)
            # assemble data
            data = {"sensor_data":{}}
            data["sensor_data"].update(sdata)
            # post data
            print(data)
            return str(get_json(json.dumps(data)))   # return a string
        return ""

    def read_thermostats_value(self, node_id, value_id):
        """
            Read one thermostats value from a specified node, after which the 
            data will be posted to BuildingDepot using RESTful api.

            Note: The sensor points will be skipped once the value is not 
            specified in zwave.json (listen item) or the node is not connected 
            property.

            Args:
                node_id: the id of sepcified node
                value_id: the id of value (sensor point) on the specified node
            Return:
                status string indicates the sensing and posting process
        """
        global listen
        node = self.network.nodes[node_id]
        value = node.values[value_id]
        if node_id in listen and \
             value.label in listen[node_id] and\
             ZwaveNetwork.check_node_connection(self.network, node_id) and\
             value_id in node.get_thermostats():
            sdata = {}
            sdata["mac_id"] = ZwaveSensor.get_mac_id(node)          
            # get sensor data
            sdata[ZwaveSensor.get_source_name(self.network, node, value)] = \
                node.get_thermostat_value(value_id)
            # assemble data
            data = {"sensor_data":{}}
            data["sensor_data"].update(sdata)
            # post data
            print(data)
            return str(get_json(json.dumps(data)))   # return a string
        return ""

    def read_sensor_value(self, node_id, value_id):
        """
            Read one sensor value from a specified node, after which the data 
            will be posted to BuildingDepot using RESTful api.

            Note: The sensor points will be skipped once the value is not 
            specified in zwave.json (listen item) or the node is not connected 
            property.

            Args:
                node_id: the id of sepcified node
                value_id: the id of value (sensor point) on the specified node
            Return:
                status string indicates the sensing and posting process
        """
        global listen
        node = self.network.nodes[node_id]
        value = node.values[value_id]
        if node_id in listen and \
             value.label in listen[node_id] and\
             ZwaveNetwork.check_node_connection(self.network, node_id) and \
             value_id in node.get_sensors():
            sdata = {}
            sdata["mac_id"] = ZwaveSensor.get_mac_id(node, value)     
            # get sensor data
            sdata[ZwaveSensor.get_source_name(self.network, node, value)] = \
                node.get_sensor_value(value_id)
            # assemble data
            data = {"sensor_data":{}}
            data["sensor_data"].update(sdata)
            # post data
            print(data)
            return str(get_json(json.dumps(data)))   # return a string
        return ""

    def snes_all_nodes(self):
        """
            Read all sensor points from all nodes.

            Note: A specific sensor points may be skipped once the value is 
            not specified in zwave.json (listen item) or the node is not 
            connected property.

            Args: None
            Return: None
        """
        msg = ""
        for node_id in self.network.nodes:
            tmp = self.sens_one_node(node_id)
            if not tmp.isspace():
                msg = msg + tmp + "\n"
        return msg

    def sens_one_node(self, node_id):
        """
            Read all sensor points from a specified node.

            Note: A specific sensor points may be skipped once the value is 
            not specified in zwave.json (listen item) or the node is not 
            connected property.

            Args: node_id the specified node
            Return: None
        """
        msg = ""
        for val_id in self.network.nodes[node_id].values:
            tmp = self.read_sensor_value(node_id, val_id)
            if not tmp.isspace():
                msg = msg + tmp + "\n"
            tmp = ""
            tmp = self.read_thermostats_value(node_id, val_id)
            if not tmp.isspace():
                msg = msg + tmp + "\n"
            tmp = ""
            tmp = self.read_battery_value(node_id, val_id)
            if not tmp.isspace():
                msg = msg + tmp + "\n"
            tmp = ""
            tmp = self.read_dimmer_value(node_id, val_id)
            if not tmp.isspace():
                msg = msg + tmp + "\n"
            tmp = ""
            tmp = self.read_rgbbulbs_value(node_id, val_id)
            if not tmp.isspace():
                msg = msg + tmp + "\n"
            tmp = ""
            tmp = self.read_power_level(node_id, val_id)
            if not tmp.isspace():
                msg = msg + tmp + "\n"
        return msg

    @staticmethod
    def is_alarm(network, node_id, value_id):
        """
           justify whether the updated value is alarm
        """
        node = network.nodes[node_id]
        if value_id in node.get_sensors() or \
          value_id in node.get_power_levels() or \
          value_id in node.get_rgbbulbs() or \
          value_id in node.get_dimmers() or \
          value_id in node.get_battery_levels() or \
          value_id in node.get_thermostats() or \
          value_id in node.get_switches_all() or \
          value_id in node.get_protections():
            return False
        return True   

class ZwaveActuator:
    """
        Class of ZwaveActuator: the instance of this class is used to control 
        zwave device in the contexual of a valid zwave network.
    """
    def __init__(self, network):
        """
            Initialize using instance of zwavenetwork

            Args: network the instance of ZwaveNetwork
            Return: None
        """
        self.network = network.network

    def search_switch(self, node_id, label):
        """
            Check whether the specified switch (marked by label) of a 
            particular node exists.

            Args:
                node_id: a node specified by node_id
                label: the label of the switch
            Return: the id of the switch, or -1 if no switch can be found
        """
        for val in self.network.nodes[node_id].get_switches():
            if self.network.nodes[node_id].values[val].label == label:
                return val
        return -1

    def on(self, node_id, label):
        """
            Turn on the switch.

            Args:
                node_id: a node specified by node_id
                label: the label of the switch
            Return: status string
                {on/off : success} else
                {"Device Not Found/Error in fetching data"}             
        """
        val = self.search_switch(node_id, label)
        if self.network.nodes[node_id].set_switch(val,True):
            return "on/off : success\n"
        else:
            return "Device Not Found/Error in fetching data\n"

    def off(self, node_id, label):
        """
            Turn off the switch.

            Args:
                node_id: a node specified by node_id
                label: the label of the switch
            Return: status string
                {on/off : success} else
                {"Device Not Found/Error in fetching data"}             
        """
        val = self.search_switch(node_id, label)
        if self.network.nodes[node_id].set_switch(val,False):
            return "on/off : success\n"
        else:
            return "Device Not Found/Error in fetching data\n"

    def toggle(self, node_id, label):
        """
            Toggle the switch (change the switch state).

            Args:
                node_id: a node specified by node_id
                label: the label of the switch
            Return: status string
                {on/off : success} else
                {"Device Not Found/Error in fetching data"}             
        """
        if self.status(node_id, label):
            return self.off(node_id,label)
        else:
            return self.on(node_id, label)

    def status(self, node_id, label):
        """
            Get switch states

            Args:
                node_id: a node specified by node_id
                label: the label of the switch
            Return: True/False (bool data)          
        """
        val = self.search_switch(node_id, label)
        return self.network.nodes[node_id].get_switch_state(val) 

class task_thread(threading.Thread):
    """
        Class of task thread used to process received command
    """
    def __init__(self, conn, sock, network):
        """
            Initialize task
        """
        threading.Thread.__init__(self)
        self.conn = conn
        self.sock = sock
        self.network = network
    
    def run(self):
        """
            Task implementation
        """
        global threads
        exit = False
        cmds = str(self.conn.recv(2048)).strip().split()
        print(cmds)
        msg = ""
        try:
            if cmds[0] == "-r":
                node_id = int(cmds[1])
                sensor = ZwaveSensor(self.network)
                if node_id == -1:
                    msg = msg + sensor.snes_all_nodes()
                elif node_id > 1:
                    msg = msg + sensor.sens_one_node(node_id)
            elif cmds[0] == "-w":
                node_id = int(cmds[1])
                actuator = ZwaveActuator(self.network)
                if node_id > 1 and \
                    actuator.search_switch(node_id, cmds[2]) is not -1:
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
            elif cmds[0] == "-q":
                MAX_THREAD = 1  # dosen't allow any more thread to come 
                msg = "Bye"
                exit = True
        except Exception as e:
            print(e)
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
    """
        Socket initialization

        Note: only the localhost process can be connected to this engine.

        Return: created socket
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = socket.gethostbyname(socket.gethostname())
        port = int(Setting(CONFIG).setting["port"])
        s.bind((host, port))
        s.listen(5)
        return s
    except Exception as e:
        sys.exit("Socket Creation Failed\n" + str(e))


def louie_network_ready():
    """
        initial signal handler
    """
    dispatcher.connect(louie_value_update, ZWaveNetwork.SIGNAL_VALUE)


def louie_value_update(network, node, value):
    """
        signal handler when value is received/updated

        $$ only update of 'alarme type value' will be processed.
    """
    global threads
    global listen
    if node.node_id in listen \
        and value.label in listen[node.node_id] \
        and len(threads) < MAX_THREAD \
        and ZwaveSensor.is_alarm(network, node.node_id, value.value_id):
        data = {"sensor_data":{}}
        sdata = {}
        sdata["mac_id"] = ZwaveSensor.get_mac_id(node, value)
        sdata[value.label] = value.data_as_string     
        data["sensor_data"].update(sdata)
        # start a new thread for posting data
        newthread = threading.Thread(target=alarm_thread_post_bd, \
                    args=(copy.deepcopy(data),))
        threads.append(newthread)
        newthread.start()

def alarm_thread_post_bd(data):
    """
        a thread routine to post the passed in data to building depot
    
        Args: snesed data:
            sensor_data: {
                <attribute/meta data>
                <sensor data>
            }
        Return: None
    """
    print(data)
    print(get_json(json.dumps(data)))   # has some issues here!
    # remove from pool after finishing
    if threading.current_thread() in threads:
        threads.remove(threading.current_thread())

def main():
    """
        Main of the zwave network engine.

        Node: 
        $ Idealy, the program should be ran forever, as long as there are no 
        nodes being added or removed.
    
        $ No arguments are required for the program, however, the program need 
        be ran under usdo permission.
    """ 
    global threads
    network = ZwaveNetwork()
    network.network_init()
    dispatcher.connect(louie_network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)
    network.config_all_nodes()
    network.network_awake()
    sock = socket_init()

    try:
        while True:
            (conn, (ip, port)) = sock.accept()
            if len(threads) >= MAX_THREAD:
                conn.close()
            else:
                newthread = task_thread(conn, sock, network)
                threads.append(newthread)
                newthread.start()
    except Exception as e:         # if socket is closed by quit thread
        print("Socket Closed, Program Exited")
        sock.close()               # close socket
        network.network_stop()
        sys.exit("Bye")            # terminated program

if __name__ == "__main__":
    main()



