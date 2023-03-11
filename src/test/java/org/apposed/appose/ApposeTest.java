package org.apposed.appose;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.File;
import java.util.HashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;

public class ApposeTest {

	@Test
	public void testAppose() {
		final int actualNumber = 4;
		assertEquals(4, actualNumber);

		final boolean actualTruthValue = true;
		assertTrue(actualTruthValue);
	}

	@Test
	public void testHighLevel() {
		Environment env = Appose.java("zulu", "11")//
			.maven("org.jython:jython-slim:2.7.2")//
			.conda(new File("environment.yml"))//
			.build();

		Map<String, Object> inputs = new HashMap<>();
		inputs.put("name", "Chuckles");
		inputs.put("age", 27);
		inputs.put("portrait", pic);

		Task task = env.runJava("org.scijava.util.VersionUtils.getVersion", inputs);
		// ^ under the hood, calls env.process("**/java",
		// {"org.apposed.appose.JavaRunner"}).run("org.scijava.util.VersionUtils.getVersion",
		// inputs);
		Object returnValue = task.result().get("returnValue");
	}

  @Test
  public void testService() {
    // lower level - I don't think we need this...?
		Environment env = Appose.java("zulu", "11")//
			.maven("org.jython:jython-slim:2.7.2")//
			.conda(new File("environment.yml"))//
			.build();
    String[] args = {"myscript.py"};
    Service service = env.launch("bin/python", "my_runner_script.py");
    Task task = service.invoke("operationName", inputs);
    Map<String, Object> outputs = task.result();
  }
}
