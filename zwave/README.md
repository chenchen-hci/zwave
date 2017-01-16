# Essential Guide Information Adapted From Main Page Documentations

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
*  `zwave/post_bd.py`: a modified version of original `bd_connect.py` module;
*  `zwave/find_port.sh`: run this script to check the file path of USB port of zwave hub controller (zwave stick);
*  `config/zwave.json`: configuration file which need be put in `/Connectors/config/` directory;
*  `openzwave/`: the library repo copied from `python-openzwave`;

<hr>
<i>Updated on Monday 16 January, 2017</i>
