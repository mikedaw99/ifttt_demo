# import the necessary packages
import argparse
import warnings
import json
import time
import logging
import logging.handlers
import glob
import time
import urllib, urllib2

# create logger'
logger = logging.getLogger('home_security')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('home_security.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
help="path to the JSON configuration file")
args = vars(ap.parse_args())

# filter warnings, load the configuration
# client
warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))

EVENT = 'aquarium_alert'
BASE_URL = 'https://maker.ifttt.com/trigger/'

# These constants used by the 1-wire device
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# Read the temperature message from the device file
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
    
# Split the actual temperature out of the message
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

# Send an IFTTT alert event
def send_notification(temp):
    print("TEMPERATURE WARNING")
    data = urllib.urlencode({'value1' : str(temp)})
    url = BASE_URL + EVENT + '/with/key/' + conf["ifttt_key"]
    response = urllib2.urlopen(url=url, data=data)
    print(response.read())


print("Monitoring")
while True:
    temp = read_temp()
    print(temp)
    if (temp < conf["low_alarm_temp"]) or (temp > conf["hight_alarm_temp]):
        send_notification(temp)
        time.sleep(conf["min_t_between_warnings"] * 60)
