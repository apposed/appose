# Adapted from:
# https://realpython.com/python-mmap/#sharing-data-between-processes-with-pythons-mmap

from multiprocessing import Process
from multiprocessing import shared_memory
from random import randint

size = 100*1024*1024

def modify(buf_name):
    shm = shared_memory.SharedMemory(buf_name)
    for _ in range(100):
        i = randint(0, size)
        shm.buf[i:i+1] = b"*"
    #shm.buf[40:50] = b"b" * 10
    shm.close()

if __name__ == "__main__":
    shm = shared_memory.SharedMemory(create=True, size=size)

    try:
        shm.buf[0:size] = b"-" * size
        proc = Process(target=modify, args=(shm.name,))
        proc.start()
        for _ in range(100):
            i = randint(0, size)
            shm.buf[i:i+1] = b"x"
        proc.join()
        print(bytes(shm.buf[:100]))
        stars = sum(1 for b in bytes(shm.buf) if b == ord("*"))
        exes = sum(1 for b in bytes(shm.buf) if b == ord("x"))
        print(f'star count = {stars}')
        print(f'ex count = {exes}')
    finally:
        shm.close()
        shm.unlink()
