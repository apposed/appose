package org.apposed.appose;

import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.util.Map;

public class Service {

	private static final Gson GSON = new Gson();

	private final Process process;
	private final PrintWriter stdin;
	private final BufferedReader stdout;
	private final Thread thread;

	public Service(String name, String... args) throws IOException {
		ProcessBuilder pb = new ProcessBuilder(args);
		process = pb.start();
		stdin = new PrintWriter(new OutputStreamWriter(process.getOutputStream()));
		stdout = new BufferedReader(new InputStreamReader(process.getInputStream()));
		thread = new Thread(() -> {
			while (true) {
				try {
					String line = stdout.readLine();
					if (line == null) return; // pipe closed
					// Process the service update. It might be:
					// - A command completion event, including output results.
					// - A command progress update, including message and current/max.
					// TODO
					try {
						Map<?, ?> map = GSON.fromJson(line, Map.class);
						Object version = map.get("version");
						Object messageType = map.get("messageType");
						map.get("");
					}
					catch (JsonSyntaxException exc) {
						// TODO: proper logging
						exc.printStackTrace();
					}
				}
				catch (IOException exc) {
					return;
				}
			}
		}, "Appose-Service-" + name);
		thread.start();
	}

	public Task run(String command, Map<String, Object> inputs) {
		stdin.println(jsonify(inputs));
		// START HERE - need to also encode two more things:
		// 1) command name;
		// 2) an ID string (probably a UUID) to use for responses.
	}

	private String jsonify(Map<String, Object> inputs) {
		return GSON.toJson(inputs);
	}
}
