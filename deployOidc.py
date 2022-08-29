#
# OIDC TAI EAR deployment/uninstall script, rev 1.1  8/29/2022
#
# Written by Barbara Jensen
# Based on deployConsole.py
#
# Copyright 2006,2022 IBM Corp.  All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

#------------------------------------------------------------------------------
# This script is to install/uninstall the OIDC TAI EAR as an admin 
# application
#
# Install:
# wsadmin.sh -f deployOidc.py install
#
# Uninstall:
# wsadmin.sh -f deployOidc.py uninstall
# 
# To prepare your system to run deployOidc.py on a deployment manager, 
# do the following:
# 
# cd (wasHome)/systemApps
# mkdir WebSphereOIDCRP.ear
# unzip ../../installableApps/WebSphereOIDCRP.ear
# cd ../profiles/(dmgr)/bin
# wsadmin -f deployOidc.py install
# 
#------------------------------------------------------------------------------
import sys

#------------------------------------------------------------------------------
# Get the directory, as a string, where WAS is installed.
#------------------------------------------------------------------------------
def getWASHome(cell, node):
	varMap = AdminConfig.getid("/Cell:" + cell + "/Node:" + node + "/VariableMap:/")
	entries = AdminConfig.list("VariableSubstitutionEntry", varMap)
	eList = entries.splitlines()
	for entry in eList:
		name =  AdminConfig.showAttribute(entry, "symbolicName")
		if name == "WAS_INSTALL_ROOT":
			value = AdminConfig.showAttribute(entry, "value")
			return value
	#failover
	return java.lang.System.getenv('WAS_HOME')


#------------------------------------------------------------------------------
# Get the WAS systemApps directory.
#
# The WAS systemApps directory is always located at <WAS_HOME>/systemApps 
#------------------------------------------------------------------------------
def getSystemAppsDir(cell, node):
	fileSep = getFileSep(node)
	return getWASHome(cell, node) + fileSep + "systemApps"

#------------------------------------------------------------------------------
# Get the directory, as a string, of the WebSphereOIDCRP.ear application.
#
# The WebSphereOIDCRP.ear is located in <WAS_HOME>/systemApps/WebSphereOIDCRP.ear
#------------------------------------------------------------------------------
def getISCDir(cell, node):
	fileSep = getFileSep(node)
	return getSystemAppsDir(cell, node) + fileSep + "WebSphereOIDCRP.ear"

#------------------------------------------------------------------------------
# Get the file separator character
#
# This gets the file separator for the node in which we plan to install the
# console.  Therefore we can't just use the value that python on Java gives
# us.  Instead, check the platform of the node, and use "\" for windows and
# "/" for everything else.
#------------------------------------------------------------------------------
def getFileSep(node): 
	os = AdminTask.getNodePlatformOS("-nodeName " + node)
	if os == 'windows':
		return '\\'
	else:
		return '/'

#------------------------------------------------------------------------------
# updateDeploymentXml 
# sharedLibBypass = true
# Console doesn't work with enableSecurityIntegration=true
# Default cookie path should be /ibm
#------------------------------------------------------------------------------
def updateDeploymentXml():
	try:
		print "Updating deployment.xml"
		WebSphereOIDCRP = AdminConfig.getid("/Deployment:WebSphereOIDCRP_Admin/")
		WebSphereOIDCRPDepObject = AdminConfig.showAttribute(WebSphereOIDCRP, "deployedObject")
		prop = [['name', 'com.ibm.ws.classloader.sharedLibBypass'], ['value', 'true'], ['required', 'false']]
		AdminConfig.create("Property", WebSphereOIDCRPDepObject, prop)
		attr1 = ['enableSecurityIntegration', 'false']
		attrs = [attr1]
		sessionMgr = [['sessionManagement', attrs]]
		configs = AdminConfig.showAttribute (WebSphereOIDCRPDepObject, "configs")
		appConfig = configs[1:len(configs)-1] 
		SM = AdminConfig.showAttribute (appConfig, 'sessionManagement') 
		AdminConfig.modify (SM, attrs)
		kuke = AdminConfig.showAttribute (SM, 'defaultCookieSettings')
		kukeAttrs = [['path', '/ibm']]
		AdminConfig.modify(kuke, kukeAttrs)
		return 1
	except:
		print "Error during updateDeploymentXml():", sys.exc_info()
		return 0	

#------------------------------------------------------------------------------
# setupIEHSClassloader 
# Set the classloader for IEHS to PARENT_LAST
#------------------------------------------------------------------------------
def setupIEHSClassloader():
	print "Setting IEHS classloader to PARENT_LAST"
	WebSphereOIDCRP = AdminConfig.getid("/Deployment:WebSphereOIDCRP_Admin/")
	WebSphereOIDCRPDepObject = AdminConfig.showAttribute(WebSphereOIDCRP, "deployedObject")
	modules =  AdminConfig.list("WebModuleDeployment", WebSphereOIDCRPDepObject).splitlines()
	for module in modules:
		if AdminConfig.showAttribute(module, "uri") == "com.ibm.ws.security.oidc.servlet.war":
			AdminConfig.modify(module, [['classloaderMode', 'PARENT_LAST']])
			return 1
	#return 0 for failure
	return 0	

#------------------------------------------------------------------------------
# setCellVar 
#------------------------------------------------------------------------------
def setCellVar(cell):
	try:
		varMap = AdminConfig.getid("/Cell:" + cell + "/VariableMap:/")
		prop = [[['symbolicName', 'WAS_CELL_NAME'], ['value', cell]]]
		AdminConfig.modify(varMap, [['entries', prop]])	
		return 1
	except:
		print "Error during setCellVar(" + cell + "):", sys.exc_info()
		return 0



#------------------------------------------------------------------------------
# deployAdminConsole
# Deploy the WebSphereOIDCRP.ear using the AdminApp install command, and then map it
# to the admin_host virtual host.
#------------------------------------------------------------------------------
def deployOidcEar(cell, node, server, type):
	iscDir  = getISCDir(cell, node)
	sysAppDir  = getSystemAppsDir(cell, node)
	try:
		print "Deploying WebSphereOIDCRP.ear"
		AdminApp.install(iscDir, ['-node', node, '-server', server, '-appname', 'WebSphereOIDCRP_Admin', '-usedefaultbindings', '-copy.sessionmgr.servername', server, '-zeroEarCopy', '-skipPreparation', '-installed.ear.destination', '$(WAS_INSTALL_ROOT)/systemApps'])
		
        #Do virtual host mapping
		print "Mapping WebSphereOIDCRP_Admin to admin_host"
		AdminApp.edit('WebSphereOIDCRP_Admin', ['-MapWebModToVH', [['.*', '.*', 'admin_host']]])
	except:
		error = str(sys.exc_info()[1])
		if error.count("7279E") > 0: # catch WASX7279E (app with given name already exists)
			print "the OIDC TAI EAR is already installed."
		else:
			print "Exception occurred during deployOidcEar(" + cell +", " + node + ", " + server + "):", error
		return 0
	return 1

#------------------------------------------------------------------------------
# Get a tuple containing the cell, node, server name, and type
#------------------------------------------------------------------------------
def getCellNodeServer():
	servers = AdminConfig.list("Server").splitlines()
	for serverId in servers:
		serverName = serverId.split("(")[0]
		server = serverId.split("(")[1]  #remove name( from id
		server = server.split("/")
		cell = server[1]
		node = server[3]
		cellId = AdminConfig.getid("/Cell:" + cell + "/")
		cellType = AdminConfig.showAttribute(cellId, "cellType")
		if cellType == "DISTRIBUTED":
			if AdminConfig.showAttribute(serverId, "serverType") == "DEPLOYMENT_MANAGER":
				return (cell, node, serverName, "DEPLOYMENT_MANAGER") 
		elif cellType == "STANDALONE":
			if AdminConfig.showAttribute(serverId, "serverType") == "APPLICATION_SERVER":
				return (cell, node, serverName, "APPLICATION_SERVER") 
			elif AdminConfig.showAttribute(serverId, "serverType") == "ADMIN_AGENT":
				return (cell, node, serverName, "ADMIN_AGENT") 
	return None	
		

#------------------------------------------------------------------------------
# Print script usage
#------------------------------------------------------------------------------
def printUsage():
	print "Usage: wsadmin deployOidc.py install"
	print "  or:  wsadmin deployOidc.py uninstall"
	print ""

#------------------------------------------------------------------------------
# Install the the OIDC TAI EAR
#------------------------------------------------------------------------------
def doInstall():
	topology = getCellNodeServer()
	if topology == None:
		sys.stderr.write("Could not find suitable server\n")
		if failOnError == "true":
			sys.exit(105)
	else:
		cell = topology[0]
		node = topology[1]
		server = topology[2]
		type = topology[3]

		retVal = deployOidcEar(cell, node, server, type)
		if retVal == 1:
			retVal = updateDeploymentXml()
		#if retVal == 1:
		#	retVal = setCellVar(cell)
		if retVal == 1:
		  	retVal = setupIEHSClassloader()
		if retVal == 1:
			AdminConfig.save()
		else:
			print "Skipping Config Save"
			if failOnError == "true":
				sys.exit(109)


#------------------------------------------------------------------------------
# Uninstall the the OIDC TAI EAR
#------------------------------------------------------------------------------
def doRemove():
	AdminApp.uninstall("WebSphereOIDCRP_Admin")
	AdminConfig.save()
	

#------------------------------------------------------------------------------
# Main entry point
#------------------------------------------------------------------------------

failOnError = "false" 

if len(sys.argv) < 1 or len(sys.argv) > 2:
	sys.stderr.write("Invalid number of arguments\n")
	printUsage()
	sys.exit(101)	
else:
	if len(sys.argv) == 2:
		if sys.argv[1] == "-failonerror":
			failOnError = "true"
			print "failonerror is enabled"
		else:
			sys.stderr.write("Invalid option:  " + sys.argv[1] + "\n")
			printUsage()			
			sys.exit(102)

	mode = sys.argv[0]
	if mode == "install":
		print "Installing the OIDC TAI EAR as an Admin app for the dmgr"
		doInstall()
	elif mode == "remove":
		print "Removing the OIDC TAI EAR Admin app"
		doRemove()
	elif mode == "uninstall":
		print "Removing the OIDC TAI EAR Admin app"
		doRemove()
	else:
		sys.stderr.write("Invalid command:  " + mode + "\n")
		printUsage()			
		if failOnError == "true":
			sys.exit(103)

