 # Copyright 2020 Hewlett Packard Enterprise Development LP
 #
 # Licensed under the Apache License, Version 2.0 (the "License"); you may
 # not use this file except in compliance with the License. You may obtain
 # a copy of the License at
 #
 #      http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 # WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 # License for the specific language governing permissions and limitations
 # under the License.

# -*- coding: utf-8 -*-
"""
An example of adding an license key for HPE iLO systems
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

from get_resource_directory import get_resource_directory

def set_license_key(_redfishobj, ilo_key):

    ilo_lic_uri = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        ilo_lic_uri = managers_members_response.obj.Oem.Hpe.Links['LicenseService']['@odata.id']
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
        if '#Manager.' in instance['@odata.type']:
            manager_uri = instance['@odata.id']
            mager_data = _redfishobj.get(manager_uri)
            ilo_lic_uri = mager_data.obj['Oem']['Hpe']['Links']['LicenseService']['@odata.id']

    if ilo_lic_uri:
        ilo_license_collection = _redfishobj.get(ilo_lic_uri)
        ilo_license_member_uri = next(iter(ilo_license_collection.obj['Members']))['@odata.id']
        try:
            ilo_license_data = _redfishobj.get(ilo_license_member_uri).obj['ConfirmationRequest']\
                                                                                            ['EON']
        except KeyError:
            sys.stdout.write("This machine will not show the full License Key.\n")
            ilo_license_data = _redfishobj.get(ilo_license_member_uri).obj['LicenseKey']

        sys.stdout.write("Current iLO License Data:\n")
        print(json.dumps(ilo_license_data, indent=4, sort_keys=True))
        resp = _redfishobj.post(ilo_lic_uri, {'LicenseKey' : ilo_key})
        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                sort_keys=True))
                sys.stderr.write("Check the validity of your license key...\n")
            except Exception as excp:
                sys.stderr.write("A response error occurred, unable to access iLO " \
                                 "Extended Message Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("Success!\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))

if __name__ == "__main__":
    # When running on the server locally use the following commented values
    #SYSTEM_URL = None
    #LOGIN_ACCOUNT = None
    #LOGIN_PASSWORD = None

    # When running remotely connect using the secured (https://) address,
    # account name, and password to send https requests
    # SYSTEM_URL acceptable examples:
    # "https://10.0.0.100"
    # "https://ilo.hostname"
    SYSTEM_URL = "https://10.0.0.100"
    LOGIN_ACCOUNT = "admin"
    LOGIN_PASSWORD = "password"

    # Must be a valid iLO License Key
    ILO_LICENSE_KEY = "XXXX-XXXX-XXXX-XXXX-XXXXX"
    # flag to force disable resource directory. Resource directory and associated operations are
    # intended for HPE servers.
    DISABLE_RESOURCE_DIR = True

    try:
        # Create a Redfish client object
        REDFISHOBJ = RedfishClient(base_url=SYSTEM_URL, username=LOGIN_ACCOUNT, \
                                                                            password=LOGIN_PASSWORD)
        # Login with the Redfish client
        REDFISHOBJ.login()
    except ServerDownOrUnreachableError as excp:
        sys.stderr.write("ERROR: server not reachable or does not support RedFish.\n")
        sys.exit()

    set_license_key(REDFISHOBJ, ILO_LICENSE_KEY)
    REDFISHOBJ.logout()
