# convert-wildcard

## Overview

Check Point management API script to migrate R77.30 wildcard objects to R80.20 compatible objects and rules

* R77-export/wildcard-object python script is used to create a [Wildcard object CSV](#wildcard-object-csv) file from a R77 management server objects_5_0.C
  * This script is run on your R77.30 MDS 
  * Extract all current wildcard object information from objects_5_0.C
  * Prepare objects_5_0.C for migrate export to R80 (update netmask for each wildcard object to a valid netmask)

* convert-wildcard python script is used to load data from a [Wildcard object CSV](#wildcard-object-csv) file into an [R80.20 management server](https://supportcenter.checkpoint.com/supportcenter/portal?eventSubmit_doGoviewsolutiondetails=&solutionid=sk122485)
  * This script can be run from any machine with Python and API access to the R80.20 MDS
  * Rename old R77 network object to a temporary name
  * Create R80.20 version wildcard objects from [Wildcard object CSV](#wildcard-object-csv) information
  * Replace references in rulebase to old R77 network object with new [R80.20 wildcard object](https://sc1.checkpoint.com/documents/latest/APIs/index.html#web/show-wildcard~v1.3)
  * Requires the [Check Point API SDK](https://github.com/CheckPointSW/cp_mgmt_api_python_sdk/tree/7508cd064ed8737cfc1a7ece55cd817617ff5953) be downloaded and configured correctly

## Wildcard object CSV
* First row of the file is a header row for the following columns:
  * name
  * color
  * comments
  * ipv4-address
  * ipv4-wildcard

* Example CSV
  ```csv
  name,color,comments,ipv4-address,ipv4-mask-wildcard
  Example_VOICE_Server,orange,"Voice Server",10.0.2.11,0.63.248.0
  ```

##Script Setup
1. ssh into R80.20 management server
1. enter expert mode
1. copy file [convert-wildcard.py](https://raw.githubusercontent.com/chkp-wbelt/convert-wildcard/master/convert-wildcard.py) to /home/admin on R80.20 management server
	```bash
	curl_cli -k https://raw.githubusercontent.com/chkp-wbelt/convert-wildcard/master/convert-wildcard.py > /home/admin/convert-wildcard.py
	```
1. chmod the script to be executable
	```bash
	chmod u+x /home/admin/convert-wildcard.py
	```

## Usage
```
usage: convert-wildcard.py [-h] -i INPUT -s SERVER [-u USER] [-p PASSWORD] [-d DOMAIN]

required arguments:
  -i INPUT, --input INPUT
                        Input file with records to convert
  -s SERVER, --server SERVER
                        Server URL for management server

optional arguments:
  -u USER, --user USER  Username to access the API
  -p PASSWORD, --password PASSWORD
                        Password to access the API
  -d DOMAIN, --domain DOMAIN
                        Domain (when using multidomain)
                        Global - the literal domain name for where global objects are stored (then reassign the global policy)
```
## Examples
* Minimal
  ```bash
  convert-wildcard.py -i output.csv -s mgmt1.example.com
  ```
  ```
  convert-wildcard.py -i output.csv -s 192.168.10.10
  ```
* Complete
  ```bash
  convert-wildcard.py --input output.csv --server mgmt1.example.com --user apiuser --password apipw --domain "My Domain"
  ```
  ```bash
  convert-wildcard.py --input output.csv --server 192.168.10.10 --user apiuser --password apipw --domain "My Domain"
  ```