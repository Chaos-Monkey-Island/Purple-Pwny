import nmap
import socket
import struct
import os
import ipaddress
import re
import random, string
from ftplib import FTP
from datetime import datetime
import netifaces
import platform

startTime = datetime.now()

# Generates a text-file with a random name
# Open file for writing our output and create if its not created already - random name will make it always create
rand_file = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randrange(5,9))) + ".txt"
f = open(rand_file,"a+")

# get host IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
	# doesn't even have to be reachable
	s.connect(('10.255.255.255', 1))
	IP = s.getsockname()[0]
except:
	IP = '127.0.0.1'
finally:
	s.close()

# get OS platform for deciding code to run later if needed
operatingSystem = platform.system()
nm = nmap.PortScanner()

f.write('Begin Script @ {0} \n\n'.format(startTime))
f.write('------ Your Host ------\n')
f.write('Host IP: {0} \n'.format(IP))

# Cross Platform way to get the following info but uses 2 imports
for i in netifaces.interfaces():
   try:
      if netifaces.ifaddresses(i)[netifaces.AF_INET][0]['addr'].startswith("192") or netifaces.ifaddresses(i)[netifaces.AF_INET][0]['addr'].startswith("10") or netifaces.ifaddresses(i)[netifaces.AF_INET][0]['addr'].startswith("172"):
         f.write("Operating System: {0} \n".format(platform.system()))
         netmask = netifaces.ifaddresses(i)[netifaces.AF_INET][0]['netmask']
         f.write("Network Mask: {0} \n".format(netmask))
         f.write("Gateway IP: {0} \n".format(netifaces.gateways()['default'][netifaces.AF_INET][0]))
         break
      else:
         pass
   except:pass

# Creates an ipaddress object that is used to hold all of the IPs on the subnet
subnet = ipaddress.ip_network(u'{0}/{1}'.format(IP, netmask),strict=False)

print(subnet)
# Just a prompt for the output file
f.write('\nInitiating quick scan from host {0} to {1} \n'.format(subnet[0], subnet[-1]))

######## NMAP STUFF ########
nm.scan(hosts=str(subnet), arguments='-O -sV --script vulners')
hostsCount = len(nm.all_hosts())
hostObjects = []
f.write("Count of alive hosts: {0}".format(hostsCount))
f2 = open("IPList.txt","a+")
f2.write('\n'.join(map(str,nm.all_hosts())))
f2.close()
for host in nm.all_hosts():
	cveCount = 0 # get len(tabs) / 3 for each port and add to cveCount
	hostCVEAvg = [] # get weighted average for each port and append to this list
	hostCVEScore = 0 # weighted average of hostCVEAvg
	f.write("\n\nResults for IP: {0}\n".format(host))
	try:
		OS = nm[host]['osmatch'][0]['name']
		f.write("OS: {0}\n".format(OS))
	except:
		f.write("OS: Not Found\n")
	try:
		f.write("Port    Service                  Details \n")
		for port in nm[host]['tcp'].keys():
			service = str(port).ljust(8," ") + nm[host]['tcp'][port]['name'].ljust(25, " ") + nm[host]['tcp'][port]['product'] + " " + nm[host]['tcp'][port]['version']
			f.write(service + '\n')
			try:
				#--------- Gets score (as float) of each CVE only ---------#
				tabs = []
				cveScoreList = []
				start = 1
				for m in re.finditer('\t', nm[host]['tcp'][port]['script']['vulners']):
					tabs.append(m.start())
				cveCount = cveCount + (len(tabs) / 3)
				while start <= len(tabs)-2:
					cveScoreList.append(float(nm[host]['tcp'][port]['script']['vulners'][tabs[start]+1:tabs[start+1]]))
					start += 3
				#--- Gets weighted avg. CVE score for this service ---#
				numerator = 0
				denominator = sum(cveScoreList)
				for score in cveScoreList:
					numerator = numerator + (score * score)
				serviceAvgScore = numerator / denominator
				hostCVEAvg.append(serviceAvgScore)
			except:
				pass
			# try:
			# 	f.write(nm[host]['tcp'][port]['script']['vulners'] + '\n')
			# except:
			# 	pass
	except:
		pass
	#-- Weighted avg. of CVEs for host --#
	if len(hostCVEAvg) > 0:
		hostNumerator = 0
		hostDenominator = sum(hostCVEAvg)
		for average in hostCVEAvg:
			hostNumerator = hostNumerator + (average * average)
		hostCVEScore = hostNumerator / hostDenominator
	else:
		pass
	thisHost = {"IP":host,"CVEScore":hostCVEScore, "CVECount":cveCount}
	hostObjects.append(thisHost)
	f.write("Host statistics: {0}\n".format(thisHost))

"""
nc['10.0.0.42']['tcp'][80]['script']['vulners']
print(nm['192.168.1.1']['addresses']['mac'])
## gets OS possibilities (a list of dictionaries) ##
##### it looks like the first dictionary returned has the highest #####
##### 'accuracy' value however example I ran the first one was wrong... #####
nm['10.0.0.42']['osmatch']
## prints all details for a particular OS name including accuracy etc
next(item for item in nm['10.0.0.42']['osmatch'] if item['name'] == 'Microsoft Windows 10 1607')
## prints value associated with key (here its 'name') for a paricular OS name
next(item['name'] for item in nm['10.0.0.42']['osmatch'] if item['name'] == 'Microsoft Windows 10 1607')
# get all open ports
nm['10.0.0.42']['tcp'].keys()
# save and then print all services on different lines
services = [nm['10.0.0.42']['tcp'][item]['name'] for item in nm['10.0.0.42']['tcp'].keys()]
print('\n'.join(map(str, services)))
# get service running on port
nm['10.0.0.42']['tcp'][135]['name']
# get version of service of applicable
nm['10.0.0.42']['tcp'][135]['product'] + nm['10.0.0.42']['tcp'][135]['version']
# prints all services
print([nm['10.0.0.42']['tcp'][item]['name'] for item in nm['10.0.0.42']['tcp'].keys()])
"""

endTime = datetime.now()
runtime = endTime-startTime
f.write('\n\n End Script @ {0}    ---   Total Runtime: {1}'.format(endTime, runtime))
f.close()
