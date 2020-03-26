"""Script to migrate R77.30 network objects to R80.20 native wildcard objects."""
import argparse
import csv
import getpass
import os.path
import sys

from cp_mgmt_api_python_sdk.cpapi import APIClient, APIClientArgs

__version__ = "2.0"


class WildcardManager():
    def __init__(self, client):
        self._client = client
        self._suffix = {}
        self._suffix["R77"] = "_R77"
        self._suffix["R80"] = "_WC"

    def convert_rulebase(self, records):
        # Loop through each record.  Rename existing objects and replace references with new object
        if len(records) > 0:
            print '--- Convert found {:,} records for processing'.format(len(records))
            # Create variable to track number of objects
            track = 0
            for record in records:
                track += 1
                print '--- Record {:,} of {:,}.  Working with {} (color:{} network:{} mask:{})'.format(
                    track, len(records), record['name'], record['color'],
                    record['ipv4-address'], record['ipv4-mask-wildcard'])
                # get uid for network object
                NUID = self.get_network_uid(record['name'])
                r77name = record['name'] + self._suffix["R77"]
                r80name = record['name'] + self._suffix["R80"]
                if NUID:
                    print '    > Found original network object "{}" (uid: {})'.format(record['name'], NUID)
                    params = {}
                    params["uid"] = NUID
                    params["new-name"] = r77name
                    response = self._client.api_call("set-network", params)
                    if response.success:
                        print '      > Renamed network object to "{}" (uid: {})'.format(r77name, NUID)
                    else:
                        print '      > Failed to renamed network object to "{}" (Message: {})'.format(
                            r77name, response.error_message)
                    NUID = ""
                if NUID == "":
                    NUID = self.get_network_uid(r77name)
                    if NUID:
                        print '    > Found R77 network object "{}" (uid: {})'.format(r77name, NUID)
                        # get uid for wildcard object
                        WUID = self.get_wildcard_uid(r80name)
                        if WUID:
                            print '    > Found wildcard object "{}" (uid: {})'.format(r80name, WUID)
                        else:
                            params = {}
                            params["name"] = r80name
                            params["ipv4-address"] = record["ipv4-address"]
                            params["ipv4-mask-wildcard"] = record["ipv4-mask-wildcard"]
                            params["color"] = record["color"]
                            response = self._client.api_call("add-wildcard", params)
                            if response.success:
                                if 'uid' in response.data:
                                    WUID = response.data["uid"]
                                    print '    > Created new wildcard object "{}" (uid: {})'.format(r80name, WUID)
                                else:
                                    print '    > ERROR "No UID returned!" after creating new wildcard object "{}"'.format(r80name)
                            else:
                                print '    > ERROR "{}" creating new wildcard object "{}"'.format(response.error_message, r80name)                         
                        response = self._client.api_call("where-used", {'uid': '{}'.format(NUID)})
                        for rule in response.data["used-directly"]["access-control-rules"]:
                            params = {}
                            params["uid"] = rule["rule"]["uid"]
                            params["layer"] = rule["layer"]["uid"]
                            params["details-level"] = "uid"
                            ruledata = self._client.api_call('show-access-rule', params)
                            ruledesc = "(uid: {})".format(params["uid"])
                            if "name" in ruledata.data:
                                if ruledata.data["name"] != "":
                                    ruledesc = '"{}"'.format(ruledata.data["name"])
                            print '    > Checking rule {}'.format(ruledesc)
                            sources = 0
                            destinations = 0
                            params["source"] = ruledata.data["source"]
                            params["destination"] = ruledata.data["destination"]
                            for i, record in enumerate(params["source"]):
                                if record == NUID:
                                    params["source"][i] = WUID
                                    sources += 1
                            for i, record in enumerate(params["destination"]):
                                if record == NUID:
                                    params["destination"][i] = WUID
                                    destinations += 1
                            if sources > 0 or destinations > 0:
                                if sources > 0 and destinations > 0:
                                    description = "source and destination columns"
                                elif sources > 0:
                                    description = "source column"
                                else:
                                    description = "destination column"
                                response = self._client.api_call('set-access-rule', params)
                                if response.success:
                                     print '      > Updated {}'.format(description)                              
                                else:
                                    print '      > ERROR "{}" updating {}'.format(response.error_message, description)

    def publish(self):
        response = self._client.api_call('publish', {}, wait_for_task=True)
        return response

    def logout(self):
        response = self._client.api_call('logout', {})
        return response

    def _get_generic_uid(self, objectType, name):
        retval = ""
        response = self._client.api_call(objectType, {'name': '{}'.format(name), 'details-level': 'uid'})
        if response.success and 'uid' in response.data:
            retval = response.data['uid']
        return retval

    def get_network_uid(self, name):
        return self._get_generic_uid('show-network', name)

    def get_wildcard_uid(self, name):
        return self._get_generic_uid('show-wildcard', name)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Wildcard import/rule conversion script v" + __version__)
    print "*** "
    print "*** " + parser.description
    print "*** "
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    required.add_argument("-i", "--input", required=True, action="store", help="Input file with records to convert")
    required.add_argument("-s", "--server", required=True, action="store", help="Server URL for management server")
    optional.add_argument("-u", "--user", action="store", help="Username to access the API")
    optional.add_argument("-p", "--password", action="store", help="Password to access the API")
    optional.add_argument("-d", "--domain", action="store", help="Domain (when using multidomain)")
    args = parser.parse_args()
    if os.path.isfile(args.input):
        records = []
        with open(args.input, 'rb') as f:
            reader = csv.DictReader(f)
            for line in reader:
                records.append(line)
        print "--- Read {:,} records from input file '{}'".format(len(records), args.input)
    else:
        print "!!! Could not open input file '{}'".format(args.input)
        sys.exit(1)

    print "--- Connecting to server at {}".format(args.server)
    client = APIClient(APIClientArgs(server=args.server, unsafe_auto_accept=True))
    result = client.check_fingerprint()
    if result is False:
        print("!!! Could not get the server's fingerprint! Check connectivity with the server.")
        sys.exit(1)

    if not args.user:
        args.user = raw_input('Username: ').strip('\r')
    else:
        print "--- Attempting to login as '{}'".format(args.user)

    if not args.password:
        args.password = getpass.getpass(stream=sys.stderr).strip('\r')

    if args.domain:
        print "--- Using domain '{}'".format(args.domain)
        response = client.login(args.user, args.password, domain=args.domain)
    else:
        print "--- Standard login..."
        response = client.login(args.user, args.password)

    if response.success is False:
        print "!!! Login failed: {}".format(response.error_message)
        sys.exit(1)

    if response.data['api-server-version'] >= 1.3:
        print "--- Login to management via API {} complete. (session-uid: {})".format(
            response.data['api-server-version'], response.data['sid'])
    else:
        print "!!! Server API needs to be version 1.3 or greater '{}' returned from login.".format(
            response.data['api-server-version'])
        sys.exit(1)

    wcm = WildcardManager(client)
    print "--- Starting Convert..."
    wcm.convert_rulebase(records)
    print "--- Starting Publish..."
    response = wcm.publish()
    if response.success:
        print "--- Publish complete."
    else:
        print "--- Publish failed. (message: {})".format(response.error_message)
    response = wcm.logout()
    if response.success:
        message = None
        if 'message' in response.data:
            message = response.data['message']
        print "--- Logout complete. (message: {})".format(message)
    else:
        print "--- Logout failed. (message: {})".format(response.error_message)


if __name__ == '__main__':
    main()
