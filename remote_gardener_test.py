#!/usr/bin/python3

print( 'remote_gardener is now running!' )

# Imports
import time
import threading
import queue
import socket
import garden_pb2 as tool_shed
from google.protobuf.message import DecodeError
from datetime import timedelta
from datetime import datetime
from os import getpid

# Print process ID in case it gets hung
print( 'PID:', getpid() )

# Set up thread safe queues
q_in = queue.Queue()
q_out = queue.Queue()

# Set up event for terminating threads
kill = threading.Event()

# Set up socket and lock for test
s_lock = threading.Lock()
HOST = 'localhost'
PORT = 50007
with socket.socket( socket.AF_INET, socket.SOCK_STREAM ) as s:
	s.connect( ( HOST, PORT ) )
	s.setblocking( 0 )

	##################################################################
	# Thread that handles receiving responses
	def receiver ():
		print( 'Receiver thread is running' )

		while True:
			# Check to see if we should kill thread
			if kill.is_set():
				break

			with s_lock:
				try:
					data = s.recv( 1024 )
					if data:
						try:
							container = tool_shed.container()
							container.ParseFromString( data )
							#q_in.put( container )

							if container.HasField( 'all_device_updates' ):
								print( 'Received updates:' )
								for dev_update in container.all_device_updates.updates:
									print( tool_shed.container.devices.Name( dev_update.device ), 'is', 'active' if dev_update.status else 'inactive' )

							elif container.HasField( 'next_watering_time' ):
								dt = datetime.fromtimestamp( container.next_watering_time.timestamp.seconds )
								td = timedelta( seconds=container.next_watering_time.duration.seconds )
								print( 'Next watering scheduled for', td, 'at', dt, ', scheduled daily:', container.next_watering_time.daily )

							elif container.HasField( 'all_watering_times' ):
								print( 'Received all scheduled watering times:' )
								for watering_time in container.all_watering_times.times:
									dt = datetime.fromtimestamp( watering_time.timestamp.seconds )
									td = timedelta( seconds=watering_time.duration.seconds )
									print( 'Watering scheduled for', td, 'at', dt, ', scheduled daily:', watering_time.daily )

							else:
								print( 'An unsupported message has been received' )

						except DecodeError:
							print( 'Was not able to parse message!' )

				except BlockingIOError:
					continue

				except ConnectionAbortedError:
					kill.set()

				except ConnectionResetError:
					kill.set()

	# Turn on the receiver thread
	receiver_thread = threading.Thread( target=receiver, daemon=True )
	receiver_thread.start()
	##################################################################

	##############################################################
	# Thread that handles sending queued messages
	def sender ():
		print( 'Sender thread is running' )

		while True:
			# Check to see if we should kill thread
			if kill.is_set():
				break

			try:
				container = q_out.get_nowait()
				data = container.SerializeToString()
				with s_lock:
					try:
						s.sendall( data )
						time.sleep( 0.25 )

					except ConnectionAbortedError:
						kill.set()

					except ConnectionResetError:
						kill.set()

			except queue.Empty:
				continue

	# Turn on the sender thread
	sender_thread = threading.Thread( target=sender, daemon=True )
	sender_thread.start()
	##############################################################

	####################################################################
	# Thread that handles queueing the heartbeat
	def heartbeat ():
		print( 'Heartbeat thread is running' )

		while True:
			# Check to see if we should kill thread
			if kill.is_set():
				break

			container = tool_shed.container()
			container.heartbeat = 1
			q_out.put( container )
			time.sleep( 1 )


	# Turn on the heartbeat thread
	heartbeat_thread = threading.Thread( target=heartbeat, daemon=True )
	heartbeat_thread.start()
	####################################################################

	# Choice variable
	choice = 0

	# Main thread loop, reads commands and sends them to the sender_thread
	while True:
		if kill.is_set():
			break

		if choice == -2:
			continue

		print( 'Options:' )
		print( '\t0. Device status update' )
		print( '\t1. Set daily watering time' )
		print( '\t2. Get next scheduled watering time' )
		print( '\t3. Get all scheduled watering times' )
		print( '\t4. Cancel future scheduled watering time' )
		print( '\t5. Water now' )
		print( '\t6. Stop watering' )
		print( '\t7. Pump now' )
		print( '\t8. Stop pumping' )
		print( '\tPress ENTER to exit.' )
		choice = input( 'Choose an option:\n' )
		if choice == '':
			# Notify all threads of shutdown
			kill.set()
			# Continue
			continue
		container = tool_shed.container()
		try:
			choice = int( choice )
			if choice == 0:
				container.get_device_updates = 1
			elif choice == 1:
				hour = input( 'Input an hour of day (0 - 23):\n' )
				minute = input( 'Input a minute of hour (0 - 59):\n' )
				duration = input( 'Input a duration in minutes:\n' )
				hour = int( hour )
				minute = int( minute )
				duration = int( duration )
				if hour < 0 or hour > 23:
					print( 'Not an hour of day!' )
					container = None
				elif minute < 0 or minute > 59:
					print( 'Not a minute of hour!' )
					container = None
				elif duration < 0:
					print( 'Duration is less than 0!' )
					container = None
				else:
					dt = datetime.today()
					print( dt )
					if hour < dt.hour:
						dt = dt + timedelta( days=1 )
					elif hour == dt.hour and minute < dt.minute:
						dt = dt + timedelta( days=1 )
					dt = dt.replace( hour=hour, minute=minute, second=0, microsecond=0 )
					print( dt )
					container.set_watering_time.timestamp.seconds = int( dt.timestamp() )
					td = timedelta( minutes=duration )
					container.set_watering_time.duration.FromTimedelta( td )
					container.set_watering_time.daily = True

			elif choice == 2:
				container.get_next_watering_time = 1

			elif choice == 3:
				container.get_watering_times = 1

			elif choice == 4:
				hour = input( 'Input an hour of day (0 - 23):\n' )
				minute = input( 'Input a minute of hour (0 - 59):\n' )
				duration = input( 'Input a duration in minutes:\n' )
				hour = int( hour )
				minute = int( minute )
				duration = int( duration )
				if hour < 0 or hour > 23:
					print( 'Not an hour of day!' )
					container = None
				elif minute < 0 or minute > 59:
					print( 'Not a minute of hour!' )
					container = None
				elif duration < 1:
					print( 'Duration is less than 1!' )
					container = None
				else:
					dt = datetime.today()
					print( dt )
					if hour < dt.hour:
						dt = dt + timedelta( days=1 )
					elif hour == dt.hour and minute < dt.minute:
						dt = dt + timedelta( days=1 )
					dt = dt.replace( hour=hour, minute=minute, second=0, microsecond=0 )
					print( dt )
					container.cancel_watering_time.timestamp.seconds = int( dt.timestamp() )
					td = timedelta( minutes=duration )
					container.cancel_watering_time.duration.FromTimedelta( td )
					container.cancel_watering_time.daily = True
					
			elif choice == 5:
				duration = input( 'Input a duration in minutes:\n' )
				duration = int( duration )
				if duration < 0:
					print( 'Duration is less than 0!' )
					container = None
				else:
					td = timedelta( minutes=duration )
					container.water_now.duration.FromTimedelta( td )

			elif choice == 6:
				container.stop_watering = 1

			elif choice == 7:
				duration = input( 'Input a duration in minutes:\n' )
				duration = int( duration )
				if duration < 0:
					print( 'Duration is less than 0!' )
					container = None
				else:
					td = timedelta( minutes=duration )
					container.pump_now.duration.FromTimedelta( td )

			elif choice == 8:
				container.stop_pumping = 1

			# Secret option: override sensor
			elif choice == -1:
				sns_list = [
					tool_shed.container.devices.DEV_SNS_TANK_FULL,
					tool_shed.container.devices.DEV_SNS_TANK_EMPTY,
					tool_shed.container.devices.DEV_SNS_WELL_EMPTY,
					tool_shed.container.devices.DEV_SNS_RAIN
				]
				print( 'Secret sensor override menu!' )
				print( '\t0. DEV_SNS_TANK_FULL' )
				print( '\t1. DEV_SNS_TANK_EMPTY' )
				print( '\t2. DEV_SNS_WELL_EMPTY' )
				print( '\t3. DEV_SNS_RAIN' )
				sensor = input( 'Choose a sensor (0 - 3):\n' )
				print( '\t0. INACTIVE' )
				print( '\t1. ACTIVE' )
				status = input( 'Choose a status (0 - 1):\n' )
				sensor = int( sensor )
				status = int( status )
				if sensor < 0 or sensor > 3:
					print( 'Invalid sensor choice!' )
					container = None
				elif status < 0 or status > 1:
					print( 'Invalid status choice!' )
					container = None
				else:
					container.sensor_override.device = sns_list[ sensor ]
					container.sensor_override.status =  ( status != 0 )

			# Secret option: shutdown daemon
			elif choice == -2:
				container.shutdown = 1

			else:
				container = None

		except ValueError:
			print( 'Not an integer choice!' )
			container = None

		if container:
			q_out.put( container )

	receiver_thread.join()
	sender_thread.join()
	heartbeat_thread.join()
