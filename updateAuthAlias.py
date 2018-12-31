print "This script is provided on an as-is basis with no implied warranty or support."
if len(sys.argv) < 2:
	print "ERROR: Expected 2 or 3 arguments, got "  + str(len(sys.argv))
	print "Usage: updateAuthAlias authAliasName newPassword [securityDomain]"
	print "Dynamically updates the password of the specified JAAS authentication alias in a server process without requiring a server restart.  This script will not work as written on a node agent or deployment manager."
	print "Required parameters:"
	print "authAliasName - the name of an existing auth alias to be updated.  This auth alias must exist in either the global/admin security domain or the specified security domain"
	print "newPassword - the new password of the auth alias"
	print "Optional parameters:"
	print "securityDomain - if not specified, the global/admin domain is updated, otherwise the specified authentication alias in the specified security domain is updated"
	sys.exit(-1)
authAlias = sys.argv[0]
password = sys.argv[1]
if len(sys.argv) == 3:
	secDomain = sys.argv[2]
	secDomainParm = '-securityDomainName [' + secDomain + ']'
else:
	secDomain = "global/admin"
	secDomainParm = ''

#lists current set of security domains
print "Listing all security domains"
print AdminTask.listSecurityDomains()
print

#lists current set of auth aliases
print "Listing all authentication aliases in " + secDomain + " security domain " 
print AdminTask.listAuthDataEntries(secDomainParm)
print

# list the current values of the specified authentication alias within the specified security domain
print "Attributes of authentication alias " + authAlias + " in " + secDomain + " security domain " + " before modification"
attribs = AdminTask.getAuthDataEntry('[-alias [' + authAlias + '] ' + secDomainParm + ']')
print attribs

print "Modifying authentication alias " + authAlias + " in security domain " + secDomain
#  change the password for the specified auth alias
AdminTask.modifyAuthDataEntry('[-alias [' + authAlias + '] -password ' + password + secDomainParm + ']')
print

# persist workspace
print "Saving changes"
AdminConfig.save()
print
  
# lookup the security admin mbean
print "Accessing security mbean"
secAdminMBean = AdminControl.queryNames("WebSphere:type=SecurityAdmin,process=server1,*")
print

# use the security admin mbean to reload the auth alias config data
print "Updating Auth data configuration"
AdminControl.invoke(secAdminMBean, 'updateAuthDataCfg', "null")
print

#retrieve userId from attrib list
userId = ""
for elem in attribs.split('] ['):
	if ("userId") in elem:
		userId = elem.split()[1]
if userId == "" :
	print "ERROR: Couldn't determine userId of auth alias " + authAlias
	sys.exit(-2)

# drop user from auth cache
print "Clearing user " + userId + " from auth cache"
AdminTask.purgeUserFromAuthCache('[-user ' + userId + ' -securityRealmName defaultWIMFileBasedRealm]')

# list the new values of the specified auth alias in the specified security domain
print "Attributes of authentication alias " + authAlias + " in " + secDomain + " security domain " + " after  modification"
print AdminTask.getAuthDataEntry('[-alias [' + authAlias + '] ' + secDomainParm + ']')
print

