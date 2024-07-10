#!/usr/bin/python3

print( 'garden_daemon is now running!' )

# Imports
import threading
import queue
import socket
import garden_pb2 as tool_shed

# Set up thread safe queues
q_in = queue.Queue() # This queue is going to hold the incoming messages from the client
q_out = queue.Queue() # This queue is going to hold the outgoing messages to the client
# Note: "messages" in this context efers to the protobuf messages defined in garden.proto

###############################################################################
# Thread that handles the requests
def gardener():
	print( 'Gardener thread is running' )

	def handle_request( update_rqst ):
		print( '\tDEVICE:', update_rqst )
		container = tool_shed.container()
		container.update.device = update_rqst.device

		if update_rqst.device == tool_shed.container.devices.DEV_ACT_PUMP:
			container.update.status = tool_shed.container.device_status.STAT_ACT_ON
			q_out.put( container )

		elif update_rqst.device == tool_shed.container.devices.DEV_ACT_VALVE:
			container.update.status = tool_shed.container.device_status.STAT_ACT_OFF
			q_out.put( container )

		elif update_rqst.device == tool_shed.container.devices.DEV_SNS_WATER_LVL_HIGH:
			container.update.status = tool_shed.container.device_status.STAT_SNS_ACTIVE
			q_out.put( container )

		elif update_rqst.device == tool_shed.container.devices.DEV_SNS_WATER_LVL_LOW:
			container.update.status = tool_shed.container.device_status.STAT_SNS_INACTIVE
			q_out.put( container )

		else:
			print( '\tUNKNOWN' )

	while True:
		container = q_in.get()
		if container.HasField( 'update_rqst' ):
			print( 'A device update has been requested:' )
			handle_request( container.update_rqst )

		elif container.HasField( 'update' ):
			print( 'A device update has been received!' )

		else:
			print( 'An unsupported message has been received' )

# Turn on the gardener thread
gardener_thread = threading.Thread( target=gardener, daemon=True )
gardener_thread.start()
###############################################################################

# Set up socket and locks
s_lock = threading.Lock()
p_lock = threading.Lock()
pulse = True
HOST = 'localhost'
PORT = 50007
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
					print( 'Message received:', data )

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
			conn.shutdown( socket.SHUT_RDWR )
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
