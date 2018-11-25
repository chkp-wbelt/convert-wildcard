# convert-wildcard
Check Point management API script to migrate R77.30 wildcard objects to R80.20 compatible objects and rules

## Usage
```
usage: convert-wildcard.py [-h] -i INPUT -s SERVER [-u USER] [-p PASSWORD]

required arguments:
  -i INPUT, --input INPUT
                        Input file with records to convert
  -s SERVER, --server SERVER
                        Server URL for management server

optional arguments:
  -u USER, --user USER  Username to access the API
  -p PASSWORD, --password PASSWORD
                        Password to access the API
```
## Examples

### Minimal
```
convert-wildcard.py -i output.csv -s https://mgmt1.example.com/
```
### Complete
```
convert-wildcard.py --input output.csv --server https://mgmt1.example.com/ --user apiuser --password apipw
```