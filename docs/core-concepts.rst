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

One of Appose's key features is **zero-copy tensor sharing** via shared memory. This allows large data structures like tensors to be shared between processes without copying — the data lives in a named memory region that both the host and worker processes can access directly.

SharedMemory
^^^^^^^^^^^^

A ``SharedMemory`` block is a named region of memory accessible to multiple processes. One process creates it; others attach to it using its name.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import appose

         # Create a new named shared memory block (1000 bytes)
         shm = appose.SharedMemory(create=True, rsize=1000)
         name = shm.name  # auto-generated name, e.g. "psm_4f3a2b"

         # Write directly to the buffer
         shm.buf[0] = 42

         # Attach to an existing block (e.g. in another process)
         shm2 = appose.SharedMemory(name=name, create=False, rsize=1000)
         assert shm2.buf[0] == 42

         # Clean up: unlink destroys the block; close only detaches
         shm2.close()   # detach (do not destroy)
         shm.unlink()   # destroy (call once across all processes)

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.SharedMemory;

         // Create a new named shared memory block (1000 bytes)
         SharedMemory shm = SharedMemory.create(1000);
         String name = shm.name();  // auto-generated name, e.g. "psm_4f3a2b"

         // Write to the buffer
         shm.buf().put(0, (byte) 42);

         // Attach to an existing block (e.g. from another process)
         SharedMemory shm2 = SharedMemory.attach(name, 1000);
         assert shm2.buf().get(0) == 42;

         // Clean up: by default, creator destroys; attached only detaches
         shm2.close();  // detach (does not destroy)
         shm.close();   // destroy (creator calls unlink automatically)

The ``rsize`` parameter is the **requested** size in bytes. The actual allocated size may be rounded up to the next page boundary — ``size`` / ``size()`` returns the actual amount.

.. note::

   By default, a block created with ``create=True`` (Python) or ``SharedMemory.create()`` (Java) will be **destroyed** when closed. A block attached with ``create=False`` (Python) or ``SharedMemory.attach()`` (Java) will only be **detached**. Call ``unlink_on_dispose()`` (Python) or ``unlinkOnClose()`` (Java) to override this behavior.

NDArray
^^^^^^^

``NDArray`` wraps a ``SharedMemory`` block and adds **dtype** and **shape** metadata, making it a typed multi-dimensional array. This is the primary way to pass tensor data between processes.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import appose

         # Create a float32 array with shape [7, 512, 512]
         data = appose.NDArray("float32", [7, 512, 512])

         name = data.shm.name  # shared memory name
         dtype = data.dtype    # "float32"
         shape = data.shape    # [7, 512, 512]

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.NDArray;
         import org.apposed.appose.NDArray.DType;
         import org.apposed.appose.NDArray.Shape;
         import static org.apposed.appose.NDArray.Shape.Order.F_ORDER;

         // Create a float32 array with shape (7, 512, 512) in F_ORDER
         NDArray data = new NDArray(DType.FLOAT32, new Shape(F_ORDER, 7, 512, 512));

         String name  = data.shm().name();  // shared memory name
         DType  dtype = data.dType();        // DType.FLOAT32
         Shape  shape = data.shape();        // Shape(F_ORDER, 7, 512, 512)

Data Types
""""""""""

The ``dtype`` (Python) / ``DType`` (Java) specifies the element type:

.. list-table::
   :header-rows: 1
   :widths: 20 25 15

   * - dtype string
     - Java DType
     - Bytes/element
   * - ``int8``
     - ``DType.INT8``
     - 1
   * - ``uint8``
     - ``DType.UINT8``
     - 1
   * - ``int16``
     - ``DType.INT16``
     - 2
   * - ``uint16``
     - ``DType.UINT16``
     - 2
   * - ``int32``
     - ``DType.INT32``
     - 4
   * - ``uint32``
     - ``DType.UINT32``
     - 4
   * - ``int64``
     - ``DType.INT64``
     - 8
   * - ``uint64``
     - ``DType.UINT64``
     - 8
   * - ``float32``
     - ``DType.FLOAT32``
     - 4
   * - ``float64``
     - ``DType.FLOAT64``
     - 8
   * - ``complex64``
     - ``DType.COMPLEX64``
     - 8
   * - ``complex128``
     - ``DType.COMPLEX128``
     - 16
   * - ``bool``
     - ``DType.BOOL``
     - 1

Shape and Axis Order
""""""""""""""""""""

Python's ``shape`` is a list of dimensions in **C order** (row-major, NumPy convention), where the last axis changes fastest in memory.

Java's ``Shape`` additionally carries an explicit **axis order**:

* ``C_ORDER`` — fastest-moving dimension first (NumPy/C convention)
* ``F_ORDER`` — fastest-moving dimension last (ImgLib2/Fortran convention)

When an NDArray crosses language boundaries, both sides see the same raw memory layout. A Java ``Shape(F_ORDER, 4, 3, 2)`` corresponds to Python shape ``[2, 3, 4]`` in C order — the memory layout is identical; only the axis interpretation differs.

Passing NDArrays to Workers
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``NDArray`` objects can be placed directly in task inputs and outputs. Appose serializes only the **metadata** (name, dtype, shape) — not the array data itself. The worker reconstructs the NDArray by attaching to the same named shared memory block.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import appose

         env = appose.system()
         with env.python() as service:
             # Create array in host process and fill with data
             data = appose.NDArray("float32", [512, 512])
             data.ndarray()[:] = 1.0

             # Worker receives it as an appose.NDArray and calls .ndarray()
             script = "task.outputs['total'] = float(data.ndarray().sum())"
             task = service.task(script, {"data": data})
             task.wait_for()
             print(task.outputs["total"])  # 262144.0

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;
         import org.apposed.appose.NDArray.DType;
         import org.apposed.appose.NDArray.Shape;
         import static org.apposed.appose.NDArray.Shape.Order.F_ORDER;
         import java.nio.FloatBuffer;
         import java.util.HashMap;
         import java.util.Map;

         Environment env = Appose.system();
         try (Service service = env.python()) {
             // Create array in host process and fill with data
             NDArray data = new NDArray(DType.FLOAT32, new Shape(F_ORDER, 512, 512));
             FloatBuffer buf = data.buffer().asFloatBuffer();
             for (int i = 0; i < 512 * 512; i++) buf.put(i, 1.0f);

             // Worker receives it as an appose.NDArray and calls .ndarray()
             String script = "task.outputs['total'] = float(data.ndarray().sum())";
             Map<String, Object> inputs = new HashMap<>();
             inputs.put("data", data);
             Task task = service.task(script, inputs);
             task.waitFor();
             System.out.println(task.outputs.get("total"));  // 262144.0
         }

NumPy Integration (Python)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Python, call ``ndarray()`` on an ``NDArray`` to get a **zero-copy NumPy array** backed by the shared memory:

.. code-block:: python

   import appose
   import numpy as np

   data = appose.NDArray("float32", [7, 512, 512])
   arr = data.ndarray()  # numpy.ndarray, shape (7, 512, 512), dtype float32

   # Any numpy operation reads and writes shared memory directly — no copying
   arr[0] = np.zeros((512, 512))
   mean = arr.mean()

This works identically in worker scripts — the worker receives the ``NDArray``, calls ``.ndarray()``, and gets a zero-copy NumPy view of the same shared memory.

ImgLib2 Integration (Java)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `imglib2-appose <https://github.com/imglib/imglib2-appose>`_ library bridges Appose's ``NDArray`` with `ImgLib2 <https://imagej.net/libs/imglib2>`_ images for zero-copy integration with Java image processing pipelines.

.. code-block:: java

   import net.imglib2.appose.NDArrays;
   import net.imglib2.appose.ShmImg;
   import net.imglib2.type.numeric.real.FloatType;

   // Create an ShmImg (ImgLib2 Img backed by shared memory)
   ShmImg<FloatType> img = new ShmImg<>(new FloatType(), 512, 512);

   // Use it like any ImgLib2 Img
   for (FloatType pixel : img)
       pixel.set(1.0f);

   // Extract the NDArray to pass to a worker (zero-copy: same shared memory)
   NDArray data = img.ndArray();

   // Wrap an existing NDArray as an ImgLib2 image (also zero-copy)
   ArrayImg<FloatType, ?> view = NDArrays.asArrayImg(data, new FloatType());

   // Convert any RandomAccessibleInterval (copies if not already shared memory)
   NDArray copied = NDArrays.asNDArray(img);

The type mapping between ImgLib2 and Appose:

.. list-table::
   :header-rows: 1
   :widths: 35 25

   * - ImgLib2 Type
     - NDArray DType
   * - ``ByteType`` / ``UnsignedByteType``
     - ``INT8`` / ``UINT8``
   * - ``ShortType`` / ``UnsignedShortType``
     - ``INT16`` / ``UINT16``
   * - ``IntType`` / ``UnsignedIntType``
     - ``INT32`` / ``UINT32``
   * - ``LongType`` / ``UnsignedLongType``
     - ``INT64`` / ``UINT64``
   * - ``FloatType``
     - ``FLOAT32``
   * - ``DoubleType``
     - ``FLOAT64``
   * - ``ComplexFloatType``
     - ``COMPLEX64``
   * - ``ComplexDoubleType``
     - ``COMPLEX128``
   * - ``NativeBoolType``
     - ``BOOL``

.. note::

   ImgLib2 uses F_ORDER (column-major) axis ordering by convention. An ``ShmImg`` created with dimensions ``[4, 3, 2]`` in Java will appear to Python as shape ``[2, 3, 4]`` in C order — the same memory layout, with axes in reverse order.

Shared Memory Lifecycle
^^^^^^^^^^^^^^^^^^^^^^^

Use context managers (Python) or try-with-resources (Java) for reliable cleanup:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         # NDArray context manager disposes the underlying SharedMemory
         with appose.NDArray("float32", [512, 512]) as data:
             arr = data.ndarray()
             # ... work with arr ...
         # shared memory released here

         # SharedMemory context manager
         with appose.SharedMemory(create=True, rsize=1000) as shm:
             shm.buf[0] = 42
         # shared memory released here

   .. tab:: Java

      .. code-block:: java

         // NDArray implements AutoCloseable
         try (NDArray data = new NDArray(DType.FLOAT32, new Shape(F_ORDER, 512, 512))) {
             FloatBuffer buf = data.buffer().asFloatBuffer();
             // ... work with buf ...
         } // shared memory released here

         // SharedMemory implements AutoCloseable
         try (SharedMemory shm = SharedMemory.create(1000)) {
             shm.buf().put(0, (byte) 42);
         } // shared memory released here

.. important::

   The shared memory block should be **unlinked exactly once** across all processes — this destroys the underlying OS resource. The process that **created** the block is responsible; processes that **attached** should only close their connection. Appose enforces this automatically through the ``unlinkOnClose`` / ``unlink_on_dispose`` defaults.
