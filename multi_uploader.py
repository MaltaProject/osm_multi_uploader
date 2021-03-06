#LISCENSE
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#INTRODUCTION
# This program serves as an interface with the bulk
# uploader program. It allows one to specify a directory
# containing multiple osm files and have them all uploaded at
# once. Please use this program carefully and reach a
# a community consensus before massive imports.
# ~ingalls

#REQUIREMENTS
# Python2
# Python3
# Perl

import os
import shutil
import sys


rootLoc = os.getcwd()
version = "0.2"
fileLoc = ""
username = ""
password = ""
comment = ""
num = 0
liveServer = False
resume = False

if len(sys.argv) == 1:
	print "OSM MultiUploader"
	print "-----"
	print "-u <username>"
	print "-p <password>"
	print "-c <changeset comment>"
	print "-d <upload directory> "
	print "-----"
	print "-m (Prompt for values)"
	print "-l (Upload to live server)"
	print "   Defaults to test server"
	print "-r (Skip processing stage)"
	print "   Use only if an upload was"
	print "   halted."
	sys.exit(1)
	
print "OSM Multi-Uploader " + version

allArgs = str(sys.argv)
print allArgs

if allArgs.find("-m") == -1:
    while num < len(sys.argv)-2:
        num += 1
        arg = sys.argv[num]
        if arg == "-u":
            num += 1
            username = sys.argv[num]
        elif arg == "-p":
            num += 1
            password =sys.argv[num]
        elif arg == "-d":
            num += 1
            fileLoc = sys.argv[num]
        elif arg == "-c":
            num += 1
            comment = sys.argv[num]
        elif arg == "-l":
            num += 1
            liveServer = True
        elif arg == "-r":
            num += 1
            resume = True

if fileLoc == "" and resume == False:
	print "Enter Directory (Press enter for current)"
	fileLoc = raw_input(":")

if username == "":
	print "Enter Username"
	username = raw_input(":")

if password == "":
	print "Enter Password"
	password = raw_input(":")

if comment == "":
	print "Enter Changeset Comment"
	comment = raw_input(":")

if fileLoc <> ".":
	fileLoc = rootLoc + fileLoc
else:
	fileLoc = rootLoc

print "\n\n\n"
print "Username: " + username
print "Password: " + password
print "Comment: " + comment

if liveServer == True:
    print "Server: LIVE"
else:
    print "Server: TEST"


print "\nAre you sure you wish to continue?"
check = raw_input("type 'yes' to continue \n:")
if check != "yes":
	exit()

print "Go get a beer. I've got this now!"

if resume == False:
    #Creates various directories used during the upload
    if not os.path.exists(rootLoc + "/conversions"): #stores osc files
        os.makedirs(rootLoc + "/conversions")
    if not os.path.exists(rootLoc + "/splits"): #stores split files
        os.makedirs(rootLoc + "/splits")
    if not os.path.exists(rootLoc + "/completed"): #stores sucessfully uploaded splits
        os.makedirs(rootLoc + "/completed") 

    osmList = list() #stores list of osm files to be split
    splits = list()

    for files in os.listdir(fileLoc): #Gets a list of osm files
        if files.endswith(".osm"):
            osmList.append(files) #Store files in list
    listNum = len(osmList) #returns number of osm files
    listNum = listNum - 1 #Fixes for 0th element

    while listNum >= 0:
       print "---Converting: " + fileLoc + "/" + osmList[listNum] + "---"
       os.system("python3 osm2change.py " + fileLoc + "/" + osmList[listNum])
       newFile = osmList[listNum].replace(".osm", ".osc")
       print "   Moving to /conversions"
       os.rename(fileLoc + "/" + newFile, rootLoc + "/conversions/" + newFile)
       newFile = rootLoc + "/conversions/" + newFile
    
       print "---Splitting: " + newFile
       os.system("python osmsplit.py --outputDir " + rootLoc + "/splits --maxElements 3000 " + newFile)
       os.rename(newFile, newFile + ".old")
	
       for files in os.listdir(rootLoc + "/conversions"): #Regenerate list of osc files with newly generated splits
          if files.endswith(".osc"):
               splits.append(files) #Store files in list
       listNumber = len(splits) #returns number of osm files
       listNumber -= 1 #Fixes for 0th element
	        
       listNum -= 1

splitList = list()

for files in os.listdir(rootLoc + "/splits"): #Gets a list of osm files
    if files.endswith(".osc"):
        splitList.append(files) #Store files in list
listNum = len(splitList) #returns number of osm files
listNum = listNum - 1 #Fixes for 0th element
fileNum = listNum

while listNum >= 0:

    if liveServer == True:
        server = "--server live"
    elif liveServer == False:
        server = "--server test"
    

    print "---Uploading: " + rootLoc + "/splits/" + splitList[listNum] + "---"
    os.system("python3 upload.py " + server + " -u " + username + " -p " + password + " -m \"" + comment + "\" -t " + rootLoc + "/splits/" + splitList[listNum] )
    
    

    
    if os.path.exists(rootLoc + "/logFile") == True: #Logfile will not exist if upload is successful
        f = open('logFile', 'r')
        error = f.readline()
        f.close()
        if os.path.exists(rootLoc + "/currentChange") == True:
            f = open("currentChange",'r')
            changeset = f.readline()
            f.close()
        else:
            changeset = "(Did not open)"
        print "Damn it! I'm an upload script not a mechanic\n"
        print "Error: " + error + " while uploading changeset " + changeset
        print "Clean up after your mess!"
        print "Use the JOSM reverter plugin to remove the changeset (if any)"
        print "Then use the -r arg. to resume the upload from where it left off"
        print "(Before resuming, delete logFile!!!)"
        
        sys.exit(1)
    else: #Probably a success
        print "   Upload Sucessful!"
    
    #Error handling code here.
    os.rename(rootLoc + "/splits/" + splitList[listNum], rootLoc + "/completed/" + splitList[listNum])
    
    listNum -= 1
