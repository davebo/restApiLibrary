# Python 2.7
#
# Plutora REST API library v1.0
#
# Instructions
#	Create a file "credentials.cfg" with the API URLs and credentials:
#		{
#		  "urls":{
#			"authUrl":"https://usoauth.plutora.com/",
#			"baseUrl":"https://usapi.plutora.com/"
#		  },
#		  "credentials": {
#			"client_id":"XXXXXXXXXXXXXXXXXXXXXXXXXX",
#			"client_secret":"YYYYYYYYYYYYYYYYYYYYYYYYYY",
#			"username":"user@company.com",
#			"password":"secretvalue"
#			}
#		}
#
#		You can leave the password field blank; if blank, you will be prompted for it at the command line.
#
#	Create a Python file that loads the Plutora package: 'include plutora'
#
# Public Functions
# ----------------
# api()
#	Make REST API call to Plutora
# listToDict()
#	Transform a list of multiple field-value pairs into a dictionary of key-value pairs
# guidByPathAndName()
#	Return the GUID of the object at an API path of a given name
# getAccessToken()
# 	Returns access_token
#
# Private Functions
# -----------------
# __getUserCredentials()
# 	Returns username and password from the command line
#
import json
import requests
import getpass
# import csv
# import datetime
# import os.path
# import glob
# import sys

with open("credentials.cfg") as data_file:
	data = json.load(data_file)

authUrl = data["urls"]["authUrl"]
baseUrl = data["urls"]["baseUrl"]
client_id = data["credentials"]["client_id"]
client_secret = data["credentials"]["client_secret"]
username = data["credentials"]["username"]
password = data["credentials"]["password"]

def __getUserCredentials(defaultUser):
	# Prompts user for username then password (no echo)
	#
	# Returns: username and password from the command line
	username = raw_input( 'Enter your Plutora userid [' + defaultUser + ']: ' )
	username = username or defaultUser
	password = getpass.getpass('Password: ')
	return username,password
	# ------End of def __getUserCredentials()-----------

if not password:
	username,password = __getUserCredentials(username)

def getAccessToken():
	# Returns access_token
	#
	# authUrl:
	#	https://usoauth.plutora.com/
	# client_id & client_secret
	#	Values generated by Plutora platform, see Customizations>API
	# username & password
	#	User credentials used to access the Plutora platform
	#
	# If successful, Returns: "" or JSON-formatted response
	# On failure, Returns: response text
	#
	headers = {}
	headers['content-type'] = "application/x-www-form-urlencoded"
	headers['cache-control'] = "no-cache"
	url = authUrl + "oauth/token"
	payload  = "client_id=" + client_id + '&'
	payload += "client_secret=" + client_secret + '&'
	payload += "grant_type=" + 'password&'
	payload += "username=" + username.replace('@','%40') + '&'
	payload += "password=" + password + '&'
	response = requests.request("POST", url, data=payload, headers=headers)
	if not response.ok:
		print "Access token: "
		print(response.text)
		exit()
	access_token = response.json()['access_token']
	return access_token
	# ------End of def getAccessToken()-----------

def api(verb, api, data=""):
	# Make REST API call to Plutora
	#
	# verb
	#	GET
	#	PUT
	#	POST
	#	DELETE
	# api
	#	systems
	#	systems/{id}
	#	etc, see https://usapi.plutora.com/help
	# data
	#	For GET and DELETE: ""
	#	For PUT and POST: Object that gets rendered as JSON by this function using json.dumps()
	#		obj = [
	#				{
	#					"name":"abc",
	#					"field1":"2.0"
	#				},
	#				{
	#					"name":"xyz",
	#					"field1":"3.0"
	#				}
	#			]
	#	
	# If successful, Returns: "" or JSON-formatted response
	# On failure, Returns: response text
	#
	access_token=getAccessToken()
	fullUrl = baseUrl + api
	headers={}
	headers['authorization']="bearer " + access_token
	headers['content-type']="application/json"
	headers['cache-control'] = "no-cache"
	response = requests.request(verb, fullUrl, data=json.dumps(data), headers=headers)
	if not response.ok:
		print(response.text)
	if response.text:
		responseJson=response.json()
	else:
		responseJson=""
	return responseJson
	# ------def listToDict()--------------------------

def listToDict(list, key, value):
	# Transform a list of multiple field-value pairs into a dictionary of key-value pairs
	# IN: [{"a":"x","b":"y","c":"z"...},{"a":"xx","b":"yy","c":"zz"...}]
	# If key = "b" and value = "c"
	# OUT: {"y":"z","yy":"zz",...}
	keyValPairs = {}
	for element in list:
		keyValPairs[element[key]]=element[value]
	return keyValPairs
	# ------End of def guidByPathAndName()-------------

def guidByPathAndName(path, name, field="name"):
	## Return the GUID of the object at an API path of a given name
	## Default field to look up by is "name", this can be optionally overridden
	# Get all objects at API path location
	objects = api("GET", path)
	# Transform list in to name_n:guid_n dictionary
	guidList=listToDict(objects, field, "id")
	return guidList[name]
	# ------End of def guidByPathAndName()---------------			


def getComponentId(path):
	# Returns the GUID of the component at the path /environmentName/hostName/layerType/componentName:
	#
	# path = {
	# 	environmentName: <environmentName>,
	# 	hostName: <hostName>,
	# 	layerType: <layerTypeName>, # As named in Settings> Customizations> Environments> Stack Layer
	# 	componentName: <componentName>
	# }
	environments = listToDict(api("GET","environments"), "name", "id")
	environmentGuid = environments[path['environmentName']]
	environmentData = api("GET","environments/"+environmentGuid)
	hosts = environmentData['hosts']
	layers = []
	stackLayerID=""
	for host in hosts:
		if (host['name']==path['hostName']):
			layers = host['layers']
			break
	for layer in layers:
		if (layer['stackLayer']==path['layerType'] and layer['componentName']==path['componentName']):
			componentId=layer['id']
			break
	return componentId
	
objectFields = {

	"systems" : [
		{"name": "Name", "required": True, "lookup": False, "values": []},
		{"name": "Vendor", "required": True, "lookup": False, "values": []},
		{"name": "Status", "required": True, "lookup": False, "values": ["Active","Inactive"]},
		{"name": "Organization", "required": True, "lookup": True, "values": []},
		{"name": "Description", "required": True, "lookup": False, "values": []}
	],
	"environments" : [
		{"name": "Name", "required": True, "lookup": False, "values": []},
		{"name": "Description", "required": False, "lookup": False, "values": []},
		{"name": "URL", "required": False, "lookup": False, "values": []},
		{"name": "Vendor", "required": True, "lookup": False, "values": []},
		{"name": "LinkedSystem", "required": True, "lookup": True, "values": []},
		{"name": "EnvironmentMgr", "required": False, "lookup": False, "values": []},
		{"name": "UsageWorkItem", "required": True, "lookup": True, "values": []},
		{"name": "EnvironmentStatus", "required": True, "lookup": True, "values": []},
		{"name": "Color", "required": True, "lookup": False, "values": []},
		{"name": "IsSharedEnvironment", "required": True, "lookup": False, "values": []},
		{"name": "hostName", "required": False, "lookup": False, "values": []},
		{"name": "StackLayer", "required": False, "lookup": True, "values": []},
		{"name": "StackLayerType", "required": False, "lookup": False, "values": []},
		{"name": "ComponentName", "required": False, "lookup": False, "values": []},
		{"name": "Version", "required": False, "lookup": False, "values": []}
	],
	"releases" : [
		{"name": "Identifier", "required": True, "lookup": False, "values": []},
		{"name": "Name", "required": True, "lookup": False, "values": []},
		{"name": "Summary", "required": False, "lookup": False, "values": []},
		{"name": "ReleaseType", "required": True, "lookup": True, "values": []},
		{"name": "Location", "required": True, "lookup": False, "values": []},
		{"name": "ReleaseStatusType", "required": True, "lookup": True, "values": ["Active","Inactive"]},
		{"name": "ReleaseRiskLevel", "required": True, "lookup": True, "values": []},
		{"name": "ImplementationDate", "required": True, "lookup": False, "values": []},
		{"name": "DisplayColor", "required": True, "lookup": False, "values": []},
		{"name": "Organization", "required": True, "lookup": True, "values": []},
		{"name": "Manager", "required": True, "lookup": True, "values": []},
		{"name": "ParentRelease", "required": False, "lookup": True, "values": []},
		{"name": "PlutoraReleaseType", "required": True, "lookup": False, "values": ["Enterprise","Integrated","Independent"]},
		{"name": "ReleaseProjectType", "required": True, "lookup": False, "values": ["IsProject","NotIsProject","None"]}
	]
}

	

