#!/usr/bin/env python

import gobject
import dbus
import dbus.service
import dbus.mainloop.glib

DBUS_NAME = 'org.openbmc.control.Chassis'
OBJ_NAME = '/org/openbmc/control/Chassis'

POWER_OFF = 0
POWER_ON = 1

class ChassisControlObject(dbus.service.Object):
	def __init__(self,bus,name):
		self.power_sequence = 0
		dbus.service.Object.__init__(self,bus,name)
		bus = dbus.SessionBus()
		try: 
			# Get PowerControl object
			power_control_service = bus.get_object('org.openbmc.control.Power','/org/openbmc/control/Power/0')
			self.power_control_iface = dbus.Interface(power_control_service, 'org.openbmc.control.Power')
			# Get ChassisIdentify object
			chassis_identify_service = bus.get_object('org.openbmc.leds.ChassisIdentify','/org/openbmc/leds/ChassisIdentify/0')
			self.identify_led_iface = dbus.Interface(chassis_identify_service, 'org.openbmc.Led');
			# Get HostControl object
			host_control_service = bus.get_object('org.openbmc.control.Host','/org/openbmc/control/Host/0')
			self.host_control_iface = dbus.Interface(host_control_service, 'org.openbmc.control.Host');

			bus.add_signal_receiver(self.power_button_signal_handler, 
						dbus_interface = "org.openbmc.Button", signal_name = "ButtonPressed")
    			bus.add_signal_receiver(self.power_good_signal_handler, 
						dbus_interface = "org.openbmc.control.Power", signal_name = "PowerGood")


		except dbus.exceptions.DBusException, e:
			# TODO: not sure what to do if can't find other services
			print "Unable to find dependent services: ",e


	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='s')
	def getID(self):
		return id


	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def setIdentify(self):
		print "Turn on identify"
		self.identify_led_iface.setOn()
		return None


	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def clearIdentify(self):
		print "Turn off identify"
		r=self.identify_led_iface.setOff()
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def setPowerOn(self):
		print "Turn on power and boot"
		self.power_sequence = 0
		if (self.getPowerState()==0):
			self.power_control_iface.setPowerState(POWER_ON)
			self.power_sequence = 1
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def setPowerOff(self):
		print "Turn off power"
		self.power_control_iface.setPowerState(POWER_OFF);
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='i')
	def getPowerState(self):
		state = self.power_control_iface.getPowerState();
		return state

	@dbus.service.method(DBUS_NAME,
		in_signature='', out_signature='')
	def setDebugMode(self):
		return None

	@dbus.service.method(DBUS_NAME,
		in_signature='i', out_signature='')
	def setPowerPolicy(self,policy):
		return None

	## Signal handler
	def power_button_signal_handler(self):
		# only power on if not currently powered on
		state = self.getPowerState()
		if state == POWER_OFF:
			self.setPowerOn()
		elif state == POWER_ON:
			self.setPowerOff();
		
		# TODO: handle long press and reset

	## Signal handler
	def power_good_signal_handler(self):
		if (self.power_sequence==1):
			self.host_control_iface.boot()
			self.power_sequence = 2



if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SessionBus()
    name = dbus.service.BusName(DBUS_NAME, bus)
    obj = ChassisControlObject(bus, OBJ_NAME)
    mainloop = gobject.MainLoop()
    
    print "Running ChassisControlService"
    mainloop.run()

