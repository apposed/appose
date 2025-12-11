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

Here's a minimal worker in Python:

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

Appose uses JSON for serialization, which supports:

* Numbers (integers and floats)
* Strings
* Booleans
* Arrays/lists
* Objects/dictionaries
* null

For complex types (like tensors), use **shared memory** with NDArrays. The shared memory name is passed as a string in inputs/outputs, and both sides can access the data without copying.

.. note::

   Shared memory support is currently being enhanced. Check your language implementation's documentation for current capabilities.

Testing Your Worker
-------------------

To test a custom worker:

1. **Run the worker manually** and send it JSON requests via stdin
2. **Verify responses** match the expected format
3. **Test error cases** (invalid script, cancelation, etc.)
4. **Integrate with Appose** using ``env.service("your-worker", ...)``

Example manual test:

.. code-block:: bash

   # Start your worker
   ./my-worker

   # Send an EXECUTE request (paste this as one line)
   {"task":"test-123","requestType":"EXECUTE","script":"result = 5 + 6","inputs":{}}

   # Expected responses:
   {"task":"test-123","responseType":"LAUNCH"}
   {"task":"test-123","responseType":"COMPLETION","outputs":{"result":11}}
