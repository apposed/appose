# Design Note: Shared Memory with One Owner and Reference Counts

*October 7, 2026 · Curtis Rueden · Status: implemented; see "Decisions made while implementing" below*

Design: the service owns all managed shared memory, and counts references to each region; workers never allocate or free anything themselves. One counting rule covers handing arrays off, sharing them and passing them on, and fixed-size slab slots keep chunked images under the operating system's mapping limits. "Alternatives considered" below explains why simpler-looking designs fall short; we tried several of them first.

## Why

Arrays should move between processes without copying and without boilerplate: a plain NumPy array (or ImgLib2 image) in a task's inputs or outputs should just work, and stay valid as long as anyone uses it.

- **Lifetimes cross processes.** Once an array has been shared, the process that created it cannot know when the others are done with it. Some process must count.
- **Mapping limit.** Linux caps memory mappings per process at about 65,530 (`vm.max_map_count`). With one block per 1 MB cell, a process hits it at 64 GB. Slabs fix this: one mapping holds many cells.
- **Star topology.** Workers only ever talk to the service, never to each other. So the service already sees every array reference that moves, and a single owner there can count them.

Prior art follows the same shape: Apache Arrow's Plasma store and Ray's object store keep one central store with reference counts and mapped clients. Plasma was removed from Arrow in 2023 for its maintenance cost, so this design stays deliberately narrow. Nothing comparable spans Java and Python.

## The model

A region is freed when nobody holds it anymore; only the service decides that, and only the service creates and unlinks blocks.

- **Region:** a span (block, offset, length) of a shared memory block. Managed blocks are slabs, each holding many fixed-size slots.
- **Holders:** the service itself, while any object in the service process views the region; and each worker, once per time the service has sent it the region.
- **The rule:** count = (1 if the service holds the region, else 0) + references held by workers. At zero, the slot is free for reuse.

Every operation is one step under that rule:

1. The service sends a region to a worker: +1 for that worker.
2. The worker is done with it (its view is closed or garbage collected) and sends `RELEASE`: −1.
3. A worker needs memory (e.g. for a result): it asks the service to allocate a slot, and gets back a region reference: +1 for that worker.
4. A worker sends a region to the service: the service resolves it to its own region, as it resolves its own `service_object` references. No new reference; the worker's stays until its `RELEASE`.
5. A worker dies: the service drops all of that worker's references.

The old modes become usage patterns, not wire modes. A "transfer" is a sender dropping its own reference right after sending, which leaves the receiver as the only holder. A "lease" is simply several holders at once.

## At a glance

```text
Only the service creates, counts and frees shared memory

+-- Service (sole owner) ---------------+                         +-- Worker 1 ---------------------+
|  Memory object                        |  region reference: +1   |  Views the regions it was sent  |
|    allocates slots for workers        | ----------------------> |  Releases each one when done    |
|  Region table                         |  RELEASE: -1            |                                 |
|    one count per region; frees at 0   | <---------------------- |                                 |
|  Slabs                                |  allocate (a call)      |                                 |
|    shared memory blocks of slots      | <---------------------- |                                 |
+---------------------------------------+                         +---------------------------------+
                                           (the same for every worker)
```

Workers only hold and release references; the service counts them per region, and frees a slot once its count reaches zero.

## Walkthrough

Every scenario Appose supports, including its showcase tests, reduces to the same rule.

| Scenario | What happens | Freed when |
| --- | --- | --- |
| Service passes a NumPy image to a worker | Service copies it into a slot, sends it (+1 worker), drops its own view | The worker releases it |
| Worker returns a NumPy result | Worker allocates a slot (+1 worker), fills it, sends it; the service now holds it too | The worker has released it and the service's result object is collected |
| Cell cache shared by two workers | Service loads the cell into a slot once, sends it to each worker (+1 each) | The cache has evicted it and both workers released it |
| Worker writes into an output image | Service allocates the image and sends it; the worker writes in place | The service is done with it and the worker released it |
| Relay from worker A to worker B | A's region reaches the service, which sends it on to B (+1 B) | A, B and the service are all done |
| Worker crashes | The service drops that worker's references | Per the other holders |
| Service crashes | Slabs are orphaned; Python's resource tracker unlinks them | Open question for Java |
| Service closes while a task still runs | The task's outputs still arrive and resolve to service regions | As usual |

Forwarding never copies, and no process ever frees memory another process might still be using.

## Wire format

The `ownership` field goes: a reference only needs one flag saying the receiver must release it, and only the service sets it.

- **Why `ownership` is unnecessary.** It said transfer or lease, i.e. whether the data is the receiver's own. Under reference counting, that is a consequence of who else holds the region, not something the receiver must be told. What remains is whether to send `RELEASE`, since an application-managed `NDArray` needs none.
- **Reference:** `{"appose_type": "shm", "name", "rsize", "offset", "length", "managed": true}`. A plain block reference (no offset, length or flag) keeps today's meaning.
- **Only service-to-worker references need the flag.** A worker sending a managed region to the service names a region the service owns; the service recognizes its own blocks.
- **`RELEASE` flows one way:** a response from worker to service, listing `{name, offset}` once per reference returned. The `RELEASE` request from service to worker goes away.
- **Allocation needs no new message.** The service exports a built-in memory object (e.g. `_appose_memory`), which workers call through the existing CALL/REPLY mechanism, as with any service object.
- **Version guard:** the service still announces support to the worker via an environment variable (`APPOSE_SHM`, naming the memory backend); without it, a worker falls back to proxies.

One invariant matters: a sender keeps its references alive until the message carrying them is written. Otherwise a garbage-collected reference could send `RELEASE` ahead of the message that uses it, and the region would be freed in between.

## Unmanaged references

A reference without the `managed` flag is unmanaged: the receiver maps it and uses it, never sends `RELEASE`, and its creator decides when it goes away. Any process, a worker included, may create blocks of its own and share them this way; the service's counts cover only regions it allocated.

- **A worker-owned ring buffer.** A camera or video worker writes frames into a ring of 64 slots in one block it created, and sends the service each frame's offset. A slot's reuse is a matter of timing (frame n is valid until frame n+64), which a per-frame `RELEASE` could not prevent anyway.
- **Memory Appose did not create.** An acquisition driver or another library owns a named segment; Appose only passes views of it. Only the external owner may free it.
- **A large read-only resource.** A worker loads a reference atlas or lookup table into its own block at startup, and the service views it at will. Nobody frees it before the worker exits, so counting would be pure overhead.
- **Today's explicit `NDArray`.** A buffer the application creates and disposes of itself, e.g. one reused across many calls. Existing code keeps working unchanged.

The creator must outlive every reader, with no protection from Appose: on Linux and macOS a reader keeps a valid mapping after an early unlink, and on Windows its open handle keeps the block alive. If the creator crashes, its blocks leak on Linux and macOS, since nobody else knows to unlink them.

## Allocator

The allocator only ever hands out fixed-size slots, so it needs no general-purpose memory management.

- **Size classes.** Cells of one image are all the same size, so each slot size gets its own slabs. Edge cells use a full slot.
- **Slabs.** A slab holds N slots, e.g. at least 16 slots and 64 MiB. Then 1 TB of 1 MB cells takes about 16,000 mappings, under the Linux limit. Tune once measured.
- **Bookkeeping.** One free-slot bitmap per slab; allocation takes the first free slot. Empty slabs are unlinked after a grace period, keeping a few warm.
- **Arrays that are not cells** (e.g. results of arbitrary size): round up to power-of-two size classes, or give each array larger than a slab its own block.
- **Other limits:** `/dev/shm` holds at most half of RAM by default, and Docker's default is only 64 MB. Apple silicon pages are 16 KB, so slots smaller than that waste space unless packed into slabs.

## ImgLib2 integration

A cell loader that wraps another cell loader, with hooks for allocating, copying and freeing cells, fits this model directly.

- **Accesses:** cells use ImgLib2's NIO `BufferAccess` types over slices of a slab's `ByteBuffer`, as `ShmImg` already does for whole images.
- **Service side:** a wrapping cell loader loads cells from any source loader (e.g. N5 or zarr) into slots. The cache holds them as the service's own references.
- **Worker side:** a proxy cell loader calls the service's cell source, e.g. `source.cell(index)`, and wraps the managed region it gets back as an access.
- **Freeing:** imglib2-cache's soft-reference caches already evict through garbage collection. Java releases a region once nothing derived from its buffers is reachable, so a collected access frees its slot. Bounded caches with explicit eviction would call close instead.
- **Writes:** land in place, visible to every holder. Tracking dirty cells and writing them back is the service-side loader's job.

## Alternatives considered

Each of these is what one might reach for first. Several of them were implemented along the way, and each failed in a way that shaped the design above.

### Copy the data into the message

Encode array data in the JSON message, e.g. as base64. This is what most RPC systems do, and it needs no shared memory at all.

It fails on size: a 1 GB image becomes 1.3 GB of text, encoded, written through a pipe, read and decoded, and then exists twice. Appose exists to avoid exactly that. Small arrays could go this way, but then behavior (copy or share) would hinge on a size threshold; one model for all sizes is simpler.

### Leave arrays as proxies

Before this work, a NumPy array in a worker's outputs came back as a proxy (a `WorkerObject`), with every element access a round trip. That is correct but useless for pixel data, and every application wrote the same boilerplate to copy arrays into an `NDArray` first.

### Each process allocates, and the creator frees

The original `NDArray` model: whoever creates a block unlinks it when done. That is simple and still the right model for unmanaged memory (see above). But for arrays passed as task inputs and outputs, the creator usually cannot tell when the receiver is done: a worker returning a result has no idea how long the service keeps it. Freeing too early breaks a receiver that has not attached the block yet, e.g. while the message referring to it is still in flight; freeing too late leaks until the creator exits.

### Transfer ownership with the array

Our first prototype: sending an array transfers it, and the receiver becomes its owner and frees it. This handles the common handoff (a worker returns a result) neatly, and a NumPy array arriving this way can simply become the receiver's own NumPy array.

It breaks as soon as data is shared rather than handed off. A cell cache sends the same cell to two workers; an output image is written by a worker and read by the service at once. Neither has a single next owner. Forwarding a received array on to another process either copies it or transfers it a second time, and we needed a "transferred twice" error to catch the latter. Transfer also put allocation on both sides, so each side needed crash cleanup for the other's blocks.

### Add leases beside transfers

Our second iteration: a "lease" mode, in which the sender keeps ownership and the receiver must say when it is done, with sublets when a lessee passes the array on. It was correct, and its showcase tests covered every scenario in the walkthrough above.

But it took two ownership modes on the wire (an `ownership` field), lending and sublet bookkeeping, copy-on-forward, "the creator unlinks", and crash cleanup in both directions: about 2,500 lines in appose-java and 1,600 in appose-python, before any slab code. And the bookkeeping in appose-java at first assumed a single worker per service; supporting several required yet more of it. The insight that replaced it: workers only ever talk to the service, so if the service owns everything, transfer and lease become usage patterns of one reference count, rather than modes.

### Tie lifetime to the task

Free an array once the task whose inputs or outputs carried it completes. It needs no `RELEASE` message at all. But results routinely outlive their tasks (the service keeps them; a worker exports them for later tasks), and cached cells outlive any one task by design. Garbage collection is the only reliable signal of "nobody uses this anymore", so both languages release regions when their views are collected (or explicitly closed).

### Mark NumPy arrays on the wire

To make NumPy arrays round-trip as NumPy arrays, one early design added a `"numpy": true` flag to array references. That ties the protocol to one language's types: a Java receiver would have to ignore it, and an ImgLib2 image would need a flag of its own. Instead, the wire says only whether a reference is managed, and each language decides how to present it: Python as a NumPy array, Java as an `NDArray`, which imglib2-appose can wrap as an image.

### One block per array

Give each array its own shared memory block, as `NDArray` always has. It is the simplest allocator, but each block is one memory mapping in every process that views it, and Linux allows only about 65,000 per process: a large image in 1 MB cells exhausts that at 64 GB. Slabs keep the number of mappings proportional to the number of distinct cell sizes and the data volume, not the number of arrays.

A general-purpose allocator over one large segment (as in partake, or Plasma) avoids the limit too, but cannot grow a mapped segment portably, so it must reserve its size up front. Fixed-size slots in growing slabs need neither, since image cells come in few sizes.

### An external shared memory daemon

A separate process (e.g. partake, a C++ daemon for shared memory) could own the memory instead of the service, which would let processes share memory with no service involved, and survive the crash of any one of them. It is a promising foundation, and the memory backend interface exists so that one can be tried. For now it is deferred: it has no Python or Java client yet (and Java 8 lacks Unix domain sockets), it reserves a fixed-size pool, and it would add a native binary to every Appose installation.

## Open questions

- [ ] Java service crash: who unlinks its orphaned slabs? Options: a tiny janitor process, or workers unlinking the blocks they know of on EOF.
- [ ] Allocation latency: is one call per result fast enough, or should a worker reserve slots in batches? (For now, one call per allocation; to be measured.)
- [x] Python: should a managed region always arrive as a NumPy array? Then a NumPy view spanning a managed region could be sent back by reference. Yes: see below.
- [ ] A read-only hint for shared cells (NumPy `writeable=False`, Java `asReadOnlyBuffer`)?
- [ ] Concurrent writes to a shared region: left to applications to coordinate?
- [x] Slab size and retirement policy defaults. A first policy: see below; tune once measured.
- [x] Application-managed `NDArray`: keep as is, alongside managed regions? Yes: see Unmanaged references.

## Decisions made while implementing

- **Python representation.** A managed array arrives in Python as a NumPy array. A NumPy array spanning a whole managed region (C-contiguous, native byte order, starting at the region's start) is sent by reference; any other NumPy array is copied into a new managed region. Unmanaged arrays still arrive as `NDArray`s.
- **API.** `NDArray(dtype, shape, managed=True)` in Python, `NDArray.managed(dType, shape)` in Java, and `ShmImg.managed(type, dims)` in imglib2-appose allocate managed arrays, in a worker by asking the service.
- **Allocation call.** The service exports a built-in function `_appose_allocate(nbytes)`, which workers call through the existing CALL/REPLY mechanism; one call per allocation, for now.
- **Slab policy.** A slot's size is the requested size rounded up to 64 bytes, and each slot size has its own slabs. Each new slab of a slot size holds twice as many slots as the last (1, 2, 4, …), up to 64 MiB: a one-off array takes a block of its own, while many arrays of one size share few blocks. An empty slab is unlinked right away.
- **Closing.** `Service.close()` now waits for the tasks already started to finish before closing the worker's input, since a worker's outputs may need allocation calls. No new task can start once closing.
- **Version guard.** The service sets `APPOSE_SHM` in the worker's environment to the name of its memory backend, e.g. `APPOSE_SHM=builtin`.
- **Memory backends.** The scheme above is one implementation (the "builtin" backend) of a small internal interface, so that others can be tried alongside it, e.g. one built on a shared memory daemon such as partake. A `MemoryBackend` allocates managed memory, and creates a `MemoryLink` for each connection, which describes the references sent over it (the fields besides `appose_type` and `managed`), resolves those received, and is told when references are sent or released and when the connection closes. A backend reaches the other side through a `Peer`: it may send messages (e.g. `RELEASE`), call the service (from a worker) or export functions (from a service). Backends register under a name, with a service side and a worker side; a service uses "builtin" unless told otherwise.
- **Errors.** A closed (or disposed) view of a managed region cannot be sent, and the service rejects references to managed regions it does not have.

## Next steps

1. Build the ImgLib2 cell loader wrapper on the region API.
2. Try a memory backend built on an external daemon such as partake, and compare.
