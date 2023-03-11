package org.apposed.appose;

import java.io.File;

public class Appose {

	public static Environment java(String vendor, String version) {
		return new Environment().java(vendor, version);
	}

	public static Environment conda(File environmentYaml) {
		return new Environment().conda(environmentYaml);
	}
}
