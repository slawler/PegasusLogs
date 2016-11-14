'''
PyScheduler.py

Notes:
1. Compatible with python v2 & v3
2. Need to test wifi on/off 
3. Issues with ssh key identification persist after reboot
4. Try/Except: add socket errors due to connection
5. Add email notifications for errors

as of nov2016.12
'''
#---Load Modules
from __future__ import print_function
import os
import glob
import time
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime 
import time
import schedule
import subprocess
import html5lib


#---Assign directories & filename
log_dir = '/home/pi/PegasusLogs/Temperature'
log_file = 'Temperature.log'
log = os.path.join(log_dir,log_file)

base_dir='/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28*')
print(device_folders)

#---Sensor ID's
device_table={#determined by physical check of each labelled probe
"0416807DF3FF" : "01",
"05168031B4FF" : "02",
"0516802F91FF" : "03",
"041684199FFF" : "04",
"0416841B3BFF" : "05",
"0516858720FF" : "06",
"0516858803FF" : "07",
"0416807FF4FF" : "08"}

#---Set Logging Parameters
sample_rate = 5  #minutes
logger_rate = 60  #minutes

#---Mandatory when using multiple sensors
os.system('modprobe w1-gpio') 
time.sleep(2.0)
os.system('modprobe w1-therm')
time.sleep(2.0)

#---Sensor Communication Functions 
def sort_key(address): # used by setup_read to sort the devices
    return device_table[address.upper()]

def setup_read():
    devices = []
    for d in device_folders:
        devadd = d[-12:].upper()
        print("\nReading From Device: ", devadd)
        if devadd in device_table:
            devices.append(devadd)
    return(sorted(devices, key=sort_key))

def read_temp_raw(device):
    filename = base_dir + '28-' + device.lower() + '/w1_slave'
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(d):
    lines = read_temp_raw(d)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        read_temp_raw(d)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string)/1000.0
        temp_f = 32.0 + 1.8 * temp_c
        return temp_c, temp_f

devices = setup_read()

'''
print("  # address\n---------------")
for d in devices:
    print(" " + device_table[d.upper()] + " " + d)
print(" ",end="")

for d in devices:
    print('{:s}'.format(" " + device_table[d.upper()]+ " |"),end="")
print("\n"+len(devices)*"-----")
'''

#---Delete all scheduled jobs
schedule.clear()

#---Sampling function: Record data to log  
def LogData():
    dtm  = datetime.now().strftime(format = '%d.%Y.%m %H:%M:%S')
    with open(log,'a') as f:
        for d in devices:
            temps = read_temp(d)
            #print('{:4.1f}|'.format(temps[0]),end="")
            d_id = str(device_table[d.upper()])
            f.write(dtm + '\t' +d_id + '\t'+ '{}'.format(temps[0])+ '\n')   
'''
def WiFi_On():
	print('Turning on WiFi')
	cmd = 'sudo ifup wlan0'
	os.system(cmd)
	print('Wireless Up and Running')


def WiFi_Off():
	print('Turning off WiFi')
	cmd = 'sudo ifdown wlan0'
	os.system(cmd)
	print('Wireless Down')
'''
#---Logging funciton: Create Plot, Push updates to remote    
def GitPush():
    try:
        print("Activating WiFi")      
        #WiFi_On()
        #time.sleep(60)
        print("Updating Tabular data on Github")
        os.system('/home/pi/UpdateGit.sh')
        print("\n...Creating Plots\n")
        url = 'https://raw.githubusercontent.com/slawler/PegasusLogs/master/Temperature/Temperature.log'
        cols = ['time','sensor', 'obs']
        df= pd.read_csv(url, header = None, sep = '\t' ,names = cols)
        df= df.set_index(pd.to_datetime(df['time'],format = '%d.%Y.%m %H:%M:%S'))
        df.drop(labels='time',axis=1, inplace= True)
        df = df.groupby([pd.TimeGrouper('{}min'.format(1)), 'sensor']).agg({'obs': np.mean})
        df = df.unstack()
        df.columns = df.columns.droplevel()
            

        #---Plot data from most recent log
        plt.ioff()
        fig = df.plot()
        plt.title('Pegasus Temperature Log'+ '\n Begining {}'.format(df.index[0]))
        plt.ylabel('Temperature (C)')
        plt.xlabel('Time')
        plt.grid(True)
        plt.ylim((0,30))

        plt.savefig('/home/pi/PegasusLogs/Temperature/temp.png')
        plt.close()
        print("Updating Plots for Webpage")
        os.system('/home/pi/UpdateGit.sh')
        #time.sleep(60)
        #WiFi_Off()
    except:
        print("ERROR")
        
    return('') 

#---Update Console 
def Print2Console():
    dtm2  = datetime.now().strftime(format = '%d.%Y.%m %H:%M:%S')
    print('Program Active: ', dtm2)

'''
#---Run Git Push at logon
try:
    time.sleep(1) #allow time for wifi connection
    GitPush()
except:
    print('Error at initial git push')
'''
    
#---Initialize Scheduler to call jobs
#schedule.every(sample_rate).minutes.do(LogData)
schedule.every(sample_rate).seconds.do(LogData) #For Testing\Debugging


#schedule.every(logger_rate).minutes.do(GitPush)
schedule.every(logger_rate).seconds.do(GitPush) #For Testing\Debugging

schedule.every(10).seconds.do(Print2Console)

#---Run Jobs
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
        print(" ",end="\r")

        
    except KeyboardInterrupt:
        print('Process Terminated')
        break
    

