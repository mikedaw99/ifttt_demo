# import the necessary packages
import argparse
import warnings
import json
import time
import logging
import logging.handlers
import glob
import time
import smtplib
import urllib, urllib2
import subprocess

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

def read_temp_subproc():
    catdata = subprocess.Popen(['cat',device_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = catdata.communicate()
    out_decode = out.decode('utf-8')
    lines = out_decode.split('\n')
    return lines
    
# Split the actual temperature out of the message
def read_temp():
    lines = read_temp_subproc()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_subproc()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c =float(temp_string)/1000.0
        temp_f = temp_c *9.0/5.0+32.0
        return temp_c, temp_f

# Send an IFTTT alert event
def send_notification(temp):
    print("TEMPERATURE WARNING")
    data = urllib.urlencode({'value1' : str(temp)})
    url = BASE_URL + EVENT + '/with/key/' + conf["ifttt_key"]
    response = urllib2.urlopen(url=url, data=data)
    print(response.read())
    
    
# Send Gmail alert
def send_notification_gmail(temp):
    subject="Aquarium Temperature warning"
    body="The temperature is {} (low {} high {}".format(temp,conf["low_alarm_temp"],conf["hight_alarm_temp"])
    user="mikedaw99"
    pwd="app_pwd"
    recipient=[]
    recipient.append("mikedaw99@gmail.com")
    send_email(user, pwd, recipient, subject, body)
    

def send_email(user, pwd, recipient, subject, body):
    gmail_user = user
    gmail_pwd = pwd
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body
    
    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print 'successfully sent the mail'
    except:
        print "failed to send mail"

def send_email_ssl(user, pwd, recipient, subject, body):
     gmail_user = user
     gmail_pwd = pwd
     FROM = user
     TO = recipient if type(recipient) is list else [recipient]
     SUBJECT = subject
     TEXT = body
     
     # Prepare actual message
     message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
     """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
     try:
        server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server_ssl.ehlo() # optional, called by login()
        server_ssl.login(gmail_user, gmail_pwd)  
        # ssl server doesn't support or need tls, so don't call server_ssl.starttls() 
        server_ssl.sendmail(FROM, TO, message)
        #server_ssl.quit()
     except:
        print "failed to send mail"
       

print("Monitoring")
while True:
    temp_c, temp_f = read_temp()
    print "%s Centigrade: %s Fahrenheit" % (temp_c, temp_f)
    if (temp_c < conf["low_alarm_temp"]) or (temp_c > conf["hight_alarm_temp"]):
        send_notification_gmail(temp_c)
        time.sleep(conf["min_t_between_warnings"] * 60)
