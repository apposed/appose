package org.apposed.appose;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class Environment {

	private File baseDirectory;

	public Environment build() {
		// TODO Auto-generated method stub
		// Hash the state to make a base directory name.
		// - Construct conda environment from condaEnvironmentYaml.
		// - Download and unpack JVM of the given vendor+version.
		// - Populate ${baseDirectory}/jars with Maven artifacts.
		// - 
		return this;
	}

	public Service createService(String name, String... args) throws IOException {
		// TODO: How is the service associated with this particular environment?
		if (args.length == 0) throw new IllegalArgumentException("No executable given");
		File exe = new File(args[0]);
		if (!exe.isAbsolute()) exe = new File(baseDirectory, args[0]);
		args[0] = exe.getAbsolutePath();
		return new Service(name, args);
	}

	public File baseDirectory() {
		return this.baseDirectory;
	}

	// -- Python/Conda --

	private File condaEnvironmentYaml;

	public Environment conda(File environmentYaml) {
		this.condaEnvironmentYaml = environmentYaml;
		return this;
	}

	// -- Java --

	private String javaVendor;
	private String javaVersion;
	private List<MavenCoordinate> mavenCoordinates = new ArrayList<>();

	public Environment java(String vendor, String version) {
		this.javaVendor = vendor;
		this.javaVersion = version;
		return this;
	}

	public Environment maven(String coordinate) {
		return maven(new MavenCoordinate().coordinate(coordinate));
	}

	public Environment maven(MavenCoordinate coordinate) {
		mavenCoordinates.add(coordinate);
		return this;
	}
}
