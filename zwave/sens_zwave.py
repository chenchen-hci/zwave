#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import time
import string
import random
import os
from config.setting import Setting

"""
    About:
    Device Connector - sens_zwave.py

    About: 
    This module is a connector that connects zwave device to BuildingDepot. 
    Essentially the operation of read and write of connector need be ran in 
    the contexual of ZwaveNetwork.

    How to Start?
    After setting up zwave device, ran following command to start zwave 
    network, as the operation of sensing and actuation need be performed in 
    the contexual of ZwaveNetwork. The network need be launched using sudo 
    permission, hence the root password may be needed.
        python sens_zwave.py -s

    Perform read and write opeation:
    Example:
        python sens_zwave.py -r -1             # read all nodes of the network
        python sens_zwave.py -r 3              # read all sensors on node 3
        python sens_zwave.py -w 3 Switch on    # activate node 3 switch

    The zwave network need be manully restarted in new network environment, 
    e.g. nodes are added/removed from network.
        python sens_zwave.py -q                # stop zwavenetwork
        python sens_zwave.py -s                # start zwavenetwork

    Usage:
    The usage information of this program can be quired from:
        python sens_zwave.py -u
    or  python sens_zwave.py
"""

CONFIG = "zwave"         # zwave.json file

def socket_init():
    """
        Socket initialization

        Note: only the localhost process can be connected to this engine.

        Return: created socket
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = socket.gethostname()
        port = int(Setting(CONFIG).setting["port"])
        s.connect((host, port))
        return s
    except Exception as e:
        sys.exit("Socket Creation Failed\n" + str(e))

def recv_timeout(the_socket, timeout = 3):
    """
        wrapper for receiving data from socket.
      
        Args: 
            the_socket: reference of the socket
            time_out: specify the maximum time for data transmission
        Return:
            String for reponse information
    """
    the_socket.setblocking(0)           # make socket non blocking
    total_data=[];
    data='';
    begin=time.time()
    while True:
        if total_data and time.time()-begin > timeout * 2:
            break
        elif time.time()-begin > timeout:
            break
        try:
            data = the_socket.recv(1024)
            if data and not data.isspace():
                total_data.append(data)
                begin = time.time()    # update beginning time
        except:
            pass
    return ''.join(total_data)

def usage(arguments):
    """
    usage infomation of the module
    """
    print("usage: {} [-r node_id] [-w node_id label control] [-q] [-s] [-u]" \
        .format(arguments[0]))
    print("    -r node_id: read sensed data from node with id being node_id, \
        which is a positive integer larger than 1. If node_id is -1, all \
        nodes will be scanned.")
    print("    -w node_id label control: send control command (on/off/toggle) \
        to switch named 'label' on node specified by node id.")
    print("    -s start zwave network engine.")
    print("    -q quit zwave network engine.")
    print("    -u show usage infomation.")

def main(arguments):
    """
        Accept the command to either read or actuate the zwave device.

        Args as Data:
                        '-r': Read data from zwave device and post to 
                              BuildingDepot stack 
                        '-w': Actuate the Zwave device Switch to switch on
                              and off.
                        '-s': Start ZwaveNetwork engine.
                        '-q': Terminate ZwaveNetwork engine.
                        '-u': Print usage information.
        Returns:
                        Status string indicating whether the command is
                        executed successfully.
                        If there are no reponse, this means the sensor/switch
                        value are skipped. There are 2 possible reasons 
                        causing this issue:
                        a) the deivce is not property connected to Zwave 
                        network (e.g. accidently power failure);
                        b) the sensor point is not specified in zwave.json 
                        file (the listen item)
    """
    s = socket_init()
    cmd = ""
    for arg in arguments[1:]:
        cmd = cmd + arg + " "
    s.send(cmd)
    print(recv_timeout(s).replace("\n", ""))        # print response
    s.close()                     # close the socket when done

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "-u":
        usage(sys.argv)
    elif sys.argv[1] == "-s":
        cmd_str = "sudo python zwave_network.py"
        os.system(cmd_str)
    else:
        main(sys.argv)
    sys.exit(0)
