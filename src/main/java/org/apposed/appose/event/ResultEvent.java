package org.apposed.appose.event;

import java.util.Map;

import org.apposed.appose.Service;

public class ResultEvent extends ServiceEvent {

	public final Map<String, Object> outputs;

	public ResultEvent(Service service, String commandID,
		Map<String, Object> outputs)
	{
		super(service, commandID);
		this.outputs = outputs;
	}
}
