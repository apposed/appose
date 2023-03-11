# Appose

Python, Java, and JavaScript, working in harmony, side by side.
Separate processes, shared memory, minimal dependencies.

1. Construct an environment. E.g.:
   * Java with dependencies from Maven.
   * Python with dependencies from conda-forge.
   * JavaScript with dependencies from NPM.

2. Invoke routines in that environment:
   * Routines are run in a separate process.
   * The routine's inputs and outputs are passed via pipes (stdin/stdout).
   * NDArrays are passed as named shared memory buffers, for zero-copy access across processes.

```java
import org.apposed.appose.Appose;

Environment env = Appose.java("zulu", "11")
                        .maven("org.scijava:scijava-common:2.91.0")
                        .conda("environment.yml")
                        .build();

Map<String, Object> inputs = new HashMap<>();
inputs.put("name", "Chuckles");
inputs.put("age", 27);
inputs.put("portrait", pic);

// lower level - I don't think we need this...?
String[] args = {"myscript.py"};
Task task = env.process("bin/python", {"my_runner_script.py"}).run("operationName", inputs);
Map<String, Object> outputs = task.result();

// higher level
inputs = null;
// START HERE - goal: do not write any custom java code to frame your execution on the child side.
Task task = env.javaMethod("org.scijava.util.VersionUtils.getVersion", inputs);
// ^ under the hood, calls env.process("**/java", {"org.apposed.appose.JavaRunner"}).run("org.scijava.util.VersionUtils.getVersion", inputs);
Object returnValue = task.result().get("returnValue");
```

```python
import appose

env = appose.java("zulu", "11") \
            .maven("org.scijava:scijava-common:2.91.0") \
            .conda("environment.yml") \
            .build()

inputs = {
  "name": "Chuckles",
  "age": 27,
  "portrait": pic
}

task = env.javaMethod("org.scijava.util.VersionUtils.getVersion", inputs)
result = task.result()
returnValue = result["returnValue"]
```
