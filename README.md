# ZWave Device Connector 
Zwave device connector for BuildingDepotV3.5 [work in progress! :tada:]

## Files
The code file in this repo includes:
<ul>
	<li><b>sens_zwave.py:</b> the main device connector program;</li>
        <li><b>check_match.py:</b> a debugging tool used to do final check on zwave network configurations and device pairing;</li>
        <li><b>find_port.sh:</b> run this script to check the file path of USB port of zwave hub controller (zwave stick);</li>
        <li><b>zwave.json: </b> configuration file which need be put in '/Connectors/config/' directory;
</ul>

## Configurations
### Library
The '''python-openzwave''' library is needed for this program, make sure to install it according to write-up available at <a href="https://github.com/OpenZWave/python-openzwave"> here; </a>

### Add Python Search Path to Sudoers
As the program is needed to run using super user permission. A copy of python search path need be added to '''/etc/sudoers''' config file.

In specific, add ''' env_keep += "PYTHONPATH" ''' to ''' /etc/sudoers ''';

### File Directories
<ul>
	<li>Put '''zwave.json''' in the directory of ''' /Connectors/config/ ''';</li>
	<li>Make a copy of '''/python-openzwave/openzwave''' to '''/Connectors/openzwave/''';</li>
</ul>

## Getting Started
<ul>
	<li>After pairing the zwave stick and zwave node device, plug zwave stick into the usb port of host. This step enable zwave stick to create a zwave mesh network; </li>
	<li>Run '''sudo bash find_port.sh''' to find the file path of zwave stick, which is normally in the format of '''/dev/ttyACM&lt;x&gt;'''; </li>
	<li>Modify the value of '''device''' in '''/Connectors/config/zwave.json''' according to the value found in previous step; </li>
	<li>Run '''sudo python check_match.py''' to make sure the zwave network is fully functioned;</li>
	<li>Run '''sudo python sens_zwave.py''' to connecting zwave devices and BuildingDepot stack;</li>
</ul>

<hr/>
<i> updated on Sunday, 8 January, 2017 </i>


