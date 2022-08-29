# sample.wsadmin.websphere-traditional
WebSphere Application Server traditional wsadmin scripts

## Scripts provided
### updateAuthAlias.py
Dynamically updates the password of the specified JAAS authentication alias in a server process without requiring a server restart.  This script will not work as written on a node agent or deployment manager.

### deployOidc.py
Installs and uninstalls the OpenId Connect (OIDC) Trust Association Interceptor (TAI) EAR, `WebSphereOIDCRP.ear`, as an admin application.
If you intend to protect the administrative console on the deployment manager with the OIDC TAI, the OIDC EAR must be deployed as an admin app. 

To prepare your system to run `deployOidc.py` on a deployment manager, do the following:

```
cd (wasHome)/systemApps
mkdir WebSphereOIDCRP.ear
unzip ../../installableApps/WebSphereOIDCRP.ear
cd ../profiles/(dmgr)/bin
wsadmin -f deployOidc.py install
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
Unless otherwise noted in a script:<br/>
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
