## Version 1
Custom Chord system with the following API:

* PUT /storage/<key>: Store the value (message body) at the specific
key (last part of the URI). PUT requests issued with existing keys should
overwrite the stored data.  
* GET /storage/<key>: Retrieve the value at the specific key (last part
of the URI). The response body should then contain the value for that
key.
* GET /neighbours: Return a JSON object with neighbouring nodes i.e.
predecessor and successor nodes in a chord [1] system.
