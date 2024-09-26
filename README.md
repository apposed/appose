# Appose

Appose is a library for interprocess cooperation with shared memory.
The guiding principles are *simplicity* and *efficiency*.

Appose was written to enable **easy execution of Python-based deep learning
from Java without copying tensors**, but its utility extends beyond that.
The steps for using Appose are:

* Build an Environment with the dependencies you need.
* Create a Service linked to a *worker*, which runs in its own process.
* Execute scripts on the worker by launching Tasks.
* Receive status updates from the task asynchronously via callbacks.

## Goals

Python, Java, and JavaScript, working in harmony, side by side.
Separate processes, shared memory, minimal dependencies.

1. Construct an environment. E.g.:
   * Java with dependencies from Maven.
   * Python with dependencies from conda-forge.
   * JavaScript/Node.js with dependencies from NPM (**planned**).

2. Invoke routines in that environment:
   * Routines are run in a separate process.
   * The routine's inputs and outputs are passed via pipes (stdin/stdout).
   * NDArrays are passed as named shared memory buffers,
     for zero-copy access across processes.

## Examples

Each supported language/platform has its own implementation of Appose.
You can find examples for each language (calling out to other languages)
in each implementation's README:

* [Java](https://github.com/apposed/appose-java#examples)
* [Python](https://github.com/apposed/appose-python#examples)

## Workers

A *worker* is a separate process created by Appose to do asynchronous
computation on behalf of the calling process. The calling process interacts
with a worker via its associated *service*.

Appose comes with built-in support for two worker implementations:
`python_worker` to run Python scripts, and `GroovyWorker` to run Groovy
scripts. These workers can be created easily by invoking the environment
object's `python()` and `groovy()` methods respectively.

But Appose is compatible with any program that abides by the
*Appose worker process contract*:

1. The worker must accept requests in Appose's *request* format on its
   standard input (stdin) stream.
2. The worker must issue responses in Appose's *response* format on its
   standard output (stdout) stream.

### Requests to worker from service

A *request* is a single line of JSON sent to the worker process via its
standard input stream. It has a `task` key taking the form of a
[UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier),
and a `requestType` key with one of the following values:

#### EXECUTE

Asynchronously execute a script within the worker process. E.g.:
```json
{
   "task" : "87427f91-d193-4b25-8d35-e1292a34b5c4",
   "requestType" : "EXECUTE",
   "script" : "task.outputs[\"result\"] = computeResult(gamma)\n",
   "inputs" : {"gamma": 2.2}
}
```

#### CANCEL

Cancel a running script. E.g.:
```json
{
   "task" : "87427f91-d193-4b25-8d35-e1292a34b5c4",
   "requestType" : "CANCEL"
}
```

### Responses from worker to service

A *response* is a single line of JSON with a `task` key taking the
form of a
[UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier),
and a `responseType` key with one of the following values:

#### LAUNCH

A LAUNCH response is issued to confirm the success of an EXECUTE
request.
```json
{
   "task" : "87427f91-d193-4b25-8d35-e1292a34b5c4",
   "responseType" : "LAUNCH"
}
```

#### UPDATE

An UPDATE response is issued to convey that a task has somehow made
progress. The UPDATE response typically comes bundled with a
`message` string indicating what has changed, `current` and/or
`maximum` progress indicators conveying the step the task has
reached, or both.
```json
{
   "task" : "87427f91-d193-4b25-8d35-e1292a34b5c4",
   "responseType" : "UPDATE",
   "message" : "Processing step 0 of 91",
   "current" : 0,
   "maximum" : 91
}
```

#### COMPLETION

A COMPLETION response is issued to convey that a task has successfully
completed execution, as well as report the values of any task outputs.
```json
{
   "task" : "87427f91-d193-4b25-8d35-e1292a34b5c4",
   "responseType" : "COMPLETION",
   "outputs" : {"result" : 91}
}
```

#### CANCELATION

A CANCELATION response is issued to confirm the success of a CANCEL
request.
```json
{
   "task" : "87427f91-d193-4b25-8d35-e1292a34b5c4",
   "responseType" : "CANCELATION"
}
```

#### FAILURE

A FAILURE response is issued to convey that a task did not completely
and successfully execute, such as an exception being raised.
```json
{
   "task" : "87427f91-d193-4b25-8d35-e1292a34b5c4",
   "responseType" : "FAILURE",
   "error", "Invalid gamma value"}
}
```

## FAQ

Q: How about abstracting the transport layer so protocols besides pipes+JSON
   can be used? Then Appose could work with pipes+pickle, and/or with Google
   Protocol Buffers, Apache Arrow, NATS.io, over HTTP local loopback,
   between machines on the cloud...

A: It is tempting. But simplicity is an important core design goal, and
   additional transport layer implementations would increase complexity.
   There are already a plethora of existing solutions for interprocess
   communication, RPC, and data sharing between processes on the same or
   different machines. The reason Appose exists is to be less complicated
   than those other solutions, while supporting dynamic construction of
   subprocess environments, and access to large data in shared memory.

Q: What about more data types for inputs and outputs? Appose could be plugin
   driven, with extension libraries registering additional externalization
   routines to convert their own favorite kinds of objects to and from JSON.

A: Again, tempting! But nailing down (via either invention or reuse) a
   plugin mechanism for each supported language would increase the size of
   the codebase, and the modularization would make it more complicated to
   depend on Appose. Have you included the right plugins in your dependency
   set? Do they all have the right versions? Where is the bill of materials
   keeping all of the dependencies in sync? Etc. For now, Appose strives to
   be self-contained with all supported types handled by one single library
   per target language.

## Alternatives and complements

* [CuVec](https://github.com/AMYPAD/CuVec)
* [Apache Arrow](https://arrow.apache.org/)
* [NATS.io](https://nats.io/)
