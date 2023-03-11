import sys
import numpy
from multiprocessing.shared_memory import SharedMemory

shm = SharedMemory(sys.argv[1], create=False)
shape = eval(sys.argv[2])
dtype = eval(f"numpy.{sys.argv[3]}")

# reconstitute the numpy array from the shared memory
narr = numpy.frombuffer(shm.buf, dtype=dtype).reshape(shape)

# start up an ImageJ2 instance (no Fiji!)
import imagej
ij = imagej.init()

# wrap the narr into a RAI
rai = ij.py.to_java(narr)

print(f"Dimensions = {rai.numDimensions()}")
for d in range(rai.numDimensions()):
    print(rai.dimension(d))

print("Now do something with rai. E.g.: rai[8,7,6,5].get()")
