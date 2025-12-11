Worker Protocol
===============

The Appose worker protocol defines how services communicate with worker processes. This document describes the protocol in detail, enabling you to create custom worker implementations.

Protocol Overview
-----------------

Workers are separate processes that communicate with the Appose service via:

* **Standard Input (stdin)**: Receives requests from the service
* **Standard Output (stdout)**: Sends responses to the service
* **Standard Error (stderr)**: Logs and error messages (optional)

All communication uses **JSON-formatted messages**, with one message per line.

Worker Contract
---------------

A worker process must:

1. Accept **requests** in Appose's request format on stdin
2. Issue **responses** in Appose's response format on stdout
3. Handle each request appropriately and in a timely manner
4. Use UUIDs to track tasks across the request/response lifecycle

Request Format
--------------

A **request** is a single line of JSON with the following structure:

Common Fields
^^^^^^^^^^^^^

All requests include:

* ``task``: A UUID string identifying the task
* ``requestType``: The type of request (``EXECUTE`` or ``CANCEL``)

Request Types
^^^^^^^^^^^^^

EXECUTE
~~~~~~~

Asynchronously execute a script within the worker process.

**Structure:**

.. code-block:: json

   {
      "task": "87427f91-d193-4b25-8d35-e1292a34b5c4",
      "requestType": "EXECUTE",
      "script": "task.outputs[\"result\"] = computeResult(gamma)\n",
      "inputs": {"gamma": 2.2}
   }

**Fields:**

* ``task`` (string): UUID of the task
* ``requestType`` (string): Must be ``"EXECUTE"``
* ``script`` (string): The script code to execute
* ``inputs`` (object, optional): Key-value pairs of input data

The worker should:

1. Parse the request
2. Send a ``LAUNCH`` response immediately to confirm receipt
3. Execute the script asynchronously
4. Make inputs available to the script in a ``task.inputs`` map/dictionary
5. Provide a ``task.outputs`` map/dictionary for the script to populate
6. Send ``UPDATE`` responses as the task progresses (optional)
7. Send a ``COMPLETION`` response with outputs when done
8. Send a ``FAILURE`` response if an error occurs

CANCEL
~~~~~~

Cancel a running task.

**Structure:**

.. code-block:: json

   {
      "task": "87427f91-d193-4b25-8d35-e1292a34b5c4",
      "requestType": "CANCEL"
   }

**Fields:**

* ``task`` (string): UUID of the task to cancel
* ``requestType`` (string): Must be ``"CANCEL"``

The worker should:

1. Mark the task for cancelation
2. Make ``task.cancel_requested`` / ``task.cancelRequested`` true in the script context
3. Allow the script to check this flag and terminate gracefully
4. Send a ``CANCELATION`` response when the task is canceled

Response Format
---------------

A **response** is a single line of JSON with the following structure:

Common Fields
^^^^^^^^^^^^^

All responses include:

* ``task``: A UUID string identifying the task (must match the request)
* ``responseType``: The type of response

Response Types
^^^^^^^^^^^^^^

LAUNCH
~~~~~~

Confirms successful receipt of an ``EXECUTE`` request.

**Structure:**

.. code-block:: json

   {
      "task": "87427f91-d193-4b25-8d35-e1292a34b5c4",
      "responseType": "LAUNCH"
   }

**Fields:**

* ``task`` (string): UUID of the task
* ``responseType`` (string): Must be ``"LAUNCH"``

**When to send:** Immediately after receiving an ``EXECUTE`` request.

UPDATE
~~~~~~

Indicates progress during task execution.

**Structure:**

.. code-block:: json

   {
      "task": "87427f91-d193-4b25-8d35-e1292a34b5c4",
      "responseType": "UPDATE",
      "message": "Processing step 0 of 91",
      "current": 0,
      "maximum": 91
   }

**Fields:**

* ``task`` (string): UUID of the task
* ``responseType`` (string): Must be ``"UPDATE"``
* ``message`` (string, optional): Human-readable progress message
* ``current`` (number, optional): Current progress value
* ``maximum`` (number, optional): Maximum progress value

**When to send:** Periodically during long-running tasks to report progress.

COMPLETION
~~~~~~~~~~

Indicates successful task completion and returns outputs.

**Structure:**

.. code-block:: json

   {
      "task": "87427f91-d193-4b25-8d35-e1292a34b5c4",
      "responseType": "COMPLETION",
      "outputs": {"result": 91}
   }

**Fields:**

* ``task`` (string): UUID of the task
* ``responseType`` (string): Must be ``"COMPLETION"``
* ``outputs`` (object): Key-value pairs of output data

**When to send:** After the task script completes successfully.

CANCELATION
~~~~~~~~~~~

Confirms successful cancelation of a task.

**Structure:**

.. code-block:: json

   {
      "task": "87427f91-d193-4b25-8d35-e1292a34b5c4",
      "responseType": "CANCELATION"
   }

**Fields:**

* ``task`` (string): UUID of the task
* ``responseType`` (string): Must be ``"CANCELATION"``

**When to send:** After a task has been successfully canceled.

FAILURE
~~~~~~~

Indicates that a task failed to complete.

**Structure:**

.. code-block:: json

   {
      "task": "87427f91-d193-4b25-8d35-e1292a34b5c4",
      "responseType": "FAILURE",
      "error": "Invalid gamma value"
   }

**Fields:**

* ``task`` (string): UUID of the task
* ``responseType`` (string): Must be ``"FAILURE"``
* ``error`` (string): Error message or stack trace

**When to send:** When a task encounters an error or exception.

Task Context
------------

Within the executing script, workers must provide a ``task`` object with:

Required Properties
^^^^^^^^^^^^^^^^^^^

* ``task.inputs`` (map/dict): Input values from the request
* ``task.outputs`` (map/dict): Output values to return in COMPLETION response
* ``task.cancel_requested`` / ``task.cancelRequested`` (boolean): True if cancelation was requested

Required Methods
^^^^^^^^^^^^^^^^

* ``task.update(current, maximum, message)`` or ``task.update(message, current, maximum)``: Send an UPDATE response
* ``task.cancel()``: Mark the task as canceled and send a CANCELATION response

Example Implementation Flow
----------------------------

Here's a complete example of the request/response flow:

1. **Service sends EXECUTE request:**

   .. code-block:: json

      {
         "task": "abc-123",
         "requestType": "EXECUTE",
         "script": "result = x * 2",
         "inputs": {"x": 5}
      }

2. **Worker sends LAUNCH response:**

   .. code-block:: json

      {
         "task": "abc-123",
         "responseType": "LAUNCH"
      }

3. **Worker executes script and sends UPDATE responses (optional):**

   .. code-block:: json

      {
         "task": "abc-123",
         "responseType": "UPDATE",
         "message": "Computing...",
         "current": 50,
         "maximum": 100
      }

4. **Worker sends COMPLETION response:**

   .. code-block:: json

      {
         "task": "abc-123",
         "responseType": "COMPLETION",
         "outputs": {"result": 10}
      }

Reference Implementations
-------------------------

Appose provides two reference worker implementations:

Python Worker
^^^^^^^^^^^^^

The ``python_worker`` module implements the protocol in Python. Key features:

* Executes Python scripts using ``exec()``
* Provides a ``task`` object to scripts with ``inputs``, ``outputs``, ``cancel_requested``
* Handles multiple concurrent tasks via threading
* Source: https://github.com/apposed/appose-python

Groovy Worker
^^^^^^^^^^^^^

The ``GroovyWorker`` class implements the protocol in Groovy/Java. Key features:

* Executes Groovy scripts using ``GroovyShell``
* Provides a ``task`` object with ``inputs``, ``outputs``, ``cancelRequested``
* Handles multiple concurrent tasks via threading
* Source: https://github.com/apposed/appose-java

Creating Custom Workers
------------------------

To create a custom worker:

1. **Choose your language/platform** for the worker
2. **Read requests from stdin** one line at a time
3. **Parse JSON** to extract task UUID, request type, and parameters
4. **Send LAUNCH response** immediately for EXECUTE requests
5. **Execute scripts** with access to task context
6. **Send responses** to stdout as JSON lines
7. **Handle CANCEL requests** by setting a flag scripts can check

Minimal Worker Example
^^^^^^^^^^^^^^^^^^^^^^

Here's a minimal (single-threaded) worker in Python:

.. code-block:: python

   import sys
   import json
   from uuid import UUID

   while True:
       # Read request
       line = sys.stdin.readline()
       if not line:
           break

       request = json.loads(line)
       task_id = request["task"]
       request_type = request["requestType"]

       if request_type == "EXECUTE":
           # Send LAUNCH
           print(json.dumps({"task": task_id, "responseType": "LAUNCH"}))
           sys.stdout.flush()

           # Execute script
           try:
               script = request["script"]
               inputs = request.get("inputs", {})

               # Minimal task context
               outputs = {}

               # Execute the script
               exec(script, {"task_inputs": inputs, "task_outputs": outputs})

               # Send COMPLETION
               print(json.dumps({
                   "task": task_id,
                   "responseType": "COMPLETION",
                   "outputs": outputs
               }))
               sys.stdout.flush()

           except Exception as e:
               # Send FAILURE
               print(json.dumps({
                   "task": task_id,
                   "responseType": "FAILURE",
                   "error": str(e)
               }))
               sys.stdout.flush()

       elif request_type == "CANCEL":
           # Send CANCELATION
           # Note: Single-threaded worker cannot actually honor task cancelations.
           print(json.dumps({"task": task_id, "responseType": "CANCELATION"}))
           sys.stdout.flush()

Best Practices
--------------

1. **Always flush stdout** after writing responses
2. **Validate JSON** before processing requests
3. **Handle errors gracefully** and send FAILURE responses
4. **Support cancelation** by checking flags periodically in long scripts
5. **Use UUIDs correctly** to match responses to requests
6. **Keep responses line-delimited** (one JSON object per line, no pretty-printing)
7. **Log to stderr** to avoid interfering with the protocol on stdout
8. **Test with multiple concurrent tasks** if your worker supports them

Data Type Considerations
------------------------

Appose uses JSON for serialization, which natively supports:

* Numbers (integers and floats)
* Strings
* Booleans
* Arrays/lists
* Objects/dictionaries
* null

Beyond JSON-Native Types
^^^^^^^^^^^^^^^^^^^^^^^^^

For data types that JSON cannot represent natively, Appose uses a special encoding scheme: complex objects are wrapped in a dictionary with an ``appose_type`` key that identifies the object type. This allows seamless serialization of domain-specific types like shared memory blocks and multi-dimensional arrays.

The worker implementations automatically handle encoding and decoding of these types. When your script produces a non-serializable object (e.g., a Python ``datetime`` instance), it is automatically exported and returned as a reference that you can interact with.

Supported Extended Types
^^^^^^^^^^^^^^^^^^^^^^^^

SharedMemory
~~~~~~~~~~~~

Represents a shared memory block for zero-copy data sharing.

**Structure:**

.. code-block:: json

   {
      "appose_type": "shm",
      "name": "psm_4812f794",
      "rsize": 16384
   }

**Fields:**

* :code:`appose_type`: Must be :code:`"shm"`
* :code:`name`: Unique identifier for the shared memory segment (OS-level name)
* :code:`rsize`: Requested/nominal size in bytes (as required by shared memory constructors)

NDArray
~~~~~~~

Represents a multi-dimensional array backed by shared memory, enabling efficient tensor sharing.

**Structure:**

.. code-block:: json

   {
      "appose_type": "ndarray",
      "dtype": "float32",
      "shape": [2, 3, 4],
      "shm": {
         "appose_type": "shm",
         "name": "psm_4812f794",
         "rsize": 16384
      }
   }

**Fields:**

* :code:`appose_type`: Must be :code:`"ndarray"`
* :code:`dtype`: Data type of array elements (e.g., :code:`"float32"`, :code:`"int64"`)
* :code:`shape`: Array dimensions as a list of integers (in C-order)
* :code:`shm`: A SharedMemory object containing the actual data

WorkerObject (Remote Object Proxies)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a worker script returns a non-JSON-serializable object (such as a Python datetime, Java object, or custom class instance), the worker automatically exports it with a generated variable name and returns a reference to it. This reference is converted into a proxy object on the client side, allowing you to interact with the remote object naturally.

**Structure:**

.. code-block:: json

   {
      "appose_type": "worker_object",
      "var_name": "_appose_auto_0"
   }

**Fields:**

* :code:`appose_type`: Must be :code:`"worker_object"`
* :code:`var_name`: The exported variable name in the worker process

.. _worker-object-protocol:

**Usage:**

When you receive a WorkerObject, the client libraries automatically convert it to a proxy object. You can access attributes directly or create a strongly-typed proxy for method calls:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         # Worker returns a datetime object
         now = service.task("import datetime; datetime.datetime.now()").wait_for().result()
         # now is a ProxyObject wrapping the remote datetime instance
         year = now.year  # Accesses the year attribute remotely
         weekday = now.weekday()  # Calls a method remotely

   .. tab:: Java

      .. code-block:: java

         // Worker returns a datetime object
         WorkerObject now = (WorkerObject) service.task(
             "import datetime; datetime.datetime.now()"
         ).waitFor().result();
         
         // Access attributes directly
         int year = (Integer) now.getAttribute("year");
         
         // Or create a strongly-typed proxy for method calls
         interface DateTime {
             int weekday();
             float timestamp();
         }
         DateTime dt = now.proxy(DateTime.class);
         int weekday = dt.weekday();
         float timestamp = dt.timestamp();

For an introduction to using proxies with task outputs, see the :doc:`core-concepts` documentation (the "Non-Serializable Objects and Proxies" section under "Task" subsections).

Encoding Rules
^^^^^^^^^^^^^^

When serializing data to JSON:

1. **Natively serializable types** (strings, numbers, booleans, lists, maps) are encoded as-is
2. **SharedMemory** objects are wrapped with :code:`appose_type: "shm"`
3. **NDArray** objects are wrapped with :code:`appose_type: "ndarray"` (includes their SharedMemory)
4. **Non-serializable objects** (in worker mode only) are auto-exported and wrapped with :code:`appose_type: "worker_object"`

Auto-export enables transparent handling of objects that cannot be serialized: the worker automatically persists them for future access, and the client receives a proxy to interact with them.

Decoding Rules
^^^^^^^^^^^^^^

When deserializing JSON:

1. **Check for** :code:`appose_type` **key** in dictionary objects
2. **If** :code:`"shm"`: Reconstruct a SharedMemory object from the name and size
3. **If** :code:`"ndarray"`: Reconstruct an NDArray, recursively decoding the embedded SharedMemory
4. **If** :code:`"worker_object"`: (Client-side only) Convert to a proxy object for remote method/attribute access
5. **Otherwise**: Return the dictionary or value as-is

Testing Your Worker
-------------------

To test a custom worker:

1. **Run the worker manually** and send it JSON requests via stdin
2. **Verify responses** match the expected format
3. **Test error cases** (invalid script, cancelation, etc.)
4. **Integrate with Appose** using ``env.service("my-worker", ...)``

Example manual test:

.. code-block:: bash

   # Start your worker
   ./my-worker

   # Send an EXECUTE request (paste this as one line)
   {"task":"test-123","requestType":"EXECUTE","script":"result = 5 + 6","inputs":{}}

   # Expected responses:
   {"task":"test-123","responseType":"LAUNCH"}
   {"task":"test-123","responseType":"COMPLETION","outputs":{"result":11}}
