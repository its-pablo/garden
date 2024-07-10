#!/usr/bin/python3

print( 'garden_daemon is now running!' )

# Imports
import threading
import queue
import heapq
import socket
import json
from os import path
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import Parse
import garden_pb2 as tool_shed
from datetime import timedelta
from datetime import datetime

# Important constant
VERSION = '0.2'
HOST = 'localhost'
PORT = 50007
WATERING_SCHEDULE_FILE_NAME = 'watering.json'

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

	def handle_request( update_rqst ):
		print( '\tDEVICE:', update_rqst )
		container = tool_shed.container()
		container.update.device = update_rqst.device

		if update_rqst.device == tool_shed.container.devices.DEV_ACT_PUMP:
			container.update.status = tool_shed.container.device_status.STAT_ACT_ON

		elif update_rqst.device == tool_shed.container.devices.DEV_ACT_VALVE:
			container.update.status = tool_shed.container.device_status.STAT_ACT_OFF

		elif update_rqst.device == tool_shed.container.devices.DEV_SNS_WATER_LVL_HIGH:
			container.update.status = tool_shed.container.device_status.STAT_SNS_ACTIVE

		elif update_rqst.device == tool_shed.container.devices.DEV_SNS_WATER_LVL_LOW:
			container.update.status = tool_shed.container.device_status.STAT_SNS_INACTIVE

		else:
			print( '\tUNKNOWN' )
			container = None

		if container:
			q_out.put( container )

	def check_watering ():
		# Check if any watering events queued
		if q_water:
			# Get next watering event from heap queue
			seconds, watering_time = heapq.heappop( q_water )
			# Check if event has expired
			dt = datetime.today()
			if seconds < int( dt.timestamp() ):
				print( 'Watering event expired! Now watering.' )
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

	while True:
		try:
			# Execution beyond get_nowait() only occures if the q_out is non-empty
			container = q_in.get_nowait()
			#---------------------------------------------------------------------

			if container.HasField( 'update_rqst' ):
				print( 'A device update has been requested:' )
				handle_request( container.update_rqst )

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
					# Find all queued watering events:
					container = tool_shed.container()
					for water in q_water:
						time = container.all_watering_times.times.add()
						time.CopyFrom( water[1] )
					q_out.put( container )

			else:
				print( 'An unsupported message has been received' )

		except queue.Empty:
			pass

		###########################################
		# DO ALL OUR GENERAL GARDENING TASKS HERE #
		###########################################
		# Check if a watering event has expired
		check_watering()
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

					# Parse received message
					container = tool_shed.container()
					container.ParseFromString( data )
					# If a heartbeat message ignore
					if container.HasField( 'heartbeat' ):
						print( 'Heartbeat!' )
					# Else, let the gardener thread handle it
					else:
						q_in.put( container )
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
