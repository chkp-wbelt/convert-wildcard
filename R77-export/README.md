# wildcard-object
Check Point management script to export R77 wildcard objects

## Usage
```
usage: wildcard-object.py [-h] {export,update} infile outfile

Wildcard object script v1.0

positional arguments:
  {export,update}  Operation to perform
  infile           Objects file with records to convert
  outfile          Output file
```
## Instructions

### Script setup
1. copy file wildcard-object.py to /home/admin/ on R77.30 management server
2. ssh into R77.30 management server
3. enter expert mode
4. run dos2unix command to ensure script is formatted properly
```
dos2unix /home/admin/wildcard-object.py
```
5. chmod the script to be executable
```
chmod u+x /home/admin/wildcard-object.py
```
6. edit the whitelist exceptions list on Gaia
```
vi /etc/fw/conf/whitelist
```
7. Add the following line to the whitelist
```
p;/home/admin/wildcard-object.py
```

### Capture wildcard objects

1. export wildcard objects from objects_5_0.C file to a csv file for use later on R80.20 management server
```
/home/admin/wildcard-object.py export /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C /home/admin/output.csv
```
2. convert wildcard objects from objects_5_0.C file to have a netmask of 255.255.255.0 so migrate export/import will work properly
```
/home/admin/wildcard-object.py update /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C /home/admin/objects_5_0.C
```
3. chmod new objects_5_0.C file to have same permissions as original objects_5_0.C file
```
chmod --reference=/var/opt/CPsuite-R77/fw1/conf/objects_5_0.C /home/admin/objects_5_0.C
```

### Before running migrate export

1. move the original objects_5_0.C file to .original
```
mv /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C.original
```
2. move upgraded objects_5_0.C file to be active objects file
```
mv /home/admin/objects_5_0.C /var/opt/CPsuite-R77/fw1/conf/objects_5_0.C
```