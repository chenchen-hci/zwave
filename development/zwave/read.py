#!/usr/bin/python

import json
import requests
import time
import urllib
import sys
from config.setting import Setting

class ReadTimeData:
    def __init__(self):
        """Initialises the sensor data and client data of the sensors"""
        bdcredentials = Setting("bd_setting")
        self.data = bdcredentials.setting
        self.urlCS = "http://chenc.us:81"
        self.urlDS = "http://chenc.us:82"
        self.header = {}

    def get_oauth_token(self):
        url = self.urlCS + "/oauth/access_token/client_id=" + self.data['client_id'] + \
              "/client_secret=" + self.data['client_key']

        response = requests.get(url, verify=False).json()
        self.oauth_token = response['access_token']
        self.header = {"Authorization": "bearer " + self.oauth_token, 'content-type': 'application/json'}

    def get_time_series_data(self, uuid, start, end):
    	url = self.urlDS + "/sensor/" + uuid + "/timeseries?start_time="+str(start)+"&end_time="+str(end)
        response = requests.get(url, headers=self.header, verify=False)
        return response

def main(arguments):
	obj = ReadTimeData()
	obj.get_oauth_token
	response = obj.get_time_series_data(arguments[1], 1483574400, 148399200)
	print("-------------response-------------------")
	print(response)


if __name__=="__main__":
	main(sys.argv)
