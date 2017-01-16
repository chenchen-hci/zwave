# ZWave Device Connector 
Zwave device connector for BuildingDepotV3.6 [Done! :tada:]

## General Phylosophy
The main challenge that the zwave device connector face is the slow speed for establish of zwave network. Typically the creation of zwave network will take roughly 10 ~ 20 seconds. Therefore the sampling frequency of device connector can be degenerated due to this fact. 

For solving this issue, a instance of zwave network is created by `zwave_network.py` program, which is idealy a long running program and should be considered as a background engine (black box) that is not supposed to be exposed to users. Within the contextual of zwave network, various operations such as reading data from nodes and sending command to device switch can be performed using `sens_zwave.py` module, which can be cosidered as a interface for external program to communicate with zwave network. The communication between `zwave_network.py` and `sens_zwave.py` is performed via TCP/IP socket. However only localhost programs are allowed to be connected to zwave network. 

In short, external programs are supposed to call `sens_zwave.py` for performing various operations, i.e. there are no need to call `zwave_network.py` directly.

## Program Usage
Generally speaking, 5 options can be used to call `sens_zwave.py` module:

### Start Zwave Network
As is demonstrated in previous section, the operations of `sens_zwave.py` is performed within the contextual of `zwave_network.py`. Hence the first thing to do before performing various sensing/actuatng operations is to establish zwave network, which must be done manually using following command (as the initializing of zwave network is performed under sodo operation, the input of root password may be required):
```
$ python sens_zwave.py -s
```

### Quit Network
The zwave network will not be terminated automatically, since the creation of zwave network is a time consuming task, which can degenerate the system sampling frequency. Hence it need be terminated manually using following command in the final steps:
```
$ python sens_zwave.py -q
```

### Usage Information
The usage information of program can be retrieved using:
```
$ python sens_zwave.py
```
or
```
$ python sens_zwave.py -u
``` 

### Publishing Sensed Value to BuildingDepot
To publish the data of all sensor points on all network nodes to BuildingDepot stack, using following command:
```
$ python sens_zwave.py -r -1
```

Additionally, to publish all sensor points on a specific nodes (specified by node_id) to BuildingDepot stack, using following command:
```
$ python sens_zwave.py -r node_id
``` 

Note: the node id must be a positive integer larger than 2 and if there are no responses, two facts can be the cause:
* The node is not connected into network (perhaps due to accidently power failure or initial zwave product matching);
* The sensed value is not correctly specified. This can refer to the `listen` item in `zwave.json`;

### Sending Command to Switch on Zwave Device
To control zwave device, using following command:
```
$ python sens_zwave.py -w node_id value_label command
``` 

*  node_id is a positive integer larger than 2 specifying the id of the node;
*  value_label indicates the name of particular switch;
*  command is the switch command which includes on/off/toggle;

For example, using following command can activate the Switch1 of node 3:
```
$ python sens_zwave.py -w 3 Switch1 on
```

## Files
The main code files in this repo includes:

*  `zwave/sens_zwave.py`: the device connector program for interfacing with external modules;
*  `zwave/zwave_network.py`: the background zwave network engine for supporting various zwave oprations;
*  `zwave/check.py`: a debugging tool used to do final check on zwave network configurations and device pairing;
*  `zwave/find_port.sh`: run this script to check the file path of USB port of zwave hub controller (zwave stick);
*  `config/zwave.json`: configuration file which need be put in `/Connectors/config/` directory;
*  `openzwave/`: the library repo copied from `python-openzwave`;

## Configurations
### Library
The `python-openzwave` library is needed for this program, make sure to install it according to write-up available at <a href="https://github.com/OpenZWave/python-openzwave"> here; </a>

### Add Python Search Path to Sudoers
As the program is needed to run using super user permission. A copy of python search path need be added to `/etc/sudoers` config file.

In specific, add ` env_keep += "PYTHONPATH" `to ` /etc/sudoers `;

### File Directories

*  Put `zwave.json` in the directory of ` /Connectors/config/ `;
*  Make a copy of `/python-openzwave/openzwave` to `/Connectors/openzwave/`;

## Arguments

For read mode [-r], 2 arguments are required, indicating the start node (inclusive) and end node(exclusive). If both arguments are -1, then all nodes in hosted network will be scanned! For another the `sens_zwave_l.py` only has on arg [-r].

<b>[Examples]</b><br>
* ` sudo python sens_zwave.py -r -1 -1 ` indicates read all nodes in hosted network;
* ` sens_zwave.py -r 2 3 ` indicates read node 2 in hosted network;
* ` sens_zwave.py -r 1 3 ` indicates read node 1 to 2 in hosted network; 
* ` sens_zwave_l.py -r` the `zwave.json` defines which values of which nodes need be listened; 

## Getting Started

*  After pairing the zwave stick and zwave node device, plug zwave stick into the usb port of host. This step enable zwave stick to create a zwave mesh network;
*  Run `sudo bash find_port.sh` to find the file path of zwave stick, which is normally in the format of `/dev/ttyACM<x>;`;
*  Modify the value of `device` in `/Connectors/config/zwave.json` according to the value found in previous step;
*  Check the `check` item in `zwave.json` defines the correct nodes and sensor points;
*  Run `sudo python check.py` to make sure the zwave network is fully functioned;
*  Run `sudo python sens_zwave.py [Args]` to connecting zwave devices and BuildingDepot stack. If a 'dead' node is detected, this node will be ignored by connector until the node is correctly connected into network;

<i>
Dead Node: A node is loose connection with network intentionally or accidently, which, for instance, may be caused by accidently power outage etc.</i>

## Notes: Units of sensed data retrived from Multisensor6:

* Temperature: F
* Humidity: %
* Luminance: Lux
* Ultraviolet: None Unit
* Bulgary Alarm: None Unit

<hr/>
<i> updated on Monday, 10 January, 2017 </i>


