Sharing Arrays Between Processes
================================

Appose shares arrays between processes through **shared memory**: the array
data lives in a named memory block that every process involved can map
directly, so only a small reference to it ever travels in a message. No pixel
is serialized, and no matter how large the array, sending it is cheap.

But shared memory raises a question that ordinary function calls never do:
once an array has been shared, **who owns its memory, and when may it be
freed?** Appose's answer: the service owns it, counts which processes use
each array, and frees an array once none of them does anymore. This page
explains how that works, the ways to use it, and when to manage memory
yourself instead.

At a Glance
-----------

.. list-table::
   :header-rows: 1
   :widths: 16 28 28 28

   * -
     - Managed, handed off
     - Managed, shared
     - Unmanaged
   * - In a sentence
     - "Here, this is yours now."
     - "Look at this with me."
     - "Here's a buffer; I'll say when it's gone."
   * - Who uses the data afterwards
     - The receiver alone
     - Everyone holding it
     - Whoever the application decides
   * - Who sees writes
     - Only the receiver
     - Everyone holding it
     - Everyone holding it
   * - When it is freed
     - Once the receiver is done
     - Once every holder is done
     - When its creator frees it
   * - Typical uses
     - Results, inputs, chunks read on demand
     - Cached image cells, shared output images
     - A reused buffer, a worker's ring buffer

Rule of thumb: **let Appose manage your arrays.** Whether an array is handed
off or shared is simply a matter of whether the sender keeps using it after
sending it. Manage memory yourself only when you need control over exactly
when it goes away.

How Managed Memory Works
------------------------

All managed memory belongs to the **service**: it alone creates and frees it.
For each managed array, the service counts the processes holding it: itself,
while any object in the service refers to the array; and each worker it has
sent the array to. Once that count drops to zero, the array is freed.

* **Workers never allocate managed memory themselves.** When a worker needs
  some (e.g. to return a NumPy array), Appose asks the service for it, behind
  the scenes.
* **Workers tell the service when they are done** with an array they
  received, once it is garbage collected (or explicitly disposed of).
* **Sending a managed array on never copies it.** Passing an array from one
  worker on to another, through the service, just adds a holder.

In Python, create a managed array with ``NDArray(dtype, shape, managed=True)``;
in Java, with ``NDArray.managed(dType, shape)``; with `imglib2-appose
<https://github.com/imglib/imglib2-appose>`_, with ``ShmImg.managed(type,
dims)``. Plain NumPy arrays (and, with imglib2-appose, ``ArrayImg``\ s) are
managed automatically: copied into managed memory once, when first sent.
A managed array arrives in Python as a NumPy array, and in Java as an
``NDArray`` (which imglib2-appose can wrap as a ``ShmImg``).

Handing an Array Off
--------------------

Send a managed array and stop using it, and the receiver has it to itself:
nobody else holds it, so the receiver may modify it at will.

**When to use it:** whenever an array is a one-way handoff.

* A worker computes a result (a segmentation mask, a feature table) and
  returns it.
* The service passes an image to a worker, which may modify its copy freely.
* A reader in the service decodes chunks of a large image on demand, each of
  which the worker consumes once.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         import appose
         import numpy as np

         image = np.random.rand(512, 512).astype(np.float32)
         with appose.system().python().init("import numpy") as worker:
             # The worker gets its own copy of the image: modify at will.
             task = worker.task("image *= 2\nimage > 1", {"image": image})
             mask = task.wait_for().result()  # A NumPy array of our own.

   .. tab:: Java

      .. code-block:: java

         // A reader in the service, called by the worker for each chunk.
         public class ChunkReader {
             public NDArray read(int index) {
                 NDArray chunk = NDArray.managed(DType.UINT16,
                     new Shape(C_ORDER, 64, 64));
                 decompressInto(chunk.buffer(), index); // No extra copy.
                 return chunk; // Freed once the worker is done with it.
             }
         }

         Task task = worker.task(
             "[int(reader.read(i).sum()) for i in range(3)]",
             Collections.singletonMap("reader", new ChunkReader()));

Sharing an Array
----------------

Keep using a managed array after sending it, and every holder views the same
memory, in place: each sees every write to it.

**When to use it:** whenever the data belongs to a long-lived source, which
several parties look at, or which the sender keeps using.

* **A cache of image cells.** The service holds a large image, lazily loaded
  from disk cell by cell. Several workers process tiles of it. When a worker
  needs a cell, the service loads it into managed memory *once*, and sends
  it; when another worker needs the same cell, it gets the same memory, with
  no reload and no copy. The cache may even evict the cell while workers
  still use it: the memory is freed only once no worker uses it anymore.
* **A shared output image.** The service creates an empty label image and
  sends it to a segmentation worker, which writes its labels straight into
  it. The service (say, an image viewer) sees the labels appear as they are
  written. Once the worker is done with it, the service can save the image.
* **Passing an array on.** The service passes a worker's result on to another
  worker, which views the very same memory.

.. tabs::

   .. tab:: Python

      .. code-block:: python

         class CellCache:
             """Loads each cell once; any number of workers can view it."""

             def __init__(self):
                 self.cells = {}

             def cell(self, index):
                 if index not in self.cells:
                     cell = appose.NDArray("float32", [64, 64], managed=True)
                     load_cell_into(np.asarray(cell), index)
                     self.cells[index] = cell
                 return self.cells[index]

             def evict(self, index):
                 # Freed once no worker uses the cell anymore.
                 self.cells.pop(index).shm.dispose()

         cache = CellCache()
         for worker in (worker1, worker2):
             # Both workers view the same memory.
             worker.task("process(cache.cell(5))", {"cache": cache})

   .. tab:: Java

      .. code-block:: java

         // Send an empty label image to a worker, which segments into it.
         try (NDArray labels = NDArray.managed(DType.UINT16, new Shape(C_ORDER, 512, 512))) {
             Map<String, Object> inputs = new HashMap<>();
             inputs.put("image", image);
             inputs.put("labels", labels);
             worker.task("segment(image, out=labels)", inputs).waitFor();
             // The labels are already here, in place: nothing to copy back.
             save(labels);
         }

.. note::

   Appose does not coordinate concurrent writes to a shared array. If several
   processes write to the same array, coordinate them yourself; e.g., give
   each worker its own tiles to write.

Unmanaged Arrays
----------------

An ``NDArray`` created as usual (``NDArray(dtype, shape)`` in Python,
``new NDArray(dType, shape)`` in Java) is unmanaged: shared in place, like a
managed array, but its creator alone decides when it goes away, whether or
not other processes still use it. Appose does no counting for it. Any
process may create unmanaged memory, a worker included.

**When to use it:** when you know exactly how long the data must live, and
want to control that yourself.

* **A buffer reused across many calls** into a worker.
* **A worker's ring buffer.** A camera or video worker writes frames into a
  ring of slots in one block it created, and sends the service a view of
  each frame's slot. Reuse of the slots is a matter of timing (frame *n* is
  valid until frame *n* + 64 overwrites it), which no counting could prevent.
* **Memory Appose did not create**, such as a segment owned by an acquisition
  driver or another library, which only its owner may free.
* **A large read-only resource** a worker loads once at startup, such as a
  reference atlas, which the service views at will until the worker exits.

.. code-block:: python

   with appose.NDArray("int32", [1024, 1024]) as buffer:
       for tile in range(100):
           worker.task("read_tile(i, numpy.asarray(buf))",
                       {"buf": buffer, "i": tile}).wait_for()
           consume(np.asarray(buffer))

The creator must outlive every reader, without protection from Appose. And
if the creator crashes, its blocks leak on Linux and macOS until reboot,
since nobody else knows to free them.

Under the Hood
--------------

**Why the service owns everything.** Workers only ever talk to the service,
never to each other, so the service sees every array that moves, and can
count its holders. One owner means one simple rule, and no process ever
frees memory another one might still use.

**Why workers say when they are done** (with a ``RELEASE`` message), rather
than the service simply forgetting about arrays it sent:

1. **Counting.** Only the worker knows when it is done with an array; without
   being told, the service could never safely reuse the memory.
2. **Windows.** On Windows, a shared memory block exists only as long as some
   process holds it open; the service holds every managed block open until
   its arrays are done with.
3. **Crashes.** If a worker crashes, the service drops its holdings, so that
   no shared memory leaks.

**Why slabs.** Operating systems limit how many memory mappings a process may
have (e.g. about 65,000 on Linux), which large images split into many small
chunks can exhaust. So the service packs managed arrays of the same size into
*slabs*: larger blocks, each holding many arrays. Each new slab for a size
holds twice as many arrays as the last (up to 64 MiB), so a one-off array
takes a block of its own, while thousands of image cells share a few slabs.

Releasing happens automatically, once an array is no longer in use:

* **Python** releases an array once it is garbage collected, i.e. once
  nothing refers to it anymore (including any NumPy views of it). To release
  an ``NDArray`` sooner, call ``nda.shm.dispose()``. Note that objects caught
  in reference cycles are only collected when Python's cycle collector runs.
* **Java** releases an array once it is garbage collected, i.e. once neither
  it nor any buffer obtained from it (including slices and views such as
  ``asFloatBuffer()``) is reachable. To release it sooner, call
  ``nda.close()``. Note that a local variable may keep an array reachable
  until its method returns, even after its last use; and that a task keeps
  its inputs.

Either way, do not use an array after disposing of or closing it.

Closing a service (``service.close()``) waits for the tasks already started
to finish, since they may still need the service, e.g. to allocate managed
memory for their outputs; no new task can start meanwhile.

Where Copies Happen
-------------------

Sharing in place is the point of shared memory, so Appose copies array data
only where it must:

* A plain NumPy array, or (with imglib2-appose) an ``ArrayImg``, does not live
  in shared memory, so it is copied into managed memory once, when sent.
  Allocate managed arrays up front to avoid even that.
* A NumPy array that spans a whole managed array (e.g. one received earlier)
  is sent by reference; a slice or other part of one is copied.
* Managed arrays passed on, and unmanaged arrays, are never copied.

Learn More
----------

The test suites include a showcase of these scenarios, written to be read as
examples:

* Python: `tests/test_sharing.py
  <https://github.com/apposed/appose-python/blob/main/tests/test_sharing.py>`_
* Java: `SharingTest.java
  <https://github.com/apposed/appose-java/blob/main/src/test/java/org/apposed/appose/SharingTest.java>`_

For the messages and rules behind all this, see the "Managed Shared Memory"
section of :doc:`worker-protocol`; for the reasoning, see
:doc:`design-shared-memory`.
