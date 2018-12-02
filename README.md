# convert-wildcard

## Overview

Check Point management API script to migrate R77.30 wildcard objects to R80.20 compatible objects and rules

* R77-export/wildcard-object python script is used to create a [Wildcard object CSV](#wildcard-object-csv) file from a R77 management server objects_5_0.C
  * Extract all current wildcard object information from objects.C
  * Prepare objects.C for migrate export to R80 (update netmask for each wildcard object to a valid netmask)

* convert-wildcard python script is used to load data from a [Wildcard object CSV](#wildcard-object-csv) file into an [R80.20 management server](https://supportcenter.checkpoint.com/supportcenter/portal?eventSubmit_doGoviewsolutiondetails=&solutionid=sk122485)
  * Rename old R77 network object to a temporary name
  * Create R80.20 version wildcard objects from [Wildcard object CSV](#wildcard-object-csv) information
  * Replace references in rulebase to old R77 network object with new [R80.20 wildcard object](https://sc1.checkpoint.com/documents/latest/APIs/index.html#web/show-wildcard~v1.3)

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
```
## Examples
* Minimal
  ```bash
  convert-wildcard.py -i output.csv -s https://mgmt1.example.com/
  ```
* Complete
  ```bash
  convert-wildcard.py --input output.csv --server https://mgmt1.example.com/ --user apiuser --password apipw --domain "My Domain"
  ```