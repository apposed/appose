package org.apposed.appose.event;

import org.apposed.appose.Service;

public class ServiceEvent {

	public final Service service;
	public final String commandID;

	public ServiceEvent(Service service, String commandID) {
		this.service = service;
		this.commandID = commandID;
	}
}
