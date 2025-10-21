Appose Documentation
====================

**Appose** is a library for interprocess cooperation with shared memory.
The guiding principles are *simplicity* and *efficiency*.

Appose was written to enable **easy execution of Python-based deep learning
from Java without copying tensors**, but its utility extends beyond that.

.. image:: https://github.com/apposed/appose-java/actions/workflows/build.yml/badge.svg
   :target: https://github.com/apposed/appose-java/actions/workflows/build.yml
   :alt: Build Status

Key Features
------------

* **Zero-copy tensor sharing** via shared memory
* **Simple API** with minimal dependencies
* **Multi-language support** - Java, Python, and more
* **Asynchronous execution** with callbacks for status updates
* **Environment management** - build isolated environments with dependencies
* **Flexible architecture** - supports custom worker implementations

Quick Example
-------------

.. tabs::

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.system();
         try (Service python = env.python()) {
             Task task = python.task("5 + 6");
             task.waitFor();
             Object result = task.outputs.get("result");
             // result == 11
         }

   .. tab:: Python

      .. code-block:: python

         import appose
         env = appose.system()
         with env.groovy() as groovy:
             task = groovy.task("5 + 6")
             task.wait_for()
             result = task.outputs["result"]
             # result == 11

How Appose Works
----------------

The workflow for using Appose follows these steps:

1. **Build an Environment** with the dependencies you need
2. **Create a Service** linked to a worker process
3. **Execute scripts** on the worker by launching Tasks
4. **Receive status updates** from tasks asynchronously via callbacks

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   getting-started
   core-concepts
   examples
   worker-protocol

.. toctree::
   :maxdepth: 1
   :caption: Reference

   faq
   alternatives

.. toctree::
   :maxdepth: 1
   :caption: Links

   GitHub Repository <https://github.com/apposed/appose>
   Issue Tracker <https://github.com/apposed/appose/issues>
   Java Implementation <https://github.com/apposed/appose-java>
   Python Implementation <https://github.com/apposed/appose-python>

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
