This project contains all of the source code of the MA OSM building import project. 

The upload directory contains:

a python wrapper around the bulk_upload.py script. This script will take a directory of .osm files and route them through the bulk_upload.py script. The script will handle breaking large files up into uploads that will fit into a single change set, and will robustly handle errors in the upload.


Please ensure that all bulk_upload.py dependancies are installed before using.
No arguments are requred, simply run 'python multi_upload.py' and the script will guide you through the process.

The createosm directory contains:

The scripts that were used to create the source osm files. 

