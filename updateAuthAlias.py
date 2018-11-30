print "This script is provided on an as-is basis with no implied warranty or support."
if len(sys.argv) != 3:
	print "Expected 3 arguments, got "  + str(len(sys.argv))
	print "Usage: updateAuthAlias authAliasName newUserName newPassword"
	print "Updates the userid and password of the specified JAAS authentication alias, where authAliasName is the name of an existing auth alias and newUserName and newPassword are the user id and password to update the auth alias with."
	sys.exit(-1)
authAlias = sys.argv[0]
userId = sys.argv[1]
password = sys.argv[2]

# lists current values of the specified auth alias 
print "Attributes of auth alias " + authAlias + " before modification"
print AdminTask.getAuthDataEntry('[-alias ' + authAlias + ']')

#  change the userid and/or password for the specified auth alias
AdminTask.modifyAuthDataEntry('[-alias ' + authAlias + ' -user ' + userId + ' -password ' + password + ']')
# persist workspace
AdminConfig.save()
 
# list the new values of the specified auth alias
print "Attributes of auth alias " + authAlias + " after modification"
print AdminTask.getAuthDataEntry('[-alias ' + authAlias + ']')

# lookup the security admin mbean
secAdminMBean = AdminControl.queryNames("WebSphere:type=SecurityAdmin,process=server1,*")
# use the security admin mbean to reload the jaas config data
AdminControl.invoke(secAdminMBean, 'updateJAASCfg', "null")
# use the security admin mbean to reload the auth alias config data
AdminControl.invoke(secAdminMBean, 'updateAuthDataCfg', "null")
# drop cache
AdminTask.clearAuthCache()
