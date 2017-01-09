# ZWave Device Connector 
Zwave device connector for BuildingDepotV3.5 [work in progress! :tada:]

## Files
The code file in this repo includes:

*  `sens_zwave.py`: the main device connector program;
*  `check_match.py`: a debugging tool used to do final check on zwave network configurations and device pairing;
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


## Getting Started

*  After pairing the zwave stick and zwave node device, plug zwave stick into the usb port of host. This step enable zwave stick to create a zwave mesh network;
*  Run `sudo bash find_port.sh` to find the file path of zwave stick, which is normally in the format of `/dev/ttyACM&lt;x&gt;`;
*  Modify the value of `device` in `/Connectors/config/zwave.json` according to the value found in previous step;
*  Run `sudo python check_match.py` to make sure the zwave network is fully functioned;
*  Run `sudo python sens_zwave.py` to connecting zwave devices and BuildingDepot stack;


<hr/>
<i> updated on Sunday, 8 January, 2017 </i>


