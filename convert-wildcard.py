"""Script to migrate R77.30 network objects to R80.20 native wildcard objects."""
import sys
import requests
import json
import csv
import urllib3
import argparse
import getpass
from time import sleep
from urlparse import urljoin

__version__ = "1.0"

class APIException(Exception):
    """Exception raised when API response is abnormal."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
    
    def __str__(self):
        return("{}: {}".format(self.code,self.message))

class APIVariables():
    def __init__(self):
        self.managmentURL = ""
        self.chkpSID = ""
        self.sessionUID = ""
        self.sessionHeaders = {}
        self.sessionHeaders['Content-Type'] = 'application/json'
        self.sessionHeaders['cache-control'] = 'no-cache'
        
apivars = APIVariables()
def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Widlcard import/rule conversion script v" + __version__)
    print ("*** ")
    print ("*** " + parser.description)
    print ("*** ")
    parser.add_argument("-s", "--server", required=True, action="store", help="Server URL used to access the management server")
    parser.add_argument("-u", "--user", action="store", help="Username used to access the API")
    parser.add_argument("-p", "--password", action="store", help="Password (for Usernamed) to access the API")
    args = parser.parse_args()
    
    apivars.managmentURL = args.server
    print ("Connecting to server at {}".format(apivars.managmentURL))
    if not args.user:
        args.user = raw_input('Username: ').strip('\r')
    else:
        print ("Attempting to login as '{}'".format(args.user))

    if not args.password:
        args.password = getpass.getpass(stream=sys.stderr).strip('\r')
    urllib3.disable_warnings()
    #Login to management server
    try:
        params = {}
        params["user"] = args.user
        params["password"] = args.password
        response = mgmtreq('login', params)

        if response["api-server-version"]:
            apiversion = response["api-server-version"]
            if float(apiversion) < 1.3:
                raise (APIException(409,"Server API needs to be version 1.3 or greater '{}' returned from login.".format(apiversion)))
            print ("--- Login to management via API {} complete. (session-uid: {})".format(apiversion,apivars.sessionUID))
    except APIException as apie:
        print ("--- Login failed! {}".format(apie))
        sys.exit(1)

    #Parse CSV for records
    records = getRecords()

    #Loop through each record.  Rename existing objects and replace references with new object
    if len(records) > 0:
        print ('--- Parse CSV complete. ({} records found for processing)'.format(len(records)))
        suffix = {}
        suffix["R77"] = "_R77"
        suffix["R80"] = "_WC"
        for record in records:
            print ('--- Working with record {} (color:{} network:{} mask:{})'.format(record['name'],record['color'],record['ipv4-address'],record['ipv4-mask-wildcard']))
            #get uid for network object
            NUID = getNetworkUID(record['name'])
            r77name = record['name'] + suffix["R77"]
            r80name = record['name'] + suffix["R80"]
            if NUID:
                try:
                    print ('    > Found original network object "{}" (uid: {})'.format(record['name'],NUID))
                    mgmtreq('set-network', {'uid': '{}'.format(NUID),'new-name': '{}'.format(r77name)})
                    print ('      > Renamed network object to "{}" (uid: {})'.format(r77name,NUID))
                    NUID = ""
                except APIException as apie:
                    print ('      > Failed to rename network object to "{}" (uid: {}) {}'.format(r77name,NUID,apie))
            if NUID == "":
                NUID = getNetworkUID(r77name)
                if NUID:
                    print ('    > Found R77 network object "{}" (uid: {})'.format(r77name,NUID))
                    #get uid for wildcard object
                    WUID = getWildcardUID(r80name)
                    if WUID:
                        print ('    > Found wildcard object "{}" (uid: {})'.format(r80name,WUID))
                    else:
                        params = {}
                        params["name"] = r80name
                        params["ipv4-address"] = record["ipv4-address"]
                        params["ipv4-mask-wildcard"] = record["ipv4-mask-wildcard"]
                        params["color"] = record["color"]
                        response = mgmtreq('add-wildcard', params)
                        if response["uid"]:
                            WUID = response["uid"]
                            print ('    > Created new wildcard object "{}" (uid: {})'.format(r80name,WUID))
                    replaceWhereUsed(NUID,WUID)
    changes = mgmtchanges()
    if changes > 0:
        print ("--- Found {} changes pending.".format(changes))
        mgmtpublish()
    mgmtlogout()

def replaceWhereUsed(OldID,NewID):
    """Replace all instances of Old ID with New ID in rules."""
    response = mgmtreq('where-used', {'uid': '{}'.format(OldID)})
    for rule in response["used-directly"]["access-control-rules"]:
        params = {}
        params["uid"] = rule["rule"]["uid"]
        params["layer"] = rule["layer"]["uid"]
        params["details-level"] = "uid"
        print ("    > Updating Rule:{} Layer:{}".format(params["uid"],params["layer"]))
        ruledata = mgmtreq('show-access-rule', params)
        sources = 0
        destinations = 0
        params["source"] = ruledata["source"]
        params["destination"] = ruledata["destination"]
        for i, record in enumerate(params["source"]):
            if record == OldID:
                params["source"][i] = NewID
                sources += 1
        for i, record in enumerate(params["destination"]):
            if record == OldID:
                params["destination"][i] = NewID
                destinations += 1
        if sources > 0 or destinations > 0:
            mgmtreq('set-access-rule', params)
            print ("      > Updated {} sources and {} destinations in rule".format(sources,destinations))
            
def getRecords():
    """Read all records to be imported from CSV file."""
    retval = []
    with open('data/output.csv', 'rb') as f:
        reader = csv.DictReader(f)
        for line in reader:
            retval.append(line)
    return (retval)

def getNetworkUID(name):
    """Get UID for standard network object by name."""
    retval = ""
    try:
        data = mgmtreq('show-network', {'name': '{}'.format(name),'details-level': 'uid'})
        if 'uid' in data:
            retval = data['uid']
    except APIException as apie:
        if apie.code == 404:
            retval = ""
        else:
            raise
    return (retval)

def getWildcardUID(name):
    """Get UID for wildcard network object by name."""
    retval = ""
    try:
        data = mgmtreq('show-wildcard',{'name': '{}'.format(name),'details-level': 'uid'})
        if 'uid' in data:
            retval = data['uid']
    except APIException as apie:
        if apie.code == 404:
            retval = ""
        else:
            raise
    return (retval)

def mgmtpublish():
    """Publish all pending changes."""
    try:
        data = mgmtreq('publish', {})
        if data["task-id"]:
            taskID = data["task-id"]
            print ("--- Publish in-progress. (task-id: {})".format(taskID))
            processesing = True
            while processesing:
                data = mgmtreq('show-task',{'task-id': '{}'.format(taskID)})
                processesing = False
                for task in data["tasks"]:
                    if task["status"] == "in progress":
                        processesing = True
                        break
                if processesing:
                    sleep(2)
            print ("--- Publish complete. (task-id: {})".format(taskID))
            
    except APIException as apie:
        print ("--- Publish failed! (ERROR: {})".format(apie.message))

def mgmtchanges():
    """Return number of changes in the current session."""
    retval = 0
    try:
        data = mgmtreq('show-session', {'uid': '{}'.format(apivars.sessionUID)})
        if data["changes"]:
            retval = data["changes"]
    except APIException as apie:
        print ("--- Show session failed! {}".format(apie))
    return (retval)

def mgmtdiscard():
    """Discard any changes in the current session."""
    try:
        data = mgmtreq('discard', {})
        if data["number-of-discarded-changes"]:
            print ("--- Discard complete. ({} changes discarded)".format(data["number-of-discarded-changes"]))
    except APIException as apie:
        print ("--- Discard failed! {}".format(apie))

def mgmtlogout():
    """Return number of changes in the current session."""
    try:
        data = mgmtreq('logout', {})
        if data["message"]:
            print ("--- Logout complete. (message: {})".format(data["message"]))
    except APIException as apie:
        print ("--- Logout failed! {}".format(apie))

def mgmtreq(command, payload):
    """Make a REST API call to management server and return results."""
    apiBaseStem = "/web_api/"
    managementBase = urljoin(apivars.managmentURL,apiBaseStem)

    data = {}
    if command:
        isLogin = False
        apiRequest = urljoin(managementBase,command)
        headers = apivars.sessionHeaders
        if command.lower() == 'login':
            isLogin = True
        if isLogin == False and apivars.chkpSID:
            headers['X-chkp-sid'] = '{}'.format(apivars.chkpSID)
        try:
            response = requests.request("POST", apiRequest, json=payload, headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            raise APIException(522,"Connection to '{}' failed".format(apiRequest))
        if response.status_code == 200:
            if response.text:
                data = json.loads(response.text)
                if isLogin:
                    if data["sid"] and data["uid"]:
                        apivars.chkpSID = data["sid"]
                        apivars.sessionUID = data["uid"]
            else:
                raise APIException(500,"Server returned a status code of 200, but with unexpected data.")
        else:
            if isLogin:
                raise APIException(407,"Authentication for '{}' failed".format(apiRequest))
            else:
                message = "Unknown error"
                if response and response.text:
                    data = json.loads(response.text)
                    if data["code"]:
                        message = data["code"]
                raise APIException(response.status_code,message)
    return data

if __name__ == '__main__':
    main()
