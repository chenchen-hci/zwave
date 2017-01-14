#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket               # Import socket module
import sys

def main(arguments):
	s = socket.socket()         # Create a socket object
	host = socket.gethostname() # Get local machine name
	port = 12345                # Reserve a port for your service.
	arguments = arguments[1:]

	cmd = ""
	for arg in arguments:
		cmd = cmd + arg + " "	

	s.connect((host, port))
	print s.send(cmd)
	if arguments[0] == "-q":
		# resend a dummy signal to exit
		s.close()
		s = socket.socket()         # Create a socket object
		s.connect((host, port))
		print s.send(cmd)
	s.close()                     # Close the socket when done

if __name__ == "__main__":
	main(sys.argv)