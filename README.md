[comment]: # "Auto-generated SOAR connector documentation"
# WiGLE

Publisher: Splunk  
Connector Version: 2\.0\.4  
Product Vendor: WiGLE  
Product Name: WiGLE  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 4\.9\.39220  

This app integrates with the WiGLE service to implement investigative actions

### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a WiGLE asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**api\_name** |  required  | string | API Name
**api\_token** |  required  | password | API Token

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity  
[lookup network](#action-lookup-network) - Get info about a WiFi SSID  

## action: 'test connectivity'
Validate the asset configuration for connectivity

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'lookup network'
Get info about a WiFi SSID

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**name** |  required  | SSID | string |  `ssid` 
**max\_results** |  optional  | Max results per page \(default is 100\) | numeric | 
**page\_token** |  optional  | Page Token \(Should be empty to get the 1st page\) | string |  `page token` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.max\_results | numeric | 
action\_result\.parameter\.name | string |  `ssid` 
action\_result\.parameter\.page\_token | string |  `page token` 
action\_result\.data\.\*\.bcninterval | numeric | 
action\_result\.data\.\*\.channel | numeric | 
action\_result\.data\.\*\.city | string | 
action\_result\.data\.\*\.comment | string | 
action\_result\.data\.\*\.country | string | 
action\_result\.data\.\*\.dhcp | string | 
action\_result\.data\.\*\.encryption | string | 
action\_result\.data\.\*\.firsttime | string | 
action\_result\.data\.\*\.freenet | string | 
action\_result\.data\.\*\.housenumber | string | 
action\_result\.data\.\*\.postalcode | string | 
action\_result\.data\.\*\.lasttime | string | 
action\_result\.data\.\*\.lastupdt | string | 
action\_result\.data\.\*\.name | string | 
action\_result\.data\.\*\.netid | string | 
action\_result\.data\.\*\.paynet | string | 
action\_result\.data\.\*\.qos | numeric | 
action\_result\.data\.\*\.region | string | 
action\_result\.data\.\*\.road | string | 
action\_result\.data\.\*\.ssid | string |  `ssid` 
action\_result\.data\.\*\.transid | string | 
action\_result\.data\.\*\.trilat | numeric | 
action\_result\.data\.\*\.trilong | numeric | 
action\_result\.data\.\*\.type | string | 
action\_result\.data\.\*\.userfound | boolean | 
action\_result\.data\.\*\.wep | string | 
action\_result\.summary\.first | numeric | 
action\_result\.summary\.last | numeric | 
action\_result\.summary\.next\_page\_token | numeric |  `page token` 
action\_result\.summary\.result\_count | numeric | 
action\_result\.summary\.total\_results | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 