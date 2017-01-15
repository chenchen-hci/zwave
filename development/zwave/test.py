#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from openzwave.option import ZWaveOption
from openzwave.network import ZWaveNetwork
from config.setting import Setting
from Connectors.zwave.sens_zwave import ZwaveNetwork
import time

def search_switch(label, network, node_id):
    """
    return value id
    """
    for val in network.nodes[node_id].get_switches():
        if network.nodes[node_id].values[val].label == label:
            return val
    return -1

CONFIG = "zwave"         # zwave.json file
NODE = 1
iterl = 3
	
def checkNodeConnection(network):
	for node in network.nodes:
		removeNodeFailed(network, node)

def removeNodeFailed(network, selectedNode):
    if network.manager.isNodeFailed(network.home_id, selectedNode):
     	print("Node [{}] is failed!" .format(selectedNode))


network = ZwaveNetwork()
network.network_init()
network.network_awake()

node2 = network.network.nodes[3]
print(node2.product_name) # this is the multisensor on my network. Yours may be a different node.

print('-' * 60)
values = node2.get_values()
for val in node2.values:
    values[node2.values[val].object_id] = {
        'label':node2.values[val].label,
        'help':node2.values[val].help,
        'command_class':node2.values[val].command_class,
        'max':node2.values[val].max,
        'min':node2.values[val].min,
        'units':node2.values[val].units,
        'data':node2.values[val].data_as_string,
        'ispolled':node2.values[val].is_polled
        }
#print("{} - Values : {}".format(node2.node_id, values))
#print("------------------------------------------------------------")
for cmd in node2.command_classes:
    print("   ---------   ")
    #print("cmd = {}".format(cmd))
    values = {}
    for val in node2.get_values_for_command_class(cmd) :
        values[node2.values[val].object_id] = {
            'label':node2.values[val].label,
            'help':node2.values[val].help,
            'max':node2.values[val].max,
            'min':node2.values[val].min,
            'units':node2.values[val].units,
            'data':node2.values[val].data,
            'data_str':node2.values[val].data_as_string,
            'genre':node2.values[val].genre,
            'type':node2.values[val].type,
            'ispolled':node2.values[val].is_polled,
            'readonly':node2.values[val].is_read_only,
            'writeonly':node2.values[val].is_write_only,
            }
    print("{} - Values for command class : {} : {}".format(node2.node_id, node2.get_command_class_as_string(cmd), values))
    print("------------------------------------------------------------")
print('-' * 60)


# get current config values
print("node2.get_sensors()\n" + str(node2.get_sensors()))
# print(str(node2.request_all_config_params()))

# set timing and stuff on multisensor
print("---------------------------------------------------")
print(node2.request_config_param(2))  # this shows the current interval (3600 seconds)
print("---------------------------------------------------")
node2.set_config_param(2, 20)  # set the temperature sensor interval to 120 seconds

print(node2.request_config_param(2))  # this shows the current interval (3600 
# node2.set_config_param(3, 125) # set motion sensor On duration to just over 2 minutes. (shorter and it never registers as on!)
 
# set reporting of power level on Aeon smart energy switches
# node5.set_config_param(101,2)  # send multisensor info about power
# node5.set_config_param(111,20) # send it every 20 seconds. 
 

time.sleep(5)

# # switch
# print(node2.get_switches_all())

# val_id =  search_switch("Switch All", network.network, 3)
# print(val_id)
# print(node2.set_switch(val_id, True))
# print(node2.get_switch_state(val_id))

val = search_switch("Switch", network.network, 3)

print(val)
print("Activate switch")
print(node2.set_switch(val,True))
time.sleep(10.0)
print("Deactivate switch")
print(node2.set_switch(val,False))


for node in network.network.nodes:
    for val in network.network.nodes[node].get_switches_all() :
        print(val)
        print("  label/help : {}/{}".format(network.network.nodes[node].values[val].label, network.network.nodes[node].values[val].help))
        print("  value / items: {} / {}".format(network.network.nodes[node].get_switch_all_item(val), network.network.nodes[node].get_switch_all_items(val)))
        print("  state: {}".format(network.network.nodes[node].get_switch_all_state(val)))
# get_swaitch_state(val_id)

# for val in network.nodes[node].get_switches_all():
#     node2.set_switch()

# get sensor info

# # check connection
# checkNodeConnection(network.network)

# print("Command_alarm class")
# print(node2.values)
# print(node2.get_values(class_id=0x80, genre='User', \
#         type='Byte', readonly=True, writeonly=False))

# print('-' * 70)

# print("-" * 60)
# print("request states")
# print(str(node2.request_state()))
# print(str(node2.network_update()))

# # only retrieve one set of values
# for val in node2.get_sensors():
# 	print(str(val))
# 	print(str(node2.values[val]))
# 	print("-" * 60)
# 	iterl -= 1

network.network_stop()
sys.exit(0)

