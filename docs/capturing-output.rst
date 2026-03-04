Capturing Output
================

Appose has several distinct layers that produce output, errors, and progress
information. Each layer has its own API for capturing that information.
This page documents all of them.

.. contents:: On this page
   :local:
   :depth: 2

----

Environment Building
--------------------

When a builder installs packages, the underlying tool (pixi, mamba, uv, etc.)
emits a stream of text. Three subscription methods let you tap into that stream.
All return the builder instance for chaining.

subscribeOutput / subscribe_output
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Captures lines written to **stdout** by the build tool (package download and
install progress, solver output, etc.).

.. tabs::

   .. tab:: Python

      .. code-block:: python

         env = appose.pixi() \
             .conda("numpy") \
             .subscribe_output(lambda line: print("OUT:", line, end="")) \
             .build()

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.pixi()
             .conda("numpy")
             .subscribeOutput(line -> System.out.print("OUT: " + line))
             .build();

subscribeError / subscribe_error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Captures lines written to **stderr** by the build tool (warnings, verbose
diagnostics, etc.).

.. tabs::

   .. tab:: Python

      .. code-block:: python

         env = appose.pixi() \
             .conda("numpy") \
             .subscribe_error(lambda line: print("ERR:", line, end="")) \
             .build()

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.pixi()
             .conda("numpy")
             .subscribeError(line -> System.err.print("ERR: " + line))
             .build();

subscribeProgress / subscribe_progress
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Receives structured **progress events** (title, current step, total steps).
Useful for driving a progress bar.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         def on_progress(title, current, total):
             pct = 100 * current // total if total else 0
             print(f"[{pct:3d}%] {title}")

         env = appose.pixi() \
             .conda("numpy") \
             .subscribe_progress(on_progress) \
             .build()

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.pixi()
             .conda("numpy")
             .subscribeProgress((title, current, total) -> {
                 long pct = total > 0 ? 100 * current / total : 0;
                 System.out.printf("[%3d%%] %s%n", pct, title);
             })
             .build();

logDebug / log_debug
^^^^^^^^^^^^^^^^^^^^^

A convenience shorthand that forwards both stdout and stderr to the process's
own stderr. Equivalent to combining ``subscribeOutput`` and ``subscribeError``
with ``System.err.print`` / ``print(..., file=sys.stderr)``.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         env = appose.pixi().conda("numpy").log_debug().build()

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.pixi().conda("numpy").logDebug().build();

.. note::

   All four methods work equally during ``build()`` **and** ``wrap()``.
   When wrapping an existing pixi project, Appose runs ``pixi install`` to
   ensure the environment is up-to-date; that invocation's output flows
   through the same subscribed callbacks.

Catching BuildException
^^^^^^^^^^^^^^^^^^^^^^^^

When a build fails, Appose throws ``BuildException``. The exception message
includes the underlying cause (e.g. the captured stderr of the failed tool
invocation) and can be inspected directly.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         from appose.builder import BuildException

         try:
             env = appose.pixi().conda("not-a-real-package").build()
         except BuildException as e:
             print("Build failed:", e)

   .. tab:: Java

      .. code-block:: java

         try {
             Environment env = Appose.pixi().conda("not-a-real-package").build();
         }
         catch (BuildException e) {
             System.err.println("Build failed: " + e.getMessage());
         }

----

Service and Worker Communication
---------------------------------

Once an environment is built and a worker is running, communication happens
over pipes (stdin/stdout for the Appose JSON protocol; stderr for worker
diagnostics). Three APIs let you observe what is happening.

service.debug
^^^^^^^^^^^^^^

Registers a callback that receives **every low-level protocol event**: JSON
messages sent to the worker (requests) and received from it (responses), plus
internal lifecycle events (worker started, stdout/stderr closed, process
termination). The callback prefix tells you whether the message originated from
the *service* or from the *worker*:

* ``[SERVICE-N]`` — a request sent to the worker, or a lifecycle event
* ``[WORKER-N]`` — a line received from the worker's stderr

This is the most detailed view available.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         service = env.python()
         service.debug(lambda msg: print("[DBG]", msg))
         task = service.task("1 + 1")
         task.wait_for()

   .. tab:: Java

      .. code-block:: java

         Service service = env.python();
         service.debug(msg -> System.out.println("[DBG] " + msg));
         Task task = service.task("1 + 1");
         task.waitFor();

.. tip::

   ``service.debug()`` can be called before the service is started, and it
   also captures ``[WORKER-N]`` lines from stderr in real time — useful when
   debugging crashes.

service.invalidLines / service.invalid_lines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A **list of all non-JSON lines** that the worker emitted on stdout since the
service started. Valid Appose messages are JSON; anything else (e.g. stray
``print()`` calls, crash tracebacks written to stdout) ends up here. This list
is especially useful for post-mortem analysis after a crash.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         for line in service.invalid_lines:
             print("Unexpected stdout:", line)

   .. tab:: Java

      .. code-block:: java

         for (String line : service.invalidLines()) {
             System.out.println("Unexpected stdout: " + line);
         }

service.errorLines / service.error_lines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A **list of all lines** the worker emitted on **stderr** since the service
started. This includes Python ``warnings``, ``logging`` output, uncaught
exception tracebacks, and anything the worker script sends to ``sys.stderr``.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         for line in service.error_lines:
             print("Worker stderr:", line)

   .. tab:: Java

      .. code-block:: java

         for (String line : service.errorLines()) {
             System.out.println("Worker stderr: " + line);
         }

.. note::

   Both invalid lines and error lines are also included automatically in
   the message of any ``CRASHED`` task event, so you don't *have* to inspect
   them yourself after a crash — they surface through the normal task listener
   path.

----

Task Events
-----------

task.listen / task.listen
^^^^^^^^^^^^^^^^^^^^^^^^^^

Registers a listener that is called for **every response the worker sends
for that specific task**. The event carries a ``responseType`` field
indicating which phase the task is in:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Response type
     - When it fires
   * - ``LAUNCH``
     - Worker has begun executing the task's script
   * - ``UPDATE``
     - Worker called ``task.update(...)``; check ``event.message``,
       ``event.current``, and ``event.maximum`` for progress details
   * - ``COMPLETION``
     - Script finished successfully; ``task.outputs`` is now populated
   * - ``CANCELATION``
     - Script was canceled in response to ``task.cancel()``
   * - ``FAILURE``
     - Script raised an unhandled exception; ``task.error`` holds the message
   * - ``CRASH``
     - Worker process terminated unexpectedly; ``task.error`` includes captured
       stdout/stderr from the service

.. tabs::

   .. tab:: Python

      .. code-block:: python

         from appose import ResponseType

         def on_event(event):
             if event.response_type == ResponseType.LAUNCH:
                 print("Task started")
             elif event.response_type == ResponseType.UPDATE:
                 print(f"  {event.current}/{event.maximum}: {event.message}")
             elif event.response_type == ResponseType.COMPLETION:
                 print("Done:", task.outputs.get("result"))
             elif event.response_type == ResponseType.FAILURE:
                 print("Failed:", task.error)
             elif event.response_type == ResponseType.CRASH:
                 print("Crashed:", task.error)

         task = service.task(script)
         task.listen(on_event)
         task.wait_for()

   .. tab:: Java

      .. code-block:: java

         Task task = service.task(script);
         task.listen(event -> {
             switch (event.responseType) {
                 case LAUNCH:
                     System.out.println("Task started");
                     break;
                 case UPDATE:
                     System.out.printf("  %d/%d: %s%n",
                         event.current, event.maximum, event.message);
                     break;
                 case COMPLETION:
                     System.out.println("Done: " + task.outputs.get("result"));
                     break;
                 case FAILURE:
                     System.err.println("Failed: " + task.error);
                     break;
                 case CRASH:
                     System.err.println("Crashed: " + task.error);
                     break;
             }
         });
         task.waitFor();

----

The Stderr Attribution Gap
--------------------------

.. note::

   This section describes a **current limitation** of Appose's design.

A worker process is shared across all tasks submitted to the same service.
Worker stderr is a single stream, and Appose reads it in a dedicated thread
that is completely separate from the per-task message-handling logic. As a
result:

* A line written to ``sys.stderr`` inside a worker script lands in
  ``service.errorLines()`` — it is **not** associated with any specific task.
* With multiple tasks running concurrently, it may not be clear which task
  produced which stderr line.
* Task listeners are never called with stderr content (unless the worker
  crashes, in which case all of ``errorLines`` appears in the ``CRASH`` event).

**Practical guidance:**

* If you run only one task at a time, the ordering of ``errorLines`` and task
  events is sufficient to correlate them manually.
* Use ``service.debug()`` to see stderr lines interleaved in real time with
  protocol events.
* For structured diagnostic output from worker scripts, prefer
  ``task.update(message=...)`` over ``print(..., file=sys.stderr)``; UPDATE
  messages carry the task UUID and are delivered to the right listener.

**The right long-term fix** would be to have the worker capture per-task stderr
(e.g. by redirecting ``sys.stderr`` to a thread-local buffer during task
execution) and emit it as a new protocol response type — say ``STDERR`` — so
the service can dispatch it to the correct task listener with full attribution,
even with concurrent tasks running. But this is not yet implemented.
