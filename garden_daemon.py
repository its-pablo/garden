#!/usr/bin/python3

# Imports
import threading
import queue
import heapq
import socket
import json
from os import path
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import Parse
from google.protobuf.message import DecodeError
import garden_pb2 as tool_shed
import garden_utils as gu
from datetime import timedelta
from datetime import datetime

# Important constant
VERSION = '0.3'
HOST = 'localhost'
PORT = 50007
WATERING_SCHEDULE_FILE_NAME = 'watering.json'
MUTE_HEARTBEAT = True

print( 'garden_daemon verion', VERSION, 'is now running!' )

# Set up thread safe queues
q_in = queue.Queue() # This queue is going to hold the incoming messages from the client
q_out = queue.Queue() # This queue is going to hold the outgoing messages to the client
# Note: "messages" in this context efers to the protobuf messages defined in garden.proto

###############################################################################
# Thread that handles the gardening and requests
def gardener():
	print( 'Gardener thread is running' )

	# Create watering queue
	q_water = []

	# Create device lock, used to synchronize with watering timer threads
	d_lock = threading.Lock()

	# Create device map:
	# protobuf device enum => ( status getter, status setter )
	dev_map = {
		tool_shed.container.devices.DEV_ACT_PUMP: ( gu.get_pump_status, gu.set_pump_status ),
		tool_shed.container.devices.DEV_ACT_VALVE: ( gu.get_valve_status, gu.set_valve_status ),
		tool_shed.container.devices.DEV_SNS_TANK_FULL: ( gu.get_tank_full_status, None ),
		tool_shed.container.devices.DEV_SNS_TANK_EMPTY: ( gu.get_tank_empty_status, None ),
		tool_shed.container.devices.DEV_SNS_WELL_EMPTY: ( gu.get_well_empty_status, None ),
		tool_shed.container.devices.DEV_SNS_RAIN: ( gu.get_rain_status, None ),
	}

	def save_message_to_json ( message, file_name ):
		json_message = MessageToJson( message )
		with open( file_name, 'w', encoding='utf-8' ) as file:
			file.write( json_message )
		print( 'Saved message to JSON!' )

	def write_water_sched_to_json ():
		# Check if any watering events are queued
		if q_water:
			# Find all queued watering events:
			container = tool_shed.container()
			for water in q_water:
				time = container.all_watering_times.times.add()
				time.CopyFrom( water[1] )
			save_message_to_json( container, WATERING_SCHEDULE_FILE_NAME )

	# Check to see if the watering schedule file exists
	if path.isfile( WATERING_SCHEDULE_FILE_NAME ):
		print( 'Watering schedule exists! Importing and updating.' )

		with open( WATERING_SCHEDULE_FILE_NAME, 'r', encoding='utf-8' ) as file:
			json_message = file.read()
			container = tool_shed.container()
			print( json_message )
			container = Parse( json_message, container )
			dt_now = datetime.today()

			for watering_time in container.all_watering_times.times:
				
				# Not expired put in q_water as is
				if watering_time.timestamp.seconds > int( dt_now.timestamp() ):
					heapq.heappush( q_water, ( watering_time.timestamp.seconds, watering_time ) )
				
				# Expired but daily, schedule new watering time
				elif watering_time.daily:
					print( 'Rescheduling expired daily watering event' )
					dt = datetime.fromtimestamp( watering_time.timestamp.seconds )
					td = dt_now - dt
					td = timedelta( days=td.days ) + timedelta( days=1 )
					dt = dt + td
					watering_time.timestamp.seconds = int( dt.timestamp() )
					heapq.heappush( q_water, ( watering_time.timestamp.seconds, watering_time ) )
		
		# Save changes
		write_water_sched_to_json()

	def stop_watering ():
		with d_lock:
			status = gu.set_valve_status( False )
			if status == False:
				print( 'Stopped watering successfully!' )
			else:
				print( 'Failed to stop watering!' )

	def start_watering ():
		with d_lock:
			status = gu.set_valve_status( True )
			if status == True:
				print( 'Started watering successfully!' )
			else:
				print( 'Failed to start watering!' )

	def stop_pumping ():
		with d_lock:
			status = gu.set_pump_status( False )
			if status == False:
				print( 'Stopped pumping successfully!' )
			else:
				print( 'Failed to stop pumping!' )

	def start_pumping ():
		with d_lock:
			status = gu.set_pump_status( True )
			if status == True:
				print( 'Started pumping successfully!' )
			else:
				print( 'Failed to start pumping!' )

	def check_watering ():
		# Check if any watering events queued
		if q_water:
			# Get next watering event from heap queue
			seconds, watering_time = heapq.heappop( q_water )
			
			# Check if event has expired
			dt = datetime.today()
			if seconds < int( dt.timestamp() ):
				print( 'Watering event expired!' )
				rain_dry = True
				with d_lock:
					rain_dry = gu.get_rain_status()
				if rained:
					start_watering()
					# Create timer to expire after the duration of the watering event
					threading.Timer( interval=watering_time.duration.seconds, function=stop_watering ).start()
				else:
					print( 'Skipping this watering event, it rained recently' )
				
				# Schedule watering event for same time tomorrow if daily
				if watering_time.daily:
					dt = datetime.fromtimestamp( seconds )
					dt = dt + timedelta( days=1 )
					print( 'Scheduling next watering event for:', dt )
					watering_time.timestamp.seconds = int( dt.timestamp() )
					heapq.heappush( q_water, ( watering_time.timestamp.seconds, watering_time ) )

				write_water_sched_to_json()

			else:
				# Next watering event not yet expired, reinsert in queue
				heapq.heappush( q_water, ( seconds, watering_time ) )

	def check_pump():
		with d_lock:

			# Pump is running
			if gu.get_pump_status():

				# Pump should not be running if the well is empty or the tank is full
				if gu.get_well_empty_status() or gu.get_tank_full_status():

					# Shut off pump
					gu.set_pump_status( False )

			# Pump is not running
			else:

				# Pump should be running if the tank is empty and the well is not empty
				if gu.get_tank_empty_status() and not gu.get_well_empty_status:

					# Turn on the pump
					gu.set_pump_status( True )

	def get_device_updates ():
		container = tool_shed.container()

		# Add device uddates per the device map
		for dev in dev_map:
			dev_update = container.all_device_updates.updates.add()
			dev_update.device = dev
			with d_lock:
				dev_update.status = dev_map[dev][0]()

		if container:
			q_out.put( container )

	while True:
		try:
			# Execution beyond get_nowait() only occures if the q_out is non-empty
			container = q_in.get_nowait()
			#---------------------------------------------------------------------

			if container.HasField( 'get_device_updates' ):
				print( 'A device update has been requested' )
				get_device_updates()

			elif container.HasField( 'set_watering_time' ):
				print( 'A scheduled watering has been requested:' )
				print( container.set_watering_time )
				heapq.heappush( q_water, ( container.set_watering_time.timestamp.seconds, container.set_watering_time ) )
				write_water_sched_to_json()

			elif container.HasField( 'get_next_watering_time' ):
				# Check if any watering events are queued
				if q_water:
					# Get next queued event and fill container
					seconds, watering_time = heapq.heappop( q_water )
					heapq.heappush( q_water, ( seconds, watering_time ) )
					container = tool_shed.container()
					container.next_watering_time.CopyFrom( watering_time )
					q_out.put( container )

			elif container.HasField( 'get_watering_times' ):
				# Check if any watering events are queued
				if q_water:
					container = tool_shed.container()

					# Find all queued watering events:
					for water in q_water:
						time = container.all_watering_times.times.add()
						time.CopyFrom( water[1] )

					q_out.put( container )

			elif container.HasField( 'water_now' ):
				start_watering()
				# Create timer to expire after the duration of the watering event
				threading.Timer( interval=container.water_now.duration.seconds, function=stop_watering ).start()

			elif container.HasField( 'stop_watering' ):
				stop_watering()

			elif container.HasField( 'cancel_watering_time' ):
				# Check if any watering events are queued
				if q_water:
					# Get time of day we are cancelling
					dt_cancel = datetime.fromtimestamp( container.cancel_watering_time.timestamp.seconds )

					# Create new version of queue
					q_water_new = []
					
					# Copy over non-cancelled watering times
					for seconds, watering_time in q_water:
						dt = datetime.fromtimestamp( seconds )
						if dt.hour == dt_cancel.hour and dt.minute == dt_cancel.minute:
							print( 'Cancelling', watering_time )
						else:
							heapq.heappush( q_water_new, ( seconds, watering_time ) )

					# Copy over to old queue
					q_water = q_water_new.copy()

					# Write changes to watering schedule
					write_water_sched_to_json()

			elif container.HasField( 'pump_now' ):
				start_pumping()
				# Create timer to expire after the duration of the pumping event
				threading.Timer( interval=container.pump_now.duration.seconds, function=stop_pumping ).start()

			elif container.HasField( 'stop_pumping' ):
				stop_pumping()

			else:
				print( 'An unsupported message has been received' )

		except queue.Empty:
			pass

		###########################################
		# DO ALL OUR GENERAL GARDENING TASKS HERE #
		###########################################
		# Check if a watering event has expired
		check_watering()
		# Run pump
		check_pump()
		###########################################
		#             END OF GARDENING            #
		###########################################

# Turn on the gardener thread
gardener_thread = threading.Thread( target=gardener, daemon=True )
gardener_thread.start()
###############################################################################

# Set up socket and locks
s_lock = threading.Lock()
p_lock = threading.Lock()
pulse = True

with socket.socket( socket.AF_INET, socket.SOCK_STREAM ) as s:
	s.bind( ( HOST, PORT ) )
	print( 'Socket is bound to:' )
	print( s.getsockname() )
	s.listen( 1 )
	print( 'Socket is listening' )
	conn, addr = s.accept()
	print( 'Socket accepted connection' )
	print( 'Connected by', addr )
	
	# Make socket non-blocking so the sender thread can still pick up the lock
	conn.setblocking( 0 )

	##############################################################
	# Thread that handles sending responses
	def sender():
		print( 'Sender thread is running' )
		global pulse
		stop = True
		with p_lock:
			stop = not pulse

		# Only run sender thread while the client is alive
		while not stop:
			try:
				# Execution beyond get_nowait() only occures if the q_out is non-empty
				container = q_out.get_nowait()
				#---------------------------------------------------------------------

				# Serialize the data and send it over to the client
				data = container.SerializeToString()
				with s_lock:
					conn.sendall( data )
					print( 'Sent update!' )

			except queue.Empty:
				pass

			# Update the status of the pulse
			with p_lock:
				stop = not pulse

	# Turn on the sender thread
	sender_thread = threading.Thread( target=sender, daemon=True )
	sender_thread.start()
	##############################################################

	###########################################################################
	# Timer thread that signals shutting down connection when no pulse detected
	def no_pulse ():
		global pulse
		print( 'Lost the client\'s pulse' )
		with p_lock:
			pulse = False

	# Turn on pulse monitor timer, 5 second interval
	pulse_timer = threading.Timer( interval=5, function=no_pulse )
	pulse_timer.start()
	###########################################################################

	# Main thread loop, receives messages from client and dispatches to the gardener
	while True:
		with s_lock:
			try:
				# Execution beyond conn.recv() only occurs if it reads successfully
				data = conn.recv( 1024 )
				# -----------------------------------------------------------------
				
				# Only process data if meaningful non-empty
				if data:
					# Set the pulse to True
					with p_lock:
						pulse = True

					# Restart the 5 second pulse monitor
					pulse_timer.cancel()
					pulse_timer = threading.Timer( interval=5, function=no_pulse )
					pulse_timer.start()

					try:
						# Parse received message
						container = tool_shed.container()
						container.ParseFromString( data )
						# If a heartbeat message ignore
						if container.HasField( 'heartbeat' ):
							if not MUTE_HEARTBEAT:
								print( 'Heartbeat!' )
						# Else, let the gardener thread handle it
						else:
							q_in.put( container )

					except DecodeError:
						print( 'Was not able to parse message!' )

			except BlockingIOError:
				pass
			
		# Check if pulse monitor reported no pulse
		# If no pulse then we join the sender thread,
		# shutdown the connection, and go back to
		# listening for a connection
		p_lock.acquire()

		if not pulse:
			print( 'Pulse lost! Shutdown connection...' )

			# Join sender thread, release the p_lock
			# so we don't block the sender_thread
			p_lock.release()
			sender_thread.join()
			pulse_timer.cancel()
			p_lock.acquire()

			# Shutdown and close connection, we
			# don't have to use s_lock because
			# we already joined sender_thread
			conn.close()

			# Let user know where to connect to
			print( 'Socket is still bound to:' )
			print( s.getsockname() )

			# Listen for new connection
			s.listen( 1 )
			print( 'Socket is listening' )
			conn, addr = s.accept()
			print( 'Socket accepted connection' )
			print( 'Connected by', addr )

			# Make socket non-blocking so the sender thread can still pick up the lock
			conn.setblocking( 0 )

			# Restart the sender thread
			sender_thread = threading.Thread( target=sender, daemon=True )
			sender_thread.start()

			# Restart the pulse monitor timer, 5 second interval
			pulse = True
			pulse_timer = threading.Timer( interval=5, function=no_pulse )
			pulse_timer.start()

		p_lock.release()
