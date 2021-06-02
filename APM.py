#!/usr/bin/env python
#source : https://gist.github.com/vo/9331349
from pymavlink import mavutil
import datetime
import math as m 
import traceback

import pytz
import time

class rfm_drone_controller():
	def __init__(self):
		self.lat = 0
		self.lon = 0
		self.alt = 0
		self.is_armed = False
		self.is_enabled = False
		self.channels = ([1000,1000,1000,1000,1000,1000,1000,1000])
		self.airspeed = 0 # can be used for checking if drone has landed or not!
		self.groundspeed = 0
		self.rpy = ([0,0,0])
		self.A = ([0,0,0]) # may be used for checking crashes or something (maybe?)
		self.G = ([0,0,0]) # may be used for checking flatspins?
		self.fix_type = 0 # should be better than 2 for good position
		self.rate = 5 # update rate. probably 5 Hz is fine (maybe even less? this should only be initiated when arming done)
		self.device = '/dev/ttyACM0'
		self.baudrate = 115200
		self.time = 0
		self.timezone_str = 'Asia/Kolkata'
		# create a mavlink serial instance
		try:
			self.master = mavutil.mavlink_connection(self.device, baud=self.baudrate)
		except:
			self.master = mavutil.mavlink_connection('/dev/ttyACM1', baud=self.baudrate) # alternate device name
		# wait for the heartbeat msg to find the system ID
		self.master.wait_heartbeat()

		# request data to be sent at the given rate
		self.master.mav.request_data_stream_send(self.master.target_system, self.master.target_component, 
			mavutil.mavlink.MAV_DATA_STREAM_ALL, self.rate, 1)

	def handle_heartbeat(self,msg):
		mode = mavutil.mode_string_v10(msg)
		self.is_armed = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
		self.is_enabled = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_GUIDED_ENABLED

	def handle_rc_raw(self,msg):
		self.channels = ([msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw, 
				msg.chan5_raw, msg.chan6_raw, msg.chan7_raw, msg.chan8_raw])

	def handle_hud(self,msg):
		self.airspeed = msg.airspeed*0.01
		self.groundspeed = msg.groundspeed*0.01

	def handle_attitude(self,msg):
		yaw = -msg.yaw
		yaw += m.pi/2
		if(yaw>m.pi):
			yaw -= 2*m.pi
		if(yaw< -m.pi):
			yaw += 2*m.pi

		self.rpy = ([msg.roll,msg.pitch,yaw])
		self.G = ([msg.rollspeed,msg.pitchspeed,-msg.yawspeed])
		self.A[0] -= 9.89*m.sin(msg.pitch)
		if(m.fabs(self.A[0])<0.1):
			self.A[0] = 0
		self.A[0] = round(self.A[0],2)
		self.A[1] += 9.89*m.sin(msg.roll)
		if(m.fabs(self.A[1])<0.1):
			self.A[1] = 0
		self.A[1] = round(self.A[1],2)


	def handle_acc(self,msg):
		self.A = ([float(msg.xacc)*0.01,float(msg.yacc)*0.01,float(msg.zacc)*0.01])

	def handle_gps(self,msg):
		self.fix_type = msg.fix_type
		self.lat = round(msg.lat*1e-7,7)
		self.lon = round(msg.lon*1e-7,7)
		self.alt = round(msg.alt*1e-3,1)

	def read_loop(self):
		while True:
			msg = self.master.recv_match(blocking=False)
			# handle the message based on its type
			try:
				msg_type = msg.get_type()
				# print(msg_type)
				if msg_type == "BAD_DATA":
					if mavutil.all_printable(msg.data):
						sys.stdout.write(msg.data)
						sys.stdout.flush()
				elif msg_type == "RC_CHANNELS_RAW": 
					self.handle_rc_raw(msg)
				elif msg_type == "HEARTBEAT":
					self.handle_heartbeat(msg)
				elif msg_type == "ATTITUDE":
					self.handle_attitude(msg)
				elif msg_type == 'RAW_IMU':
					self.handle_acc(msg)
				elif msg_type == 'GPS_RAW_INT':
					self.handle_gps(msg)
				elif msg_type == "SYSTEM_TIME":
					self.time = datetime.datetime.utcfromtimestamp(msg.time_unix_usec*1e-6)
					timezone = pytz.timezone(self.timezone_str)
					self.time = timezone.utcoffset(self.time) + self.time
			# except Exception as e:
			# 	print(traceback.format_exc())
			except:
				time.sleep(0.1)
	def print_stuff(self):
		print("lat:",self.lat,"lon:",self.lon,"alt:",self.alt,"fix_type:",self.fix_type,"time:",self.time)
		



