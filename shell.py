#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket               # Import socket module
import sys
import time
import string
import random
from config.setting import Setting

CONFIG = "zwave"         # zwave.json file

def get_socket():
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
		host = socket.gethostname()                      # Get local machine name
		port = int(Setting(CONFIG).setting["port"])     # Reserve a port for your service.
		s.connect((host, port))        # Bind to the port
		return s
	except Exception as e:
		sys.exit("Socket Creation Failed\n" + str(e))

def recv_timeout(the_socket, timeout = 2):
    #make socket non blocking
    the_socket.setblocking(0)
    #total data partwise in an array
    total_data=[];
    data='';
    #beginning time
    begin=time.time()
    while True:
        #if you got some data, then break after timeout
        if total_data and time.time()-begin > timeout * 2:
            break
         
        #if you got no data at all, wait a little longer, twice the timeout
        elif time.time()-begin > timeout:
            break
        
        #recv something
        try:
            data = the_socket.recv(1024)
            if data and not data.isspace():
                total_data.append(data)
                #change the beginning time for measurement
                begin = time.time()

        except:
            pass
     
    #join all parts to make final string
    return ''.join(total_data)

def main(arguments):
	s = get_socket()
	cmd = ""
	for arg in arguments[1:]:
		cmd = cmd + arg + " "
	s.send(cmd)
	print(recv_timeout(s))
	s.close()                     # Close the socket when done

if __name__ == "__main__":
	main(sys.argv)