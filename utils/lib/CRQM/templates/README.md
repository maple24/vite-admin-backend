## How to get xml template
request.get an existing url and delete filled infos
Sometimes <namespace> will change.
template can be various depends on your requirement

## Header
the header can specify your request data format, "json" or "xml"
however put&post method only accept xml.

## Request.text
the request info is a xml only when your authentification is right, otherwise it is a html

## Login
cookies are stored in header which is a self parameter once logged in


## Resoure type mapping  
- buildrecord:          Build Record
- configuration:        Test Environment
- testplan:             Test Plan
- testsuite:            Test Suite
- suiteexecutionrecord: Test Suite Execution Record (TSER)
- testsuitelog:         Test Suite Log (Test suite results)
- testcase:             Test Case
- executionworkitem:    Test Case Execution Record (TCER)
- executionresult:      Execution Result (Test case results)

## HTTP request status code
200	OK
201	Resource Created
303	See Other
400	Bad Request (Incorrect XML)
403	Forbidden (Unauthorized)
401	Unauthorized
404	Not Found
405	Bad Method
406	Not Acceptable
409	Conflict
410	Gone
413	Request Entity Too Large
500	Internal Server Error
501	Not Implemented