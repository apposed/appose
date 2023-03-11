package org.apposed.appose.event;

import org.apposed.appose.Service;

public class StatusEvent extends ServiceEvent {

	public final String message;
	public final int current;
	public final int maximum;

	public StatusEvent(Service service, String commandID, String message,
		int current, int maximum)
	{
		super(service, commandID);
		this.message = message;
		this.current = current;
		this.maximum = maximum;
	}
}
