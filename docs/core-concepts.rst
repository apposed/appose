Core Concepts
=============

Understanding Appose's core concepts will help you make the most of its capabilities.

Architecture Overview
---------------------

Appose follows a simple four-layer architecture:

.. code-block:: text

   ┌─────────────┐
   │   Builder   │  Create environments with dependencies
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ Environment │  Configured environment with executables
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │   Service   │  Access to worker process
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │    Task     │  Asynchronous operation (analogous to Future)
   └─────────────┘

Builder
-------

A **Builder** is responsible for creating environments with specific dependencies. Appose provides several builder types:

Builder Types
^^^^^^^^^^^^^

**PixiBuilder** (Recommended)
   Modern package manager supporting both conda and PyPI packages.

   .. tabs::

      .. tab:: Python

         .. code-block:: python

            env = appose.pixi() \
                .conda("python>=3.10", "numpy") \
                .pypi("cowsay") \
                .channels("conda-forge") \
                .build("my-env")

      .. tab:: Java

         .. code-block:: java

            Environment env = Appose.pixi()
                .conda("python>=3.10", "numpy")
                .pypi("cowsay")
                .channels("conda-forge")
                .build("my-env");

**MambaBuilder**
   Traditional conda environments via micromamba.

   .. tabs::

      .. tab:: Python

         .. code-block:: python

            env = appose.mamba("environment.yml").build()

      .. tab:: Java

         .. code-block:: java

            Environment env = Appose.mamba("environment.yml")
                .build();

**UvBuilder**
   Fast Python virtual environments via uv.

   .. tabs::

      .. tab:: Python

         .. code-block:: python

            env = appose.uv() \
                .python("3.11") \
                .include("numpy", "pandas") \
                .build("my-env")

      .. tab:: Java

         .. code-block:: java

            Environment env = Appose.uv()
                .python("3.11")
                .include("numpy", "pandas")
                .build("my-env");

**SystemBuilder**
   Uses system PATH without installing packages.

   .. tabs::

      .. tab:: Python

         .. code-block:: python

            env = appose.system()

      .. tab:: Java

         .. code-block:: java

            Environment env = Appose.system();

Builder Features
^^^^^^^^^^^^^^^^

All builders support monitoring build progress:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         def progress_callback(progress):
             print(f"Progress: {progress.current}/{progress.total}")

         env = appose.pixi() \
             .conda("python>=3.10", "numpy") \
             .subscribe_progress(progress_callback) \
             .subscribe_output(lambda line: print(f"Output: {line}")) \
             .subscribe_error(lambda line: print(f"Error: {line}", file=sys.stderr)) \
             .build("my-env")

         # Or simply log everything:
         env = appose.pixi() \
             .conda("python>=3.10", "numpy") \
             .log_debug() \
             .build("my-env")

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.pixi()
             .conda("python>=3.10", "numpy")
             .subscribeProgress(progress -> {
                 System.out.println("Progress: " + progress.current + "/" + progress.total);
             })
             .subscribeOutput(line -> System.out.println("Output: " + line))
             .subscribeError(line -> System.err.println("Error: " + line))
             .build("my-env");

         // Or simply log everything to stderr:
         Environment env = Appose.pixi()
             .conda("python>=3.10", "numpy")
             .logDebug()
             .build("my-env");

Environment
-----------

An **Environment** represents a configured environment with executables and dependencies. It provides three key properties:

* **base**: The root directory of the environment
* **binPaths**: Directories to search for executables
* **launchArgs**: Arguments to prepend when launching workers

Creating Workers
^^^^^^^^^^^^^^^^

Environments provide methods to create worker services:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         env = appose.system()

         # Create a Python worker
         python = env.python()

         # Create a Groovy worker
         groovy = env.groovy()

         # Create a Java worker
         java_worker = env.java()

         # Create a custom worker
         custom = env.service("my-worker", "arg1", "arg2")

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.system();

         // Create a Python worker
         Service python = env.python();

         // Create a Groovy worker
         Service groovy = env.groovy();

         // Create a Java worker
         Service java = env.java();

         // Create a custom worker
         Service custom = env.service("my-worker", "arg1", "arg2");

Service
-------

A **Service** provides access to a worker process running in a separate process. The service manages communication between your main process and the worker.

Service Lifecycle
^^^^^^^^^^^^^^^^^

Services should be properly closed when done to clean up resources:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         # Using context manager (recommended)
         with env.python() as python:
             # Use the service
         # Automatically closed

         # Manual management
         python = env.python()
         try:
             # Use the service
         finally:
             python.close()

   .. tab:: Java

      .. code-block:: java

         // Using try-with-resources (recommended)
         try (Service python = env.python()) {
             // Use the service
         } // Automatically closed

         // Manual management
         Service python = env.python();
         try {
             // Use the service
         } finally {
             python.close();
         }

Creating Tasks
^^^^^^^^^^^^^^

Services create tasks to execute scripts:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         with env.python() as python:
             task = python.task("result = 5 + 6")

   .. tab:: Java

      .. code-block:: java

         try (Service python = env.python()) {
             Task task = python.task("result = 5 + 6");
         }

Task
----

A **Task** represents an asynchronous operation performed by a service. Tasks are analogous to Futures/Promises in other frameworks.

Task Lifecycle
^^^^^^^^^^^^^^

Tasks go through several states during execution:

.. code-block:: text

   READY → RUNNING → COMPLETE
                   ↘ CANCELED
                   ↘ FAILED
                   ↘ CRASHED

Task States:

* **READY**: Task created but not yet started
* **RUNNING**: Task is currently executing
* **COMPLETE**: Task finished successfully
* **CANCELED**: Task was canceled before completion
* **FAILED**: Task encountered an error
* **CRASHED**: Worker process crashed

Executing Tasks
^^^^^^^^^^^^^^^

There are two ways to execute tasks:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         # 1. Fire and forget (starts immediately)
         task = python.task(script)
         task.wait_for()

         # 2. Deferred execution (start manually)
         task = python.task(script)
         # ... do other setup ...
         task.start()
         task.wait_for()

   .. tab:: Java

      .. code-block:: java

         // 1. Fire and forget (starts immediately)
         Task task = python.task(script);
         task.waitFor();

         // 2. Deferred execution (start manually)
         Task task = python.task(script);
         // ... do other setup ...
         task.start();
         task.waitFor();

Task Inputs and Outputs
^^^^^^^^^^^^^^^^^^^^^^^^

Tasks can receive inputs and produce outputs:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         task = python.task("output = input1 + input2")
         task.inputs["input1"] = 5
         task.inputs["input2"] = 6
         task.wait_for()
         result = task.outputs["output"]
         # result == 11

   .. tab:: Java

      .. code-block:: java

         Task task = python.task("output = input1 + input2");
         task.inputs.put("input1", 5);
         task.inputs.put("input2", 6);
         task.waitFor();
         Object result = task.outputs.get("output");
         // result == 11

 .. _non-serializable-objects-and-proxies:

Non-Serializable Objects and Proxies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a task returns an object that cannot be represented in JSON (such as a Python ``datetime`` instance or a custom class), Appose automatically exports it to the worker and returns a **proxy object** that you can use to interact with the remote object:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         # Task returns a datetime object
         task = python.task("import datetime; datetime.datetime.now()")
         task.wait_for()
         now = task.outputs.get("result")
         # now is a ProxyObject wrapping the remote datetime instance
         
         year = now.year  # Access attributes
         weekday = now.weekday()  # Call methods

   .. tab:: Java

      .. code-block:: java

         // Task returns a datetime object
         Task task = python.task("import datetime; datetime.datetime.now()");
         task.waitFor();
         WorkerObject now = (WorkerObject) task.outputs.get("result");
         // now is a reference to the remote datetime instance
         
         // Access attributes
         int year = (Integer) now.getAttribute("year");
         
         // Or create a strongly-typed proxy for method calls
         interface DateTime {
             int weekday();
             float timestamp();
         }
         DateTime dt = now.proxy(DateTime.class);
         int weekday = dt.weekday();

This feature enables seamless interaction with objects that live in the worker process. For detailed information on how this works under the hood, see :doc:`worker-protocol` (the "WorkerObject (Auto-Proxified Objects)" section under "Data Type Considerations").

Task Callbacks
^^^^^^^^^^^^^^

Tasks provide callbacks for monitoring progress:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         from appose import ResponseType

         def task_listener(event):
             if event.response_type == ResponseType.LAUNCH:
                 print("Task started")
             elif event.response_type == ResponseType.UPDATE:
                 print(f"Progress: {task.current}/{task.maximum}")
             elif event.response_type == ResponseType.COMPLETION:
                 print("Task completed successfully")
             elif event.response_type == ResponseType.FAILURE:
                 print(f"Task failed: {task.error}", file=sys.stderr)

         task = python.task(script)
         task.listen(task_listener)
         task.wait_for()

   .. tab:: Java

      .. code-block:: java

         Task task = python.task(script);
         task.listen(event -> {
             switch (event.responseType) {
                 case LAUNCH:
                     System.out.println("Task started");
                     break;
                 case UPDATE:
                     System.out.println("Progress: " + task.current + "/" + task.maximum);
                     break;
                 case COMPLETION:
                     System.out.println("Task completed successfully");
                     break;
                 case FAILURE:
                     System.err.println("Task failed: " + task.error);
                     break;
             }
         });
         task.waitFor();

Canceling Tasks
^^^^^^^^^^^^^^^

Long-running tasks can be canceled:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         task = python.task(long_running_script)
         # ... wait a bit ...
         if not task.status.is_finished():
             task.cancel()
         task.wait_for()

   .. tab:: Java

      .. code-block:: java

         Task task = python.task(longRunningScript);
         // ... wait a bit ...
         if (!task.status.isFinished()) {
             task.cancel();
         }
         task.waitFor();

Worker
------

A **Worker** is a separate process created by Appose to perform asynchronous computation. Workers communicate with services via JSON over stdin/stdout.

Built-in Workers
^^^^^^^^^^^^^^^^

Appose comes with two built-in worker implementations:

* **python_worker**: Runs Python scripts
* **GroovyWorker**: Runs Groovy scripts

Task Context in Workers
^^^^^^^^^^^^^^^^^^^^^^^^

Within worker scripts, a ``task`` object is available with the following:

.. tabs::

   .. tab:: Groovy

      .. code-block:: groovy

         // Access inputs
         value = task.inputs["my_input"]

         // Set outputs
         task.outputs["my_output"] = result

         // Report progress
         task.update("Processing...", 5, 10)

         // Check for cancelation
         if (task.cancelRequested) {
             task.cancel()
         }

   .. tab:: Python

      .. code-block:: python

         # Access inputs
         value = task.inputs["my_input"]

         # Set outputs
         task.outputs["my_output"] = result

         # Report progress
         task.update(current=5, maximum=10, message="Processing...")

         # Check for cancelation
         if task.cancel_requested:
             task.cancel()

Custom Workers
^^^^^^^^^^^^^^

You can create custom workers that implement the Appose worker protocol. See :doc:`worker-protocol` for details.

Shared Memory
-------------

One of Appose's key features is **zero-copy tensor sharing** via shared memory. This allows large data structures (like tensors) to be shared between processes without copying.

.. note::

   Shared memory support is currently being enhanced. Check the API documentation for your language implementation for current capabilities.

The shared memory system is:

* **Platform-agnostic**: Works on Linux, macOS, and Windows
* **Efficient**: No data copying required
* **Named**: Buffers are identified by name for easy access
* **Automatic cleanup**: Shared memory is automatically released when no longer needed
