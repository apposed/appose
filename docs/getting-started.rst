Getting Started
===============

This guide will help you get started with Appose in your preferred programming language.

Installation
------------

.. tabs::

   .. tab:: Python

      **PyPI/Pip**

      Add ``appose`` to your project dependencies in ``pyproject.toml``:

      .. code-block:: toml

         dependencies = [
           "appose"
         ]

      Or install directly:

      .. code-block:: bash

         pip install appose

      **Conda/Mamba**

      Add ``appose`` to your ``environment.yml``:

      .. code-block:: yaml

         dependencies:
           - appose

      Or install directly:

      .. code-block:: bash

         conda install -c conda-forge appose

   .. tab:: Java

      **Maven**

      Add the following dependency to your project's ``pom.xml``:

      .. code-block:: xml

         <dependencies>
           <dependency>
             <groupId>org.apposed</groupId>
             <artifactId>appose</artifactId>
             <version>0.3.0</version>
           </dependency>
         </dependencies>

      **Gradle**

      Add the following to your project's ``build.gradle.kts``:

      .. code-block:: kotlin

         repositories {
             mavenCentral()
         }
         dependencies {
             implementation("org.apposed:appose:0.3.0")
         }

      **JAR Files**

      You can also build from source:

      .. code-block:: bash

         git clone https://github.com/apposed/appose-java.git
         cd appose-java
         mvn package dependency:copy-dependencies

      Then grab the JARs from:

      * ``target/appose-<version>.jar``
      * ``target/dependency/*.jar``

Prerequisites
-------------

.. tabs::

   .. tab:: Python

      To use Appose from Python, you need:

      * **Python 3.10 or higher**
      * **Java 8+** (if calling Java/Groovy workers)

   .. tab:: Java

      To use Appose from Java, you need:

      * **Java 8 or higher** - Appose targets Java 8 compatibility
      * **Python 3.10+ with appose** (if calling Python workers)

      Verify Python availability:

      .. code-block:: bash

         python -c 'import appose'

Your First Appose Program
--------------------------

Let's create a simple program that demonstrates Appose's basic functionality.

.. tabs::

   .. tab:: Python

      Create a file ``hello_appose.py``:

      .. code-block:: python

         import appose

         # Create an environment using the system Java
         env = appose.system()

         # Launch a Groovy worker service
         with env.groovy() as groovy:
             # Execute a simple calculation
             task = groovy.task("5 + 6")
             task.wait_for()

             # Get the result
             result = task.outputs["result"]
             print(f"Result: {result}")
             # Output: Result: 11

      Run it:

      .. code-block:: bash

         python hello_appose.py

   .. tab:: Java

      Create a file ``HelloAppose.java``:

      .. code-block:: java

         import org.apposed.appose.Appose;
         import org.apposed.appose.Environment;
         import org.apposed.appose.Service;
         import org.apposed.appose.Task;

         public class HelloAppose {
             public static void main(String[] args) throws Exception {
                 // Create an environment using the system Python
                 Environment env = Appose.system();

                 // Launch a Python worker service
                 try (Service python = env.python()) {
                     // Execute a simple calculation
                     Task task = python.task("5 + 6");
                     task.waitFor();

                     // Get the result
                     Object result = task.outputs.get("result");
                     System.out.println("Result: " + result);
                     // Output: Result: 11
                 }
             }
         }

      Run it:

      .. code-block:: bash

         javac -cp "appose-0.3.0.jar:dependency/*" HelloAppose.java
         java -cp ".:appose-0.3.0.jar:dependency/*" HelloAppose

Understanding the Code
-----------------------

Let's break down what's happening:

1. **Environment Creation**: ``Appose.system()`` (Java) or ``appose.system()`` (Python) creates an environment that uses the system's installed executables.

2. **Service Creation**: ``env.python()`` or ``env.groovy()`` launches a worker process in the target language.

3. **Task Execution**: ``service.task(script)`` sends a script to the worker for asynchronous execution.

4. **Waiting for Results**: ``task.waitFor()`` or ``task.wait_for()`` blocks until the task completes.

5. **Getting Results**: Task outputs are available in the ``outputs`` map/dictionary.

Next Steps
----------

Now that you have Appose running, you can:

* Learn about :doc:`core-concepts` like Environments, Services, and Tasks
* Explore more advanced :doc:`examples`
* Understand the :doc:`worker-protocol` for creating custom workers
* Check out the :doc:`faq` for common questions

Building Custom Environments
-----------------------------

Instead of using the system environment, you can build isolated environments with specific dependencies.

.. tabs::

   .. tab:: Python

      **Using Pixi** (recommended):

      .. code-block:: python

         env = appose.pixi() \
             .conda("python>=3.10", "numpy", "pandas") \
             .pypi("scikit-learn") \
             .channels("conda-forge") \
             .build("my-ml-env")

      **Using Conda/Mamba**:

      .. code-block:: python

         env = appose.mamba("environment.yml").build()

      **Using uv** (Python virtual environments):

      .. code-block:: python

         env = appose.uv() \
             .python("3.11") \
             .include("numpy", "pandas", "matplotlib") \
             .build("my-env")

   .. tab:: Java

      **Using Pixi** (recommended):

      .. code-block:: java

         Environment env = Appose.pixi()
             .conda("python>=3.10", "numpy", "pandas")
             .pypi("scikit-learn")
             .channels("conda-forge")
             .build("my-ml-env");

      **Using Conda/Mamba**:

      .. code-block:: java

         Environment env = Appose.mamba("environment.yml")
             .build();

      **Using uv** (Python virtual environments):

      .. code-block:: java

         Environment env = Appose.uv()
             .python("3.11")
             .include("numpy", "pandas", "matplotlib")
             .build("my-env");

Environments are cached by default in ``~/.local/share/appose/<env-name>``, so they only need to be built once.
