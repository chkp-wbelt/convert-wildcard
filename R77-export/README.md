# wildcard-object
Check Point management script to export R77 wildcard objects

## Instructions

### Script setup
1. ssh into R77.30 management server
1. enter expert mode
1. copy file [wildcard-object.py](https://raw.githubusercontent.com/chkp-wbelt/convert-wildcard/master/R77-export/wildcard-object.py) to /home/admin/ on R77.30 management server
   ```
   curl_cli -k https://raw.githubusercontent.com/chkp-wbelt/convert-wildcard/master/R77-export/wildcard-object.py > /home/admin/wildcard-object.py
   ```
1. chmod the script to be executable
   ```
   chmod u+x /home/admin/wildcard-object.py
   ```
1. edit the whitelist exceptions list on Gaia
   ```
   vi /etc/fw/conf/whitelist
   ```
1. Add the following line to the whitelist
   ```
   p;/home/admin/wildcard-object.py
   ```

### Capture wildcard objects

1. export wildcard objects from objects_5_0.C file to a csv file for use later on R80.20 management server
   ```
   /home/admin/wildcard-object.py export /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C /home/admin/output.csv
   ```
1. convert wildcard objects from objects_5_0.C file to have a netmask of 255.255.255.0 so migrate export/import will work properly
   ```
   /home/admin/wildcard-object.py update /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C /home/admin/objects_5_0.C
   ```
1. chmod new objects_5_0.C file to have same permissions as original objects_5_0.C file
   ```
   chmod --reference=/var/opt/CPsuite-R77/fw1/conf/objects_5_0.C /home/admin/objects_5_0.C
   ```

### Before running migrate export

1. move the original objects_5_0.C file to .original
   ```
   mv /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C.original
   ```
1. move upgraded objects_5_0.C file to be active objects file
   ```
   mv /home/admin/objects_5_0.C /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C
   ```
## Usage
```
usage: wildcard-object.py [-h] {export,update} infile outfile

Wildcard object script v1.0

positional arguments:
  {export,update}  Operation to perform
  infile           Objects file with records to convert
  outfile          Output file
```
