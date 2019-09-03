# Bifrost

Bifrost provides an RPC bridge between different services and/or programming
languages, with a focus on providing client interfaces that are as close as
possible to native function calls.


# Terminology

* **Master**/**Slave**: The master/client processes in a **master/slave** operation mode
* **Client**/**Server**: The master/client processes in a **client/server** operation mode
* **Host**: A [slave] or [server] that makes a [collection] available to [consumers].
* **Consumer**: A [master] that spawns a [slave] process and makes RPC calls to the collection
  provided by that [slave]; OR
  a [client] that connects to a [server] and makes RPC calls to the collection provided by that
  server.
* **Collection** a class or function that defines a list of CCC that will be made available to
  consumers.
* **Consumer Library**: An auto-generated package of source code containing function and class
  wrappers that make RPC calls to to a Server or Slave.

* TODO:
  * AAA: a list of functions/classes/variables that are grouped together for 
  * BBB: an auto-generated library for Clients or Masters or to import and use as endpoints to use functions/classes/variables of an AAA
  * CCC: the various functions/classes/variables of an AAA
* Consumer Library - an exported library for processes that want to connect to a Collection
* TODO


# Naming Conventions

In this example you have a collection of functions that handle user authentication and you want to
create a Server that hosts this collection on the network for other services to use.
TODO: reword this

## PHP

The Collection would be a class named `MyProject\CoolThings\AuthServices`.

The consumer library would typically be exported to:

* PHP: namespace `MyProject\CoolThings\AuthServices\ConsumerAPI`.
* Python: module `MyProject.CoolThings.AuthServices.ConsumerAPI`. Note that
  `MyProject.CoolThings.AuthServices` would be [namespace packages](todo: link).
* JavaScript: module `MyProject/CoolThings/AuthServices/ConsumerAPI.js`.
  TODO: we'll need a mechanism to choose the exported module type ... :-/

The Consumer Library would be exported to the corresponding namespace `My\Namespace\SomeCollection\ConsumerAPI`.

When




# Supported Data Types

* JSON-compatible values
* Stateless class instances
* Handles (Stateful class instances - TODO: what operation modes support this?)


# Other Features

* Exposing constants as well as callables
* username/password authentication?

# Class Instance Paradox

When a class instance handle is given to a client, and the client calls a
setSomeProperty() method on the instance, we can reasonably assume we need
transmit all the instance's properties from the server back to the client.

However, what if the instance has a sub-object. E.g., We have a `Person $person` which has an
`Address $address` property, and we call `$person->setAddressCountry(...)` to modify their
address.

How do we determine that properties of the `$address` need to be transmitted back to the client?

It's worth noting that if you used a simpler API platform such as REST or JSON-RPC you wouldn't
have this issue because it's implicit that you're working with a copy of the server's object data
stored in an ad-hoc data structure.

1) Don't transmit public properties at all. Force client's to use getters e.g.  `getFirstName()`.
   **Pros:** obvious exactly how and when state is being copied from the server.
   **Cons:** calling multiple getters in a row will be expensive.

   Variant A) We have a mechanism to mark certain properties as immutable (e.g.
   `$person->PersonID`) and transmit those properties immediately with the original object
   handlwith the original object handle.

TODO: finish fleshing this out



# Operation modes

- **Master/Slave**: _master_ process _A_ written in language _A_ spawns a
  subprocess _B_ written in language _B_ and uses RPC over stdin/stdout streams to
  call functions from _B_ and get results.
  Options:
  - spawn modes: immediate; first-use; immediate-async
  - Supports handles? Yes

- **Client/Server**: _server_ process _A_ written in language _A_ listens for
  connections, and responds to requests. _client_ process _B_ written in
  language _B_ connects to _A_ via e.g. https protocol and makes function calls
  - Options:
  - Protocol: http(s) / MSGPACK-RPC / Line-based
  - Transport: unix socket, network port
  - Authentication?
  - Supports handles: Maybe - via unix sockets maybe, but not over https

- **Cluster**: multiple _server_ processes listen on network sockets using e.g.
  MSGPACK-RPC. Each process in the cluster has an identical mapping that
  specifies which network hosts are serving which AAA. Each processes
