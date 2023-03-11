package org.apposed.appose;

public class MavenCoordinate {

	private String g;
	private String a;
	private String v = "RELEASE";
	private String c;
	private String p = "jar";
	private String s = "compile";
	private boolean optional;

	@SuppressWarnings("fallthrough")
	public MavenCoordinate coordinate(String coordinate) {
		String[] tokens = coordinate.split(":");
		switch (tokens.length) {
			case 6: scope(tokens[5]);
			case 5: packaging(tokens[4]);
			case 4: classifier(tokens[3]);
			case 3: version(tokens[2]);
			case 2: artifactId(tokens[1]);
			case 1: groupId(tokens[0]);
				break;
			default:
				throw new IllegalArgumentException("Invalid coordinate: " + coordinate);
		}
		return this;
	}

	public MavenCoordinate groupId(String g) {
		this.g = g;
		return this;
	}

	public MavenCoordinate artifactId(String a) {
		this.a = a;
		return this;
	}

	public MavenCoordinate version(String v) {
		this.v = v;
		return this;
	}

	public MavenCoordinate classifier(String c) {
		this.c = c;
		return this;
	}

	public MavenCoordinate packaging(String p) {
		this.p = p;
		return this;
	}

	public MavenCoordinate scope(String s) {
		this.s = s;
		return this;
	}

	public MavenCoordinate optional(boolean optional) {
		this.optional = optional;
		return this;
	}
}
