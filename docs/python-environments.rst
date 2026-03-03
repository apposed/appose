Python Environment Best Practices
==================================

Appose manages Python environments for you — installing the right packages
once, caching them, and reusing them on every subsequent run. But getting the
environment configuration definition completely right for real-world deep
learning workloads can be quite tricky, because you often need more than a flat
list of packages: GPU acceleration, platform-specific libraries, optional
developer tools, and reproducible cross-platform builds all require careful
configuration.

This guide walks through best practices for environment configuration, with a
focus on the patterns most commonly needed for GPU-accelerated Python workers.

.. contents:: On this page
   :local:
   :depth: 2

Choosing an Environment Manager
---------------------------------

Appose supports several environment managers. The right choice depends on your
use case:

.. list-table::
   :header-rows: 1
   :widths: 15 45 40

   * - Manager
     - Best for
     - Key limitation
   * - **Pixi**
     - Multi-platform reproducibility, GPU/CUDA, mixed conda+PyPI deps
     - Slower environment resolution than uv due to the conda solver
   * - **uv**
     - Pure-Python environments, fast installs
     - No conda package support
   * - **Mamba**
     - Existing ``environment.yml`` files, conda-only packages
     - Slower solves, no built-in feature system

For GPU-accelerated deep learning across macOS, Linux, and Windows, **Pixi is
the recommended choice**. It natively handles platform-conditional packages,
multiple named environments, and the NVIDIA channel — all in a single
``pixi.toml`` file.

Pixi: Single-Platform Quickstart
----------------------------------

The simplest Pixi setup specifies conda and PyPI dependencies together:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import appose

         env = appose.pixi() \
             .channels("conda-forge") \
             .conda("python=3.11", "numpy", "scipy") \
             .pypi("torch", "torchvision") \
             .build("my-dl-env")

         with env.python() as svc:
             task = svc.task("import torch; result = str(torch.__version__)")
             task.wait_for()
             print(task.outputs["result"])

   .. tab:: Java

      .. code-block:: java

         Environment env = Appose.pixi()
             .channels("conda-forge")
             .conda("python=3.11", "numpy", "scipy")
             .pypi("torch", "torchvision")
             .build("my-dl-env");

         try (Service python = env.python()) {
             Task task = python.task(
                 "import torch; result = str(torch.__version__)");
             task.waitFor();
             System.out.println(task.outputs.get("result"));
         }

This generates a ``pixi.toml``, runs ``pixi install``, and caches the
environment at ``~/.local/share/appose/my-dl-env``.

Pixi: Multi-Platform Configuration
-------------------------------------

Real projects often need different packages on different operating systems —
one good example is TensorFlow, which ships as separate packages for
Intel macOS, Apple Silicon, and CUDA-enabled Linux/Windows.

Rather than writing platform detection logic in application code, encode it
directly in a ``pixi.toml``:

.. code-block:: toml

   [workspace]
   name = "my-appose-worker"
   channels = ["conda-forge"]
   platforms = ["osx-arm64", "osx-64", "linux-64", "win-64"]

   [dependencies]
   python = "==3.11"
   numpy = "*"
   scipy = "*"
   pip = "*"

   # ---- Per-platform TensorFlow variants ----

   [target.win-64.pypi-dependencies]
   tensorflow = "==2.15.0"

   [target.linux-64.pypi-dependencies]
   tensorflow = "==2.15.0"

   [target.osx-64.pypi-dependencies]
   tensorflow = "*"            # latest CPU TF for Intel Mac

   [target.osx-arm64.pypi-dependencies]
   tensorflow-macos = "*"      # Apple Silicon TF
   tensorflow-metal = "*"      # Metal GPU plugin

   # ---- Environments ----

   [environments]
   default = { solve-group = "default" }

When Pixi installs this environment on any of the four platforms it will
automatically select the correct TensorFlow variant. No ``if sys.platform``
guards needed in your Python worker.

.. tip::

   Lock your TensorFlow version on Linux/Windows (``"==2.15.0"``) to ensure
   compatibility with a specific CUDA toolkit version. On macOS you can
   generally leave it unpinned since GPU support is handled by the Metal
   plugin rather than by CUDA.

Pixi: CUDA Feature Pattern
---------------------------

CUDA support requires extra conda packages (``cudatoolkit``, ``cudnn``) and
environment variable tweaks that differ by OS. Pixi's *feature* system is the
cleanest way to make this opt-in without creating a separate environment file:

.. code-block:: toml

   [workspace]
   name = "my-appose-worker"
   channels = ["conda-forge"]
   platforms = ["linux-64", "win-64"]

   [dependencies]
   python = "==3.11"
   numpy = "*"
   pip = "*"

   [pypi-dependencies]
   torch = "*"

   # ---- CUDA feature (Windows/Linux only) ----

   [feature.cuda]
   channels = ["nvidia", "conda-forge"]

   [feature.cuda.target.linux-64.dependencies]
   cudatoolkit = "11.8.*"
   cudnn = "8.6.*"

   [feature.cuda.target.win-64.dependencies]
   cudatoolkit = "11.8.*"
   cudnn = "8.6.*"

   # Activation: make CUDA libraries visible at runtime
   [feature.cuda.target.linux-64.activation.env]
   LD_LIBRARY_PATH = "$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

   [feature.cuda.target.win-64.activation.env]
   PATH = "%CONDA_PREFIX%\\Library\\bin;%PATH%"

   # ---- Environments ----

   [environments]
   default = { solve-group = "default" }          # CPU-only
   cuda    = { features = ["cuda"], solve-group = "default" }  # GPU

Key points:

* The ``[feature.cuda]`` block adds the ``nvidia`` channel alongside
  ``conda-forge``. This is where ``cudatoolkit`` and ``cudnn`` are sourced.
* ``[feature.cuda.target.<os>.activation.env]`` sets environment variables
  whenever the ``cuda`` environment is activated, so PyTorch and TensorFlow
  can find the CUDA libraries without any manual ``export`` commands.
* ``solve-group = "default"`` tells Pixi to solve the ``cuda`` and ``default``
  environments together, maximising package reuse between them.

.. note::

   The ``nvidia`` channel hosts CUDA toolkit packages. Always list it
   *before* ``conda-forge`` in the feature's ``channels`` list so that
   CUDA-specific packages take precedence.

Pixi: Apple Silicon and the ``nometal`` Pattern
-------------------------------------------------

On Apple Silicon, ``tensorflow-metal`` accelerates TF with the GPU. Some
workflows (e.g., reproducibility testing) need a CPU-only variant. The
``nometal`` feature handles this:

.. code-block:: toml

   # Default Apple Silicon setup — GPU-accelerated
   [target.osx-arm64.pypi-dependencies]
   tensorflow-macos = "*"
   tensorflow-metal = "*"

   # Optional: CPU-only override for Apple Silicon
   [feature.nometal]
   channels = ["conda-forge"]

   [feature.nometal.target.osx-arm64.pypi-dependencies]
   tensorflow = "*"           # plain CPU TF overrides tensorflow-macos

   [environments]
   default = { solve-group = "default" }
   nometal = { features = ["nometal"], solve-group = "default" }

Users who need CPU-only inference can activate ``pixi run -e nometal python
worker.py`` without maintaining a second environment file.

Combining Features: Dev + CUDA
-------------------------------

Features compose cleanly. A typical project ships four environments:

.. code-block:: toml

   [feature.dev.dependencies]
   pytest = "*"
   ruff   = "*"

   [feature.dev.pypi-dependencies]
   build = "*"

   [environments]
   default  = { solve-group = "default" }
   cuda     = { features = ["cuda"],        solve-group = "default" }
   dev      = { features = ["dev"],         solve-group = "default" }
   cuda-dev = { features = ["cuda", "dev"], solve-group = "default" }

CI runs the ``dev`` environment. Production servers with GPUs use ``cuda``.
Developers with NVIDIA cards use ``cuda-dev``. All share the same solve group
so dependency versions stay consistent.

Using a ``pixi.toml`` with Appose
----------------------------------

For environments this complex, maintain the full ``pixi.toml`` alongside your
project source and point Appose at the pre-configured environment by name.
Commit the ``pixi.lock`` file to your repository to guarantee reproducible
installs across machines and CI runs.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import appose

         # Point Appose at a non-default pixi.toml environment.
         # Appose will run `pixi install -e cuda` if needed,
         # then launch a worker in that environment.
         env = appose.pixi("path/to/pixi.toml") \
             .environment("cuda") \
             .build()

         with env.python() as svc:
             task = svc.task(
                 "import torch; result = torch.cuda.is_available()")
             task.wait_for()
             print("CUDA available:", task.outputs["result"])

   .. tab:: Java

      .. code-block:: java

         // Point Appose at a non-default pixi.toml environment.
         // Appose will run `pixi install -e cuda` if needed,
         // then launch a worker in that environment.
         Environment env = Appose.pixi("path/to/pixi.toml")
             .environment("cuda")
             .build();

         try (Service python = env.python()) {
             Task task = python.task(
                 "import torch; result = torch.cuda.is_available()");
             task.waitFor();
             System.out.println("CUDA available: " + task.outputs.get("result"));
         }

.. tip::

   Store your ``pixi.toml`` and ``pixi.lock`` in version control. The lock
   file pins every transitive dependency, making builds reproducible across
   developer machines and CI without a network solve.

Detecting GPU Availability at Runtime
---------------------------------------

When shipping an application you may not know in advance whether a GPU is
present. A safe pattern is to build the GPU environment eagerly but fall back
gracefully to CPU at runtime:

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import appose

         # Try to build the CUDA environment first.
         # If CUDA packages are unavailable on this platform,
         # pixi will raise an error — catch it and use CPU.
         try:
             env = appose.pixi("pixi.toml").environment("cuda").build()
         except Exception:
             env = appose.pixi("pixi.toml").build()  # default env

         worker_script = (
             "import torch\n"
             "device = 'cuda' if torch.cuda.is_available() else 'cpu'\n"
             "result = device\n"
         )

         with env.python() as svc:
             task = svc.task(worker_script)
             task.wait_for()
             print("Running on:", task.outputs["result"])

   .. tab:: Java

      .. code-block:: java

         Environment env;
         try {
             env = Appose.pixi("pixi.toml").environment("cuda").build();
         } catch (Exception e) {
             env = Appose.pixi("pixi.toml").build();  // default env
         }

         String script =
             "import torch\n" +
             "device = 'cuda' if torch.cuda.is_available() else 'cpu'\n" +
             "result = device\n";

         try (Service python = env.python()) {
             Task task = python.task(script);
             task.waitFor();
             System.out.println("Running on: " + task.outputs.get("result"));
         }

Complete Example: TensorFlow Worker
--------------------------------------

Putting it all together — a ``pixi.toml`` that supports four platforms with
automatic GPU acceleration, and the Appose code that uses it:

**pixi.toml**

.. code-block:: toml

   [workspace]
   name = "tf-appose-worker"
   channels = ["conda-forge"]
   platforms = ["osx-arm64", "osx-64", "linux-64", "win-64"]

   [dependencies]
   python = "==3.11"
   numpy  = "<2"
   scipy  = "*"
   pip    = "*"

   # Platform-specific TensorFlow
   [target.win-64.pypi-dependencies]
   tensorflow = "==2.15.0"

   [target.linux-64.pypi-dependencies]
   tensorflow = "==2.15.0"

   [target.osx-64.pypi-dependencies]
   tensorflow = "*"

   [target.osx-arm64.pypi-dependencies]
   tensorflow-macos = "*"
   tensorflow-metal = "*"

   # CUDA feature (Linux and Windows)
   [feature.cuda]
   channels = ["nvidia", "conda-forge"]

   [feature.cuda.target.linux-64.dependencies]
   cudatoolkit = "11.8.*"
   cudnn       = "8.6.*"

   [feature.cuda.target.win-64.dependencies]
   cudatoolkit = "11.8.*"
   cudnn       = "8.6.*"

   [feature.cuda.target.linux-64.activation.env]
   LD_LIBRARY_PATH = "$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"

   [feature.cuda.target.win-64.activation.env]
   PATH = "%CONDA_PREFIX%\\Library\\bin;%PATH%"

   [environments]
   default = { solve-group = "default" }
   cuda    = { features = ["cuda"], solve-group = "default" }

**Application code**

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import appose
         import platform

         # Pick the environment by platform capability
         is_gpu_platform = platform.system() in ("Linux", "Windows")
         env_name = "cuda" if is_gpu_platform else "default"

         env = appose.pixi("pixi.toml").environment(env_name).build()

         worker_script = (
             "import tensorflow as tf\n"
             "gpus = tf.config.list_physical_devices('GPU')\n"
             "result = f'{len(gpus)} GPU(s) available'\n"
         )

         with env.python() as svc:
             task = svc.task(worker_script)
             task.wait_for()
             print(task.outputs["result"])

   .. tab:: Java

      .. code-block:: java

         import org.apposed.appose.*;
         import java.io.File;

         public class TFWorkerDemo {
             public static void main(String[] args) throws Exception {
                 String os = System.getProperty("os.name").toLowerCase();
                 boolean isGpuPlatform = os.contains("linux") || os.contains("win");
                 String envName = isGpuPlatform ? "cuda" : "default";

                 Environment env = Appose
                     .pixi("pixi.toml")
                     .environment(envName)
                     .build();

                 String script =
                     "import tensorflow as tf\n" +
                     "gpus = tf.config.list_physical_devices('GPU')\n" +
                     "result = f'{len(gpus)} GPU(s) available'\n";

                 try (Service python = env.python()) {
                     Task task = python.task(script);
                     task.waitFor();
                     System.out.println(task.outputs.get("result"));
                 }
             }
         }

Summary of Best Practices
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Practice
     - Why
   * - Use Pixi for multi-platform projects
     - Single file handles OS-specific packages and GPU features
   * - Pin CUDA toolkit versions
     - Prevents incompatible driver/library mismatches
   * - Use ``[target.<os>.*]`` for platform-specific deps
     - Avoids ``if platform`` guards in application code
   * - Define CUDA as an optional *feature*, not a hard dependency
     - Lets CPU-only machines install and run without modification
   * - Commit ``pixi.lock`` to version control
     - Guarantees identical environments across machines and CI
   * - Use ``solve-group`` to share packages between environments
     - Reduces disk usage and install time
   * - Set activation env vars in ``pixi.toml``
     - CUDA libraries are found automatically; no manual ``export`` needed
   * - Use separate ``cuda`` and ``default`` environments
     - Makes the GPU upgrade path explicit and reversible
