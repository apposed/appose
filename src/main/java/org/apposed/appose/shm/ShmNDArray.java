package org.apposed.appose.shm;

import org.apposed.appose.ndarray.NDArray;

/**
 * Implementation of {@link NDArray} backed by {@link SharedMemory}.
 *
 * @author Curtis Rueden
 * @param <T> The type of each array element.
 */
public class ShmNDArray<T> implements NDArray<T> {

	/**
	 * TODO
	 * 
	 * @param shape tuple of ints : Shape of created array.
	 * @param dtype data-type, optional : Any object that can be interpreted as a
	 *          numpy data type.
	 * @param buffer object exposing buffer interface, optional : Used to fill the
	 *          array with data.
	 * @param offset int, optional : Offset of array data in buffer.
	 * @param strides tuple of ints, optional : Strides of data in memory.
	 * @param cOrder {'C', 'F'}, optional : If true, row-major (C-style) order; if
	 *          false, column-major (Fortran-style) order.
	 */
	public ShmNDArray(long[] shape, Class<T> dtype, SharedMemory buffer,
		long offset, long[] strides, boolean cOrder)
	{
		
	}
}
