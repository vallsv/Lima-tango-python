Pixirad Tango device
====================

This is the reference documentation of the Pixirad Tango device.

you can also find some useful information about the camera models/prerequisite/installation/configuration/compilation in the :ref:`Pixirad camera plugin <camera-pixirad>` section.

Properties
----------
==================== =============== =============== =========================================================================
Property name	     Mandatory	     Default value   Description
==================== =============== =============== =========================================================================
ip_address	     Yes	     N/A     	     The ip address or the hostname of the detector computer interface 
port_number	     No		     6666	     The port number for detector (DAQ commmands)
initial_model	     No	    	     PX8	     Model type PX1, PX2 or PX8
==================== =============== =============== =========================================================================


Attributes
----------
============================= ======= ======================= ==========================================================================
Attribute name		      RW      Type		      Description
============================= ======= ======================= ==========================================================================
high_threshold0		      rw      DevDouble		      High Energy threshold 0 (KeV)
low_threshold0		      rw      DevDouble		      Low Energy threshold 0 (KeV)
high_threshold1		      rw      DevDouble		      High Energy threshold 1 (KeV)
low_threshold1		      rw      DevDouble		      Low Energy threshold 1 (KeV)
dead_time_free_mode	      rw      DevString		      Enable or disable the free mode dead-time:
			      	      			       - **DEAD_TIME_FREE_MODE_OFF**
							       - **DEAD_TIME_FREE_MODE_ON**

cooling_temperature_setpoint  rw      DevDouble		      Cooling temperature setpoint for the peltier module of the detector
high_voltage_biais	      rw      DevDouble		      Bias tension for the high voltage in manual mode
high_voltage_delay_before_on  rw      DevDouble		      Delay for the hv before acquisition
h_v_refresh_period	      rw      DevShort		      How many image before hv is reset
delay_between_frames	      rw      DevShort		      Delay between frame in loop acquisition (millisecond)
color_mode		      rw      DevString		      Color mode:
			      	      			       - **COLMODE_1COL0**
							       - **COLMODE_2COL**
							       - **COLMODE_1COL1**
							       - **COLMODE_DTF**
							       - **COLMODE_4COL**

sensor_config_build	      rw      DevString		      The configuration build:
			      	      			       - **PX1**
							       - **PX2**
							       - **PX8**

trsf_mode		      rw      DevString		      Moderated or unmoderated udp transport, modes are:
			      	      			       - **UMOD**
							       - **UNMODH**
							       - **MOD**

h_v_bias_mode_power	      rw      DevBoolean	      Enable (True) or disable (False) the high voltage
hybrid_mode		      rw      DevString		      **CDTE** or **GAAS**
temperature_peltier_cold      rw      DevDouble		      Temperature of the peltier (live) cold surface in Celsuis
temperature_peltier_hot	      rw      DevDouble		      Temperature of the peltier (live) Hot surface in Celsuis
high_voltage_tension	      rw      DevDouble		      The tension of the High Voltage in Volt
box_humidity		      ro      DevDouble		      The moisture level in the detector box
box_temperature		      ro      DevDouble		      The temperature in the detector box in Celsuis
peltier_power		      ro      DevDouble		      The percentage of peltier power
alarm_temp_too_hot	      ro      DevBoolean	      The temperature is too hot alarm
alarm_temp_too_hot_enabled    ro      DevBoolean	      The Alarm <<Temperature is too hot>> is enabled or not (is watched or not)
alarm_temp_too_cold	      ro      DevBoolean	      The temperature is too cold alarm
alarm_temp_too_cold_enabled   ro      DevBoolean	      The Alarm <<Temperature is too cold>> is enabled or not (is watched or not)
alarm_humidity		      ro      DevBoolean	      The humidity is too high
alarm_humidity_enabled	      ro      DevBoolean	      The Alarm <<Humidity>> is enabled or not (is watched or not)
============================= ======= ======================= ==========================================================================

Please refer to the Pixirad documention for more information on parameter meanings.


Commands
--------

=======================	=============== =======================	===========================================
Command name		Arg. in		Arg. out		Description
=======================	=============== =======================	===========================================
Init			DevVoid 	DevVoid			Do not use
State			DevVoid		DevLong			Return the device state
Status			DevVoid		DevString		Return the device state as a string
getAttrStringValueList	DevString:	DevVarStringArray:	Return the authorized string value list for
			Attribute name	String value list	a given attribute name
=======================	=============== =======================	===========================================
