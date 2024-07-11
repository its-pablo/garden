#!/usr/bin/python3

# Imports
import threading
import queue
import multiprocessing as mp
import heapq
import socket
import json
import time
import sys
import os
from pathlib import Path
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import Parse
from google.protobuf.message import DecodeError
import garden_pb2 as tool_shed
import garden_utils as gu
from datetime import timedelta
from datetime import datetime

# Important constant
VERSION = '0.7'
HOST = 'localhost'
PORT = 50007
WATERING_SCHEDULE_FILE_NAME = Path(__file__).resolve().parent / 'watering.json'
EVENT_LOG_FILE_NAME = Path(__file__).resolve().parent / 'event_log.txt'
MUTE_HEARTBEAT = True
ENABLE_TIMING = False

###############################################################################
# Thread that handles the gardening and requests
def gardener( q_in, q_out, kill, ws_file_name, el_file_name ):
	# Keep track of origin of current watering event
	watering_timestamp = 0

	# Keep track of origin of current pumping event
	pumping_timestamp = 0

	# Create watering queue
	q_water = []

	# Create device lock, used to synchronize with watering timer threads
	d_lock = threading.RLock()

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

	def write_water_sched_to_json ():
		# Check if any watering events are queued
		if q_water:
			# Find all queued watering events:
			container = tool_shed.container()
			for water in q_water:
				time = container.all_watering_times.times.add()
				time.CopyFrom( water[1] )
			save_message_to_json( container, ws_file_name )

	def log_event ( event ):
		with open( el_file_name, 'a', encoding='utf-8' ) as file:
			dt = datetime.today()
			log = str( dt ) + ': ' + str( event ) + '\n'
			file.write( log )

	def tail( f, lines=1, _buffer=4098 ):
		"""Tail a file and get X lines from the end"""
		# place holder for the lines found
		lines_found = []
		
		# block counter will be multiplied by buffer
		# to get the block size from the end
		block_counter = -1
		
		# loop until we find X lines
		while len( lines_found ) < lines:
			try:
				f.seek( block_counter * _buffer, os.SEEK_END )
			except IOError:  # either file is too small, or too many lines requested
				f.seek( 0 )
				lines_found = f.readlines()
				break
				
			lines_found = f.readlines()
			
			# decrement the block counter to get the
			# next X bytes
			block_counter -= 1
			
		return lines_found[ -lines: ]

	def peak_event_log ( num_lines ):
		logs = ''
		with open( el_file_name, 'a+', encoding='utf-8' ) as file:
			lines = tail( file, num_lines )
			logs = ''.join( lines )
		container = tool_shed.container()
		container.logs = logs
		q_out.put( container )

	def is_date_conflict ( dt_to_check, dt_base, td_base_period ):
		td_0 = timedelta( 0 )
		# Not conflicting if datetime to check happens before base datetime
		if dt_to_check < dt_base:
			return False

		# Same datetime so obviously conflict
		elif dt_to_check == dt_base:
			return True

		# Might still have conflict if periodic multiple
		elif ( dt_to_check - dt_base ) % td_base_period == td_0:
			return True

		# No conflict
		else:
			return False

	# Check to see if the watering schedule file exists
	if os.path.isfile( ws_file_name ):
		print( 'Watering schedule exists! Importing and updating.' )

		with open( ws_file_name, 'r', encoding='utf-8' ) as file:
			json_message = file.read()
			container = tool_shed.container()
			container = Parse( json_message, container )
			dt_now = datetime.today()

			for watering_time in container.all_watering_times.times:
				
				# Not expired put in q_water as is
				if watering_time.timestamp.seconds > int( dt_now.timestamp() ):
					heapq.heappush( q_water, ( watering_time.timestamp.seconds, watering_time ) )
				
				# Expired but periodic
				elif watering_time.period.seconds > 0:
					dt = datetime.fromtimestamp( watering_time.timestamp.seconds )
					td_period = timedelta( seconds=watering_time.period.seconds )
					td = dt_now - dt
					num_periods = td // td_period
					num_periods = num_periods + 1
					dt = dt + ( td_period * num_periods )
					watering_time.timestamp.seconds = int( dt.timestamp() )
					heapq.heappush( q_water, ( watering_time.timestamp.seconds, watering_time ) )

		# Save changes
		write_water_sched_to_json()

	def stop_watering ():
		with d_lock:
			if not gu.get_valve_status():
				print( 'Watering valve already closed!' )
				return False
			status = gu.set_valve_status( False )
			if status == False:
				print( 'Stopped watering successfully!' )
				log_event( 'STOPPED WATERING' )
			else:
				print( 'Failed to stop watering!' )
			return status

	# Special version used by the stop timer so that we don't stop the wrong watering event
	def stop_watering_guarded ( timestamp ):
		if not kill.is_set():
			with d_lock:
				if watering_timestamp == timestamp:
					stop_watering()

	# DO NOT USE DIRECTLY! Use start_watering_guarded or start_watering_guarded_now
	def start_watering ():
		with d_lock:
			if gu.get_valve_status():
				print( 'Watering valve already open!' )
				return False
			if gu.get_tank_empty_status():
				print( 'Cannot start watering, tanks empty' )
				return False
			if not gu.get_rain_status():
				print( 'Cannot start watering, it has rained' )
				return False
			status = gu.set_valve_status( True )
			if status == True:
				print( 'Started watering successfully!' )
				log_event( 'STARTED WATERING' )
			else:
				print( 'Failed to start watering!' )
			return status

	# Special version used to start watering when we expect to be stopped by a stop timer
	def start_watering_guarded ( timestamp ):
		nonlocal watering_timestamp
		with d_lock:
			watering_timestamp = timestamp
			start_watering()

	# Special version used to start watering when we do not expect to be stopped by a stop timer
	def start_watering_guarded_now ():
		dt = datetime.today()
		start_watering_guarded( int( dt.timestamp() ) )

	def stop_pumping ():
		with d_lock:
			if not gu.get_pump_status():
				print( 'Pump already stopped!' )
				return False
			status = gu.set_pump_status( False )
			if status == False:
				print( 'Stopped pumping successfully!' )
				log_event( 'STOPPED PUMPING' )
			else:
				print( 'Failed to stop pumping!' )
			return status
	
	# Special version used by the stop timer so that we don't stop the wrong pumping event
	def stop_pumping_guarded ( timestamp ):
		if not kill.is_set():
			with d_lock:
				if pumping_timestamp == timestamp:
					stop_pumping()

	def start_pumping ():
		with d_lock:
			if gu.get_pump_status():
				print( 'Pump already running!' )
				return False
			if gu.get_well_empty_status() or gu.get_tank_full_status():
				print( 'Cannot start pumping, well empty or tanks full' )
				return False
			status = gu.set_pump_status( True )
			if status == True:
				print( 'Started pumping successfully!' )
				log_event( 'STARTED PUMPING' )
			else:
				print( 'Failed to start pumping!' )
			return status

	# Special version used to start pumping when we expect to be stopped by a stop timer
	def start_pumping_guarded ( timestamp ):
		nonlocal pumping_timestamp
		with d_lock:
			pumping_timestamp = timestamp
			start_pumping()

	# Special version used to start pumping when we do not expect to be stopped by a stop timer
	def start_pumping_guarded_now ():
		dt = datetime.today()
		start_pumping_guarded( int( dt.timestamp() ) )

	def check_watering_schedule ():
		# Check if any watering events queued
		if q_water:
			# Get next watering event from heap queue
			seconds, watering_time = heapq.heappop( q_water )
			
			# Check if event has expired
			dt = datetime.today()
			if seconds < int( dt.timestamp() ):
				rain_dry = True
				tank_empty = False
				with d_lock:
					rain_dry = gu.get_rain_status()
					tank_empty = gu.get_tank_empty_status()
				if rain_dry and not tank_empty:
					start_watering_guarded( seconds )
					# Create timer to expire after the duration of the watering event
					threading.Timer( interval=watering_time.duration.seconds, function=stop_watering_guarded, args=[ seconds ] ).start()
				
				# Reschedule watering event if periodic
				if watering_time.period.seconds > 0:
					dt = datetime.fromtimestamp( seconds )
					dt = dt + timedelta( seconds=watering_time.period.seconds )
					watering_time.timestamp.seconds = int( dt.timestamp() )
					heapq.heappush( q_water, ( watering_time.timestamp.seconds, watering_time ) )

				write_water_sched_to_json()

			else:
				# Next watering event not yet expired, reinsert in queue
				heapq.heappush( q_water, ( seconds, watering_time ) )

	def check_pump ():
		with d_lock:

			# Pump is running
			if gu.get_pump_status():

				# Pump should not be running if the well is empty or the tank is full
				if gu.get_well_empty_status() or gu.get_tank_full_status():

					# Shut off pump
					stop_pumping()

			# Pump is not running
			else:

				# Pump should be running if the tank is empty and the well is not empty
				if gu.get_tank_empty_status() and not gu.get_well_empty_status():

					# Turn on the pump
					start_pumping()

	def check_valve ():
		with d_lock:

			# Valve is open for watering
			if gu.get_valve_status():

				# Valve should not be open for watering if tanks are empty or it has rained
				if gu.get_tank_empty_status() or not gu.get_rain_status():

					# Close valve
					stop_watering()

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

	print( 'Gardener process is running' )
	# Print process ID in case it gets hung
	print( 'PID:', os.getpid() )

	while True:
		if kill.is_set():
			break

		try:
			# Execution beyond get_nowait() only occures if the q_in is non-empty
			container = q_in.get_nowait()
			#---------------------------------------------------------------------

			if container.HasField( 'get_device_updates' ):
				get_device_updates()

			elif container.HasField( 'set_watering_time' ):
				dt = datetime.today()
				if int( dt.timestamp() ) <= container.set_watering_time.timestamp.seconds:
					conflict = False
					for seconds, watering_time in q_water:
						if is_date_conflict( datetime.fromtimestamp( container.set_watering_time.timestamp.seconds ), datetime.fromtimestamp( seconds ), timedelta( seconds=watering_time.period.seconds ) ):
							conflict = True
							break

					if not conflict:
						heapq.heappush( q_water, ( container.set_watering_time.timestamp.seconds, container.set_watering_time ) )
						write_water_sched_to_json()

			elif container.HasField( 'get_next_watering_time' ):
				container = tool_shed.container()

				# Check if any watering events are queued
				if q_water:
					# Get next queued event and fill container
					seconds, watering_time = heapq.heappop( q_water )
					heapq.heappush( q_water, ( seconds, watering_time ) )
					container.next_watering_time.CopyFrom( watering_time )

				else:
					container.no_watering_times = 1

				q_out.put( container )

			elif container.HasField( 'get_watering_times' ):
				container = tool_shed.container()

				# Check if any watering events are queued
				if q_water:

					# Find all queued watering events:
					for water in q_water:
						time = container.all_watering_times.times.add()
						time.CopyFrom( water[1] )

				else:
					container.no_watering_times = 1

				q_out.put( container )

			elif container.HasField( 'water_now' ):
				duration = container.water_now.duration.seconds
				if duration:
					dt = datetime.today()
					ts = int( dt.timestamp() )
					start_watering_guarded( ts )
					# Create timer to expire after the duration of the watering event
					threading.Timer( interval=duration, function=stop_watering_guarded, args=[ ts ] ).start()
				else:
					start_watering_guarded_now()

			elif container.HasField( 'stop_watering' ):
				stop_watering()

			elif container.HasField( 'cancel_watering_time' ):
				# Check if any watering events are queued
				if q_water:
					# Get time of day we are cancelling
					dt_cancel = datetime.fromtimestamp( container.cancel_watering_time.timestamp.seconds )

					# Create new version of queue
					q_water_new = []

					# Handle non-periodic, exact timestamp match
					if container.cancel_watering_time.period.seconds == 0:
						# Copy over non-cancelled watering times
						for seconds, watering_time in q_water:
							dt = datetime.fromtimestamp( seconds )
							if dt != dt_cancel:
								heapq.heappush( q_water_new, ( seconds, watering_time ) )

					# Handle periodic, exact time of day match spanned over all watering time periods
					else:
						# Copy over non-cancelled watering times
						for seconds, watering_time in q_water:
							dt = datetime.fromtimestamp( seconds )
							if not is_date_conflict( dt_cancel, dt, timedelta( seconds=watering_time.period.seconds ) ):
								heapq.heappush( q_water_new, ( seconds, watering_time ) )

					# Copy over to old queue
					q_water = q_water_new.copy()

					# Write changes to watering schedule
					write_water_sched_to_json()

			elif container.HasField( 'pump_now' ):
				duration = interval=container.pump_now.duration.seconds
				if duration:
					dt = datetime.today()
					ts = int( dt.timestamp() )
					start_pumping_guarded( ts )
					# Create timer to expire after the duration of the pumping event
					threading.Timer( interval=duration, function=stop_pumping_guarded, args=[ ts ] ).start()
				else:
					start_pumping_guarded_now()

			elif container.HasField( 'stop_pumping' ):
				stop_pumping()

			elif container.HasField( 'peak_event_log' ):
				peak_event_log( container.peak_event_log )

			# Secret option
			elif container.HasField( 'sensor_override' ):
				with d_lock:
					sns_dict = {
						tool_shed.container.devices.DEV_SNS_TANK_FULL: gu.SNS_TANK_FULL,
						tool_shed.container.devices.DEV_SNS_TANK_EMPTY: gu.SNS_TANK_EMPTY,
						tool_shed.container.devices.DEV_SNS_WELL_EMPTY: gu.SNS_WELL_EMPTY,
						tool_shed.container.devices.DEV_SNS_RAIN: gu.SNS_RAIN
					}
					sns_dict[ container.sensor_override.device ].is_active = container.sensor_override.status

			else:
				print( 'An unsupported message has been received' )

		except queue.Empty:
			pass

		###########################################
		# DO ALL OUR GENERAL GARDENING TASKS HERE #
		###########################################
		# Check if a watering event has expired
		check_watering_schedule()
		# Run pump
		check_pump()
		# Run valve
		check_valve()
		###########################################
		#             END OF GARDENING            #
		###########################################

if __name__ == '__main__':
	def print_argv_options ():
		print( 'Options are:' )
		print( '\t--help' )
		print( '\t--host [-h] HOST' )
		print( '\t--port [-p] PORT, PORT must be a non-negative integer' )
		print( '\t--schedule_file [-sf] FILE_NAME' )
		print( '\t--log_file [-lf] FILE_NAME' )
	# Check arguments
	if len( sys.argv ) == 2 and sys.argv[1] == '--help':
		print_argv_options()
		sys.exit( 0 )
	elif len( sys.argv ) % 2 != 1:
		print( 'Bad arguments' )
		print_argv_options()
		sys.exit( 0 )
	elif len( sys.argv ) > 1:
		for i in range( ( len( sys.argv ) - 1 ) // 2 ):
			arg_opt = sys.argv[ i + 1 ]
			arg_val = sys.argv[ i + 2 ]
			if arg_opt == '--host' or arg_opt == '-h':
				HOST = arg_val
			elif arg_opt == '--port' or arg_opt == '-p':
				try:
					PORT = int( arg_val )
					if PORT < 0:
						print( 'Negative integer PORT' )
				except ValueError:
					print( 'Non integer PORT' )
			elif arg_opt == '--schedule_file' or arg_opt == '-sf':
				WATERING_SCHEDULE_FILE_NAME = arg_val
			elif arg_opt == '--log_file' or arg_opt == '-lf':
				EVENT_LOG_FILE_NAME = arg_val
			else:
				print( 'Unrecognized argument:', arg_opt, arg_val )
				print_argv_options()
				sys.exit( 0 )

	# Check to see if we have write access to the watering schedule
	if os.path.isfile( WATERING_SCHEDULE_FILE_NAME ) and ( not os.access( WATERING_SCHEDULE_FILE_NAME, os.R_OK ) or not os.access( WATERING_SCHEDULE_FILE_NAME, os.W_OK ) ):
		print( 'Do not have read/write access to', WATERING_SCHEDULE_FILE_NAME )
		sys.exit( 0 )

	# Check to see if we have write access to the event log
	if os.path.isfile( EVENT_LOG_FILE_NAME ) and ( not os.access( EVENT_LOG_FILE_NAME, os.R_OK ) or not os.access( EVENT_LOG_FILE_NAME, os.W_OK ) ):
		print( 'Do not have read/write access to', EVENT_LOG_FILE_NAME )
		sys.exit( 0 )

	# Print info
	print( 'Starting garden_daemon with the following args:' )
	print( '\tHOST:', HOST )
	print( '\tPORT:', PORT )
	print( '\tWATERING_SCHEDULE_FILE_NAME:', WATERING_SCHEDULE_FILE_NAME )
	print( '\tEVENT_LOG_FILE_NAME:', EVENT_LOG_FILE_NAME )

	# Set up process safe queues
	q_in = mp.Queue() # This queue is going to hold the incoming messages from the client
	q_out = mp.Queue() # This queue is going to hold the outgoing messages to the client
	# Note: "messages" in this context efers to the protobuf messages defined in garden.proto

	# Set up event for terminating threads
	kill = mp.Event()

	# Set connection threading
	s_lock = threading.Lock()
	no_pulse = threading.Event()
	lost_conn = threading.Event()

	with socket.socket( socket.AF_INET, socket.SOCK_STREAM ) as s:
		# Print version
		print( 'garden_daemon verion', VERSION, 'is now running!' )
		# Print process ID in case it gets hung
		print( 'PID:', os.getpid() )

		print( 'Attempting to bind socket' )
		while True:
			try:
				s.bind( ( HOST, PORT ) )
				break
			except OSError:
				continue
			except socket.gaierror as e:
				print( str( e ) )
				print( 'Aborting garden_daemon' )
				sys.exit( 0 )
		print( 'Socket is bound to:' )
		print( s.getsockname() )

		# Turn on the gardener process
		gardener_process = mp.Process( target=gardener, daemon=True, args=( q_in, q_out, kill, WATERING_SCHEDULE_FILE_NAME, EVENT_LOG_FILE_NAME ), name='gardener_process' )
		gardener_process.start()

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

			# Only run sender thread while the client is alive
			while True:
				if no_pulse.is_set() or kill.is_set() or lost_conn.is_set():
					break

				try:
					# Execution beyond get_nowait() only occures if the q_out is non-empty
					container = q_out.get_nowait()
					#---------------------------------------------------------------------

					# Serialize the data and send it over to the client
					data = container.SerializeToString()
					with s_lock:
						try:
							conn.sendall( data )

						except ConnectionAbortedError:
							lost_conn.set()

						except ConnectionResetError:
							lost_conn.set()

				except queue.Empty:
					pass

		# Turn on the sender thread
		sender_thread = threading.Thread( target=sender, daemon=True )
		sender_thread.start()
		##############################################################

		###########################################################################
		# Timer thread that signals shutting down connection when no pulse detected
		def pulse_mon ():
			if not kill.is_set():
				print( 'Lost the client\'s pulse' )
				no_pulse.set()

		# Turn on pulse monitor timer, 5 second interval
		pulse_timer = threading.Timer( interval=5, function=pulse_mon )
		pulse_timer.start()
		###########################################################################

		# Main thread loop, receives messages from client and dispatches to the gardener
		if ENABLE_TIMING:
			t1 = time.time()
			dt_max = 0.0
		while True:
			# Timing section, useful to perform analysis on how many requests per seconds we can accomodate
			# right now can accomate about 4 to 5 requests per second in the worst case
			if ENABLE_TIMING:
				t0 = t1
				t1 = time.time()
				print( t1 - t0 )
				if t1 - t0 > dt_max:
					print( 'NEW MAX DT' )
					dt_max = t1 - t0

			# Shutdown
			if kill.is_set():
				print( 'Shutting down garden_daemon!' )
				# Join all threads
				gardener_process.join()
				sender_thread.join()
				pulse_timer.cancel()

				# Close connection and socket
				conn.close()

				# Print max timing delta if enabled
				if ENABLE_TIMING: print( dt_max )

				# Break out of main loop
				break

			# Check if pulse monitor reported no pulse
			# If no pulse then we join the sender thread,
			# shutdown the connection, and go back to
			# listening for a connection
			if no_pulse.is_set() or lost_conn.is_set():
				print( 'Pulse or connection lost! Shutdown connection...' )

				# Join sender thread
				sender_thread.join()
				pulse_timer.cancel()

				# Reset queues
				def empty_queue ( q ):
					while not q.empty():
						try:
							q.get_nowait()
						except queue.Empty:
							break

				empty_queue( q_in )
				empty_queue( q_out )

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

				# Clear events
				lost_conn.clear()
				no_pulse.clear()

				# Restart the sender thread
				sender_thread = threading.Thread( target=sender, daemon=True )
				sender_thread.start()

				# Restart the pulse monitor timer, 5 second interval
				pulse_timer = threading.Timer( interval=5, function=pulse_mon )
				pulse_timer.start()

				# If timing reset time
				if ENABLE_TIMING: t1 = time.time()

			# Normal execution, try to read messages and dispatch them
			with s_lock:
				try:
					# Execution beyond conn.recv() only occurs if it reads successfully
					data = conn.recv( 1024 )
					# -----------------------------------------------------------------
					
					# Only process data if meaningful non-empty
					if data:
						# Clear no pulse signal since we have pulse
						no_pulse.clear()

						# Restart the 5 second pulse monitor
						pulse_timer.cancel()
						pulse_timer = threading.Timer( interval=5, function=pulse_mon )
						pulse_timer.start()

						try:
							# Parse received message
							container = tool_shed.container()
							container.ParseFromString( data )
							# If a heartbeat message ignore
							if container.HasField( 'heartbeat' ):
								if not MUTE_HEARTBEAT:
									print( 'Heartbeat!' )
							# If a shutdown message, send kill signal
							elif container.HasField( 'shutdown' ):
								print( 'Killing' )
								kill.set()
							# Else, let the gardener thread handle it
							else:
								q_in.put( container )

						except DecodeError:
							print( 'Was not able to parse message!' )

				except BlockingIOError:
					pass

				except ConnectionAbortedError:
					lost_conn.set()

				except ConnectionResetError:
					lost_conn.set()
