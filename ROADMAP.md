# Bifrost RPC Roadmap

## Version 1.0

All that's needed for a 1.0 release is the limited subset of features I would
reasonably expect to implement if I was building an ad-hoc JSON-RPC API for a
typical web app.

This would include a mechanism to expose existing functions through a flask app
in such a way that:

- All that's needed to expose a function is it's name and its containing module
- You use the function's real name to call it from the client
- Clients can pass an arbitrarily-long list of values that become the
  function's arguments
- The functions' return values are returned to the client

Notably, I wouldn't imagine myself building any of the following into an ad-hoc
JSON-RPC API:

- Master/slave mode
- Any serialization method other than JSON
- Any server mode other than stateless http server via flask (python) or http/nginx (php)
- Serialization of class instances.
- Serialization of callbacks.
- Serialization of any value that isn't JSON-compatible
- Unserializing to non-JSON values at the other end
- Asynchronous request handling when callbacks are activated
- Automatic generation of client libraries.
- Automatic type annotations in client libraries
- Automatic documentation of client libraries
- Tools to export/manage Shape/Versions, and change of shape/versions over time
