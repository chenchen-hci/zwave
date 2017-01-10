# ZWave Device Connector 
Zwave device connector for BuildingDepotV3.5 [work in progress! :tada:]

## Files
The code file in this repo includes:

*  `sens_zwave.py`: the main device connector program;
*  `match.py`: a debugging tool used to do final check on zwave network configurations and device pairing;
*  `find_port.sh`: run this script to check the file path of USB port of zwave hub controller (zwave stick);
*  `zwave.json`: configuration file which need be put in `/Connectors/config/` directory;

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

For read mode [-r], 2 arguments are required, indicating the start node (inclusive) and end node(exclusive). If both arguments are -1, then all nodes in hosted network will be scanned! 

<b>[Examples]</b><br>
* ` sudo python sens_zwave.py -r -1 -1 ` indicates read all nodes in hosted network;
* ` sens_zwave.py -r 2 3 ` indicates read node 2 in hosted network;
* ` sens_zwave.py -r 1 3 ` indicates read node 1 to 2 in hosted network; 

## Getting Started

*  After pairing the zwave stick and zwave node device, plug zwave stick into the usb port of host. This step enable zwave stick to create a zwave mesh network;
*  Run `sudo bash find_port.sh` to find the file path of zwave stick, which is normally in the format of `/dev/ttyACM<x>;`;
*  Modify the value of `device` in `/Connectors/config/zwave.json` according to the value found in previous step;
*  Run `sudo python check.py` to make sure the zwave network is fully functioned;
*  Run `sudo python sens_zwave.py [Args]` to connecting zwave devices and BuildingDepot stack. If a 'dead' node is detected, this node will be ignored by connector until the node is correctly connected into network;

<i>Dead Node: A node is loose connection with network intentionally or accidently, which, for instance, may be caused by accidently power outage etc.</i>


<hr/>
<i> updated on Monday, 9 January, 2017 </i>


