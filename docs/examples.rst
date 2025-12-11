Examples
========

This page provides comprehensive examples of using Appose in various scenarios.

Basic Examples
--------------

Simple Calculation
^^^^^^^^^^^^^^^^^^

The most basic example: execute a simple calculation.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class SimpleCalculation {
             public static void main(String[] args) throws Exception {
                 Environment env = Appose.system();
                 try (Service python = env.python()) {
                     Task task = python.task("5 + 6");
                     task.waitFor();
                     Object result = task.outputs.get("result");
                     System.out.println("Result: " + result); // 11
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         env = appose.system()
         with env.groovy() as groovy:
             task = groovy.task("5 + 6")
             task.wait_for()
             result = task.outputs["result"]
             print(f"Result: {result}")  # 11

With Inputs and Outputs
^^^^^^^^^^^^^^^^^^^^^^^^

Passing inputs to tasks and retrieving outputs.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class WithInputsOutputs {
             public static void main(String[] args) throws Exception {
                 Environment env = Appose.system();
                 try (Service python = env.python()) {
                     String script = """
                         # Calculate the sum
                         result = a + b
                         task.outputs["sum"] = result
                         task.outputs["product"] = a * b
                         """;

                     Task task = python.task(script);
                     task.inputs.put("a", 10);
                     task.inputs.put("b", 5);
                     task.waitFor();

                     System.out.println("Sum: " + task.outputs.get("sum"));      // 15
                     System.out.println("Product: " + task.outputs.get("product")); // 50
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         script = """
         // Calculate the sum
         result = a + b
         task.outputs["sum"] = result
         task.outputs["product"] = a * b
         """

         env = appose.system()
         with env.groovy() as groovy:
             task = groovy.task(script)
             task.inputs["a"] = 10
             task.inputs["b"] = 5
             task.wait_for()

             print(f"Sum: {task.outputs['sum']}")       # 15
             print(f"Product: {task.outputs['product']}") # 50

Progress Tracking
-----------------

Golden Ratio Approximation
^^^^^^^^^^^^^^^^^^^^^^^^^^

A more complex example showing progress tracking and cancelation.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class GoldenRatio {
             public static void main(String[] args) throws Exception {
                 String script = """
                 # Approximate the golden ratio using the Fibonacci sequence.
                 previous = 0
                 current = 1
                 iterations = 50
                 for i in range(iterations):
                     if task.cancel_requested:
                         task.cancel()
                         break
                     task.update(current=i, maximum=iterations)
                     v = current
                     current += previous
                     previous = v
                 task.outputs["numer"] = current
                 task.outputs["denom"] = previous
                 """;

                 Environment env = Appose.system();
                 try (Service python = env.python()) {
                     Task task = python.task(script);

                     task.listen(event -> {
                         switch (event.responseType) {
                             case UPDATE:
                                 System.out.println("Progress: " + task.current + "/" + task.maximum);
                                 break;
                             case COMPLETION:
                                 long numer = ((Number) task.outputs.get("numer")).longValue();
                                 long denom = ((Number) task.outputs.get("denom")).longValue();
                                 double ratio = (double) numer / denom;
                                 System.out.println("Result: " + numer + "/" + denom + " ≈ " + ratio);
                                 break;
                             case CANCELATION:
                                 System.out.println("Task canceled");
                                 break;
                             case FAILURE:
                                 System.err.println("Task failed: " + task.error);
                                 break;
                         }
                     });

                     task.start();
                     Thread.sleep(1000);

                     if (!task.status.isFinished()) {
                         // Task is taking too long; request cancelation
                         task.cancel();
                     }

                     task.waitFor();
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose
         from appose import ResponseType
         from time import sleep

         script = """
         // Approximate the golden ratio using the Fibonacci sequence.
         previous = 0
         current = 1
         iterations = 50
         for (i=0; i<iterations; i++) {
             if (task.cancelRequested) {
                 task.cancel()
                 break
             }
             task.update(null, i, iterations)
             v = current
             current += previous
             previous = v
         }
         task.outputs["numer"] = current
         task.outputs["denom"] = previous
         """

         def task_listener(event):
             if event.response_type == ResponseType.UPDATE:
                 print(f"Progress: {task.current}/{task.maximum}")
             elif event.response_type == ResponseType.COMPLETION:
                 numer = task.outputs["numer"]
                 denom = task.outputs["denom"]
                 ratio = numer / denom
                 print(f"Result: {numer}/{denom} ≈ {ratio}")
             elif event.response_type == ResponseType.CANCELATION:
                 print("Task canceled")
             elif event.response_type == ResponseType.FAILURE:
                 print(f"Task failed: {task.error}", file=sys.stderr)

         env = appose.system()
         with env.groovy() as groovy:
             task = groovy.task(script)
             task.listen(task_listener)
             task.start()

             sleep(1)
             if not task.status.is_finished():
                 # Task is taking too long; request cancelation
                 task.cancel()

             task.wait_for()

Environment Building
--------------------

Conda Environment
^^^^^^^^^^^^^^^^^

Building an environment with conda dependencies.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class CondaEnvironment {
             public static void main(String[] args) throws Exception {
                 Environment env = Appose.mamba()
                     .conda("python=3.11", "numpy", "pandas")
                     .channels("conda-forge")
                     .logDebug()
                     .build("my-data-env");

                 try (Service python = env.python()) {
                     String script = """
                     import numpy as np
                     import pandas as pd

                     # Create a simple array
                     arr = np.array([1, 2, 3, 4, 5])
                     task.outputs["mean"] = float(np.mean(arr))
                     task.outputs["std"] = float(np.std(arr))
                     """;

                     Task task = python.task(script);
                     task.waitFor();

                     System.out.println("Mean: " + task.outputs.get("mean"));
                     System.out.println("Std: " + task.outputs.get("std"));
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         env = appose.mamba() \
             .conda("python=3.11", "numpy", "pandas") \
             .channels("conda-forge") \
             .log_debug() \
             .build("my-data-env")

         with env.python() as python:
             script = """
             import numpy as np
             import pandas as pd

             # Create a simple array
             arr = np.array([1, 2, 3, 4, 5])
             task.outputs["mean"] = float(np.mean(arr))
             task.outputs["std"] = float(np.std(arr))
             """

             task = python.task(script)
             task.wait_for()

             print(f"Mean: {task.outputs['mean']}")
             print(f"Std: {task.outputs['std']}")

Pixi Environment
^^^^^^^^^^^^^^^^

Using Pixi for a modern, faster alternative to conda.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class PixiEnvironment {
             public static void main(String[] args) throws Exception {
                 Environment env = Appose.pixi()
                     .conda("python>=3.10", "numpy")
                     .pypi("scikit-learn")
                     .channels("conda-forge")
                     .build("my-ml-env");

                 try (Service python = env.python()) {
                     String script = """
                     import numpy as np
                     from sklearn.linear_model import LinearRegression

                     # Simple linear regression
                     X = np.array([[1], [2], [3], [4], [5]])
                     y = np.array([2, 4, 6, 8, 10])

                     model = LinearRegression()
                     model.fit(X, y)

                     task.outputs["slope"] = float(model.coef_[0])
                     task.outputs["intercept"] = float(model.intercept_)
                     """;

                     Task task = python.task(script);
                     task.waitFor();

                     System.out.println("Slope: " + task.outputs.get("slope"));
                     System.out.println("Intercept: " + task.outputs.get("intercept"));
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         env = appose.pixi() \
             .conda("python>=3.10", "numpy") \
             .pypi("scikit-learn") \
             .channels("conda-forge") \
             .build("my-ml-env")

         with env.python() as python:
             script = """
             import numpy as np
             from sklearn.linear_model import LinearRegression

             # Simple linear regression
             X = np.array([[1], [2], [3], [4], [5]])
             y = np.array([2, 4, 6, 8, 10])

             model = LinearRegression()
             model.fit(X, y)

             task.outputs["slope"] = float(model.coef_[0])
             task.outputs["intercept"] = float(model.intercept_)
             """

             task = python.task(script)
             task.wait_for()

             print(f"Slope: {task.outputs['slope']}")
             print(f"Intercept: {task.outputs['intercept']}")

uv Environment
^^^^^^^^^^^^^^

Using uv for fast Python virtual environments.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class UvEnvironment {
             public static void main(String[] args) throws Exception {
                 Environment env = Appose.uv()
                     .python("3.11")
                     .include("requests", "beautifulsoup4")
                     .build("my-web-env");

                 try (Service python = env.python()) {
                     String script = """
                     import requests
                     from bs4 import BeautifulSoup

                     # Simple web scraping example
                     # (In real use, make actual HTTP request)
                     html = "<html><body><h1>Hello World</h1></body></html>"
                     soup = BeautifulSoup(html, 'html.parser')

                     task.outputs["title"] = soup.h1.text
                     """;

                     Task task = python.task(script);
                     task.waitFor();

                     System.out.println("Title: " + task.outputs.get("title"));
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         env = appose.uv() \
             .python("3.11") \
             .include("requests", "beautifulsoup4") \
             .build("my-web-env")

         with env.python() as python:
             script = """
             import requests
             from bs4 import BeautifulSoup

             # Simple web scraping example
             html = "<html><body><h1>Hello World</h1></body></html>"
             soup = BeautifulSoup(html, 'html.parser')

             task.outputs["title"] = soup.h1.text
             """

             task = python.task(script)
             task.wait_for()

             print(f"Title: {task.outputs['title']}")

From Environment Files
^^^^^^^^^^^^^^^^^^^^^^^

Loading environments from configuration files.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class FromFile {
             public static void main(String[] args) throws Exception {
                 // Auto-detect builder from file extension
                 Environment env = Appose.file("environment.yml")
                     .logDebug()
                     .build();

                 try (Service python = env.python()) {
                     Task task = python.task("import sys; task.outputs['version'] = sys.version");
                     task.waitFor();
                     System.out.println("Python version: " + task.outputs.get("version"));
                 }

                 // Or explicitly specify Mamba
                 env = Appose.mamba("environment.yml").build();

                 // Or use Pixi with pixi.toml
                 env = Appose.pixi("pixi.toml").build();
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         # Auto-detect builder from file extension
         env = appose.file("environment.yml") \
             .log_debug() \
             .build()

         with env.python() as python:
             task = python.task("import sys; task.outputs['version'] = sys.version")
             task.wait_for()
             print(f"Python version: {task.outputs['version']}")

         # Or explicitly specify Mamba
         env = appose.mamba("environment.yml").build()

         # Or use Pixi with pixi.toml
         env = appose.pixi("pixi.toml").build()

Wrapping Existing Environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Wrap and use existing conda/pixi environments.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;
         import java.io.File;

         public class WrapEnvironment {
             public static void main(String[] args) throws Exception {
                 // Wrap an existing environment (auto-detects type)
                 Environment env = Appose.wrap(new File("/path/to/existing/env"));

                 try (Service python = env.python()) {
                     Task task = python.task("print('Hello from wrapped environment!')");
                     task.waitFor();
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         # Wrap an existing environment (auto-detects type)
         env = appose.wrap("/path/to/existing/env")

         with env.python() as python:
             task = python.task("print('Hello from wrapped environment!')")
             task.wait_for()

Advanced Examples
-----------------

Multiple Tasks in Sequence
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Running multiple tasks one after another.

.. todo:: Running tasks in sequence is not very "Advanced". More appropriate would be things like: 1) open-ended tasks that send updates for communication back to the service process; or 2) use of the queue=main feature to run sensitive tasks on the main thread to avoid threading issues.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class SequentialTasks {
             public static void main(String[] args) throws Exception {
                 Environment env = Appose.system();
                 try (Service python = env.python()) {
                     // Task 1: Initialize data
                     Task task1 = python.task("""
                         data = [1, 2, 3, 4, 5]
                         task.outputs["data"] = data
                         """);
                     task1.waitFor();

                     // Task 2: Process data
                     Task task2 = python.task("""
                         result = sum(data) / len(data)
                         task.outputs["average"] = result
                         """);
                     task2.inputs.put("data", task1.outputs.get("data"));
                     task2.waitFor();

                     System.out.println("Average: " + task2.outputs.get("average"));
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         env = appose.system()
         with env.python() as python:
             # Task 1: Initialize data
             task1 = python.task(
                 "data = [1, 2, 3, 4, 5]\n"
                 "task.outputs['data'] = data"
             )
             task1.wait_for()

             # Task 2: Process data
             task2 = python.task(
                 "result = sum(data) / len(data)\n"
                 "task.outputs['average'] = result"
             )
             task2.inputs["data"] = task1.outputs["data"]
             task2.wait_for()

             print(f"Average: {task2.outputs['average']}")

Error Handling
^^^^^^^^^^^^^^

Properly handling task failures.

.. todo:: The following example will throw an exception at the task.waitFor() step. This example needs to be changed to either: A) try/catch at that step and handle that way; or B) do not call waitFor and instead handle errors asynchronously by checking task.status at intervals; or C) maybe one example of each?

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class ErrorHandling {
             public static void main(String[] args) throws Exception {
                 Environment env = Appose.system();
                 try (Service python = env.python()) {
                     Task task = python.task("""
                         # This will raise an exception
                         result = 1 / 0
                         """);

                     task.listen(event -> {
                         switch (event.responseType) {
                             case FAILURE:
                                 System.err.println("Task failed with error:");
                                 System.err.println(task.error);
                                 break;
                             case COMPLETION:
                                 System.out.println("Task completed successfully");
                                 break;
                         }
                     });

                     task.waitFor();

                     if (task.status == TaskStatus.FAILED) {
                         System.err.println("Handling the failure...");
                         // Recover or retry
                     }
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose
         from appose import ResponseType, TaskStatus

         env = appose.system()
         with env.python() as python:
             task = python.task("result = 1 / 0")

             def task_listener(event):
                 if event.response_type == ResponseType.FAILURE:
                     print(f"Task failed with error:", file=sys.stderr)
                     print(task.error, file=sys.stderr)
                 elif event.response_type == ResponseType.COMPLETION:
                     print("Task completed successfully")

             task.listen(task_listener)
             task.wait_for()

             if task.status == TaskStatus.FAILED:
                 print("Handling the failure...", file=sys.stderr)
                 # Recover or retry

Real-World Use Cases
--------------------

Deep Learning Inference
^^^^^^^^^^^^^^^^^^^^^^^^

.. todo:: This example needs to be finished. We can use https://github.com/ctrueden/starfun3d

Running deep learning models from a different language.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class DeepLearning {
             public static void main(String[] args) throws Exception {
                 // Build environment with PyTorch
                 Environment env = Appose.pixi()
                     .conda("python>=3.10")
                     .pypi("torch", "torchvision")
                     .build("pytorch-env");

                 try (Service python = env.python()) {
                     // Load a pre-trained model
                     Task loadModel = python.task("""
                         import torch
                         import torchvision.models as models

                         # Load pre-trained ResNet
                         model = models.resnet18(pretrained=False)
                         model.eval()

                         task.outputs["status"] = "Model loaded"
                         """);
                     loadModel.waitFor();

                     System.out.println(loadModel.outputs.get("status"));

                     // In a real scenario, you would:
                     // 1. Share image tensors via shared memory
                     // 2. Run inference
                     // 3. Get results back via shared memory
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         # Build environment with your ML framework
         env = appose.pixi() \
             .conda("python>=3.10") \
             .pypi("torch", "torchvision") \
             .build("pytorch-env")

         with env.python() as python:
             # Load a pre-trained model
             script = (
                 "import torch\n"
                 "import torchvision.models as models\n"
                 "\n"
                 "model = models.resnet18(pretrained=False)\n"
                 "model.eval()\n"
                 "task.outputs['status'] = 'Model loaded'"
             )
             load_model = python.task(script)
             load_model.wait_for()

             print(load_model.outputs["status"])

             # In a real scenario, you would:
             # 1. Share tensors via shared memory
             # 2. Run inference
             # 3. Get results back

Data Science Pipeline
^^^^^^^^^^^^^^^^^^^^^

.. todo:: This example needs testing and refinement.

Complex data processing workflow.

.. tabs::

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;

         public class DataPipeline {
             public static void main(String[] args) throws Exception {
                 Environment env = Appose.pixi()
                     .conda("python>=3.10", "pandas", "numpy")
                     .pypi("scikit-learn")
                     .build("data-pipeline");

                 try (Service python = env.python()) {
                     // Step 1: Load and preprocess data
                     Task preprocess = python.task("""
                         import pandas as pd
                         import numpy as np

                         # Simulate loading data
                         data = pd.DataFrame({
                             'x': np.random.randn(100),
                             'y': np.random.randn(100)
                         })

                         # Preprocess
                         data_normalized = (data - data.mean()) / data.std()

                         task.outputs["rows"] = len(data_normalized)
                         task.outputs["status"] = "Preprocessed"
                         """);
                     preprocess.waitFor();

                     System.out.println("Preprocessed " + preprocess.outputs.get("rows") + " rows");

                     // Step 2: Train model
                     Task train = python.task("""
                         from sklearn.linear_model import LinearRegression

                         # Training logic here
                         task.outputs["status"] = "Model trained"
                         """);
                     train.waitFor();

                     System.out.println(train.outputs.get("status"));
                 }
             }
         }

   .. tab:: Python

      .. code-block:: python

         import appose

         env = appose.pixi() \
             .conda("python>=3.10", "pandas", "numpy") \
             .pypi("scikit-learn") \
             .build("data-pipeline")

         with env.python() as python:
             # Step 1: Load and preprocess data
             preprocess_script = (
                 "import pandas as pd\n"
                 "import numpy as np\n"
                 "\n"
                 "data = pd.DataFrame({\n"
                 "    'x': np.random.randn(100),\n"
                 "    'y': np.random.randn(100)\n"
                 "})\n"
                 "data_normalized = (data - data.mean()) / data.std()\n"
                 "task.outputs['rows'] = len(data_normalized)\n"
                 "task.outputs['status'] = 'Preprocessed'"
             )
             preprocess = python.task(preprocess_script)
             preprocess.wait_for()

             print(f"Preprocessed {preprocess.outputs['rows']} rows")

             # Step 2: Train model
             train_script = (
                 "from sklearn.linear_model import LinearRegression\n"
                 "task.outputs['status'] = 'Model trained'"
             )
             train = python.task(train_script)
             train.wait_for()

             print(train.outputs["status"])
