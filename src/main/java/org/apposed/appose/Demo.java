/*-
 * #%L
 * Appose: multi-language interprocess plugins with shared memory ndarrays.
 * %%
 * Copyright (C) 2023 Appose developers.
 * %%
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 * #L%
 */
package org.apposed.appose;

import com.sun.jna.Pointer;

import java.nio.ByteBuffer;
import java.nio.file.Path;
import java.nio.file.Paths;

/*
# Plan:
# 1. start Java *first*
# 2. allocate big shm buffer using LArray (encapsulated)
#    - output: buf_name
# 3. start Python process via ProcessBuilder
# 4. from multiprocess import shared_memory
# 5. shm = shared_memory.SharedMemory(buf_name)
# 6. write to shm
# 7. meanwhile, in Java: write to shm also
# 8. finally, Python returns json
*/

/**
 * <strong>Unfinished</strong> Java-first version of the demo.
 *
 * @author Curtis Rueden
 */
public class Demo {

	public static Path getPythonExe(String condaEnv) {
		String condaPrefix = System.getenv("CONDA_PREFIX");
		if (condaPrefix == null) throw new RuntimeException("No CONDA_PREFIX!");
		Path condaEnvPath = Paths.get(condaPrefix, "envs", condaEnv);
		if (!condaEnvPath.toFile().exists()) {
			throw new RuntimeException("No conda environment '" + condaEnv + "' found");
		}
		Path pythonExePath = condaEnvPath.resolve("bin").resolve("python.exe");
		if (!pythonExePath.toFile().exists())
			pythonExePath = condaEnvPath.resolve("bin").resolve("python");
		if (!pythonExePath.toFile().exists()) {
			throw new RuntimeException("No Python executable found at '" + //
				pythonExePath + "' or (.exe)");
		}
		return pythonExePath.toAbsolutePath();
	}

	public static void main(final String... args) throws Exception {
		// TEMP: Start an embedded Python, so that we can
		// use Python's multiprocess.shared_memory feature.

		String jepPythonExe = getPythonExe("jep").toString();

		try (Interpreter interp = new SharedInterpreter()) {
				interp.exec("from multiprocess import shared_memory");
				interp.exec("s = 'Hello World'");
				interp.exec("System.out.println(s)");
				interp.exec("print(s)");
				interp.exec("print(s[1:-1])");
				Object result = interp.getValue("s");
		}

		String pijPythonExe = getPythonExe("pyimagej-dev").toString();

		String cwd = System.getProperty("user.dir");
		Path pythonScriptPath = Paths.get(cwd, "go.py");
		ProcessBuilder pb = new ProcessBuilder(pijPythonExe, pythonScriptPath.toString());
		Process p = pb.start();

		// Use JNA to wrap a memory address to a ByteBuffer. 2GB len max.
		long address = 0; // FIXME
		long offset = 0; // FIXME
		long length = 0; // FIXME
		ByteBuffer shm = new Pointer(address).getByteBuffer(offset, length);

		p.waitFor();

		//Path tempDir = Files.createTempDirectory("curtis");
		//System.out.println(tempDir);
		// on macos, outputs something of the form:
		// /var/folders/n2/5q09bjq11kv6xwpp0xlg4npc0000gq/T/curtis7281232030776860312
	}

}
