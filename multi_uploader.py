# This program serves as an interface with the bulk
# uploader program. It allows one to specify a directory
# containing multiple osm files and have them all uploaded at
# once. Please use this program carefully and reach a
# a community consensus before massive imports.
# ~ingalls

import os

print "OSM Multi-Uploader v0.1"
print "Please make sure that you know what you are doing..."
print "Directory (Press enter for current)"
fileLoc = raw_input(":")

if fileLoc <> "": 
	os.chdir(fileLoc) #change to user specified directory

print "Username"
username = raw_input(":")

print "Password"
password = raw_input(":")

print "Changeset Comment"
comment = raw_input(":")

# TODO poll array to find out how many files are to be uploaded and inform user.
print "\nAre you sure you wish to continue?"
check = raw_input("type 'yes' to continue \n:")
if check != "yes":
	exit()

fileList = list() #Declares variable

for files in os.listdir("."): #Files in current directory
    if files.endswith(".osm"):
        fileList.append(files) #Store files in list

listNum = len(fileList) #returns number of osm files
listNum = listNum - 1 #Fixes for 0th element

while listNum >= 0:
	print "--- Converting: " + fileList[listNum] + "---"
	os.system("python3 osm2change.py " + fileList[listNum])
	newFile = fileList[listNum].replace(".osm", ".osc")
	
	#Warning - I'm playing around with this
	fileSize = int(os.path.getsize(newFile) * 0.000976562) #gets size in B, converts to kB, rounds to int.
	print fileSize
	
	#TODO Add split code here
	
	#TODO Add diff code here
	
	 os.system("python3 upload.py -u " + username + " -p " + password + " -m \"" + comment + "\" -t -c yes " + newFile )
	listNum = listNum - 1
