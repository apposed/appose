import numpy
import imagej
import sys
from multiprocessing.shared_memory import SharedMemory

# Get yourself an ndarray, however you want. :-)
print("Loading the image (from Fiji in this case)...")
ij = imagej.init('sc.fiji:fiji')
dataset = ij.io().open(sys.argv[1])
arr = ij.py.from_java(dataset)

print(f"Image loaded: shape={arr.shape}, dtype={arr.dtype}")

# Allocate shared memory matching size of numpy array.
print()
print("Allocating shared memory buffer...")
shm = SharedMemory(create=True, size=arr.size*arr.dtype.itemsize)

# NB: If this Python process closes, the memory will
# be destroyed even if other processes are using it.
#
# https://github.com/python/cpython/issues/82300
# ^ "resource tracker destroys shared memory segments
#    when other processes should still have valid access"
#
# https://stackoverflow.com/q/64915548
# ^ this shows how to use the undocumented unregister function
#   of resource_tracker to prevent Python from destroying shared
#   memory segments when the creating process shuts down.

# Copy our standard ndarray into a special one backed by that memory.
print("""
Copying the image into shared memory...
(we wouldn't have to do this if we had built a
shared-memory-backed ndarray in the first place ;-)""")
arr_shared = numpy.frombuffer(shm.buf, dtype=arr.dtype).reshape(arr.shape)
numpy.copyto(arr_shared, arr)

print(f"""
Done! Now run the following command to start another process:

  python -i src/main/python/receive-numpy-array-from-shm.py {shm.name} '{arr_shared.shape}' {arr_shared.dtype}

Then do things with arr_shared. E.g.: arr_shared[5,6,7,8] = 2
""")
