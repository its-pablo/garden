#!/usr/bin/python3

print( 'remote_gardener is now running!' )

# Imports
import time
import threading
import queue
import socket
import garden_pb2 as tool_shed

# Set up thread safe queue
q_in = queue.Queue()
q_out = queue.Queue()

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
			with s_lock:
				try:
					data = s.recv( 1024 )
					if data:
						container = tool_shed.container()
						container.ParseFromString( data )
						#q_in.put( container )
						print( 'Received update:', container )
				except BlockingIOError:
					continue

	# Turn on the receiver thread
	receiver_thread = threading.Thread( target=receiver, daemon=True )
	receiver_thread.start()
	##################################################################

	##############################################################
	# Thread that handles sending queued messages
	def sender ():
		print( 'Sender thread is running' )

		while True:
			container = q_out.get()
			data = container.SerializeToString()
			with s_lock:
				s.sendall( data )

	# Turn on the sender thread
	sender_thread = threading.Thread( target=sender, daemon=True )
	sender_thread.start()
	##############################################################

	####################################################################
	# Thread that handles queueing the heartbeat
	def heartbeat ():
		print( 'Heartbeat thread is running' )

		while True:
			container = tool_shed.container()
			container.heartbeat = 1
			q_out.put( container )
			time.sleep( 1 )

	# Turn on the heartbeat thread
	heartbeat_thread = threading.Thread( target=heartbeat, daemon=True )
	heartbeat_thread.start()
	####################################################################

	# Main thread loop, reads commands and sends them to the sender_thread
	while True:
		container = tool_shed.container()
		print( 'Options:' )
		print( '\t0. WATER_LVL_HIGH sensor update' )
		print( '\t1. WATER_LVL_LOW sensor update' )
		print( '\t2. PUMP actuator update' )
		print( '\t3. VALVE actuator update' )
		print( '\tPress ENTER to exit.' )
		choice = input( 'Choice?\n' )
		if not choice:
			break
		try:
			choice = int( choice )
			if choice == 0:
				container.update_rqst.device = tool_shed.container.devices.DEV_SNS_WATER_LVL_HIGH
			elif choice == 1:
				container.update_rqst.device = tool_shed.container.devices.DEV_SNS_WATER_LVL_LOW
			elif choice == 2:
				container.update_rqst.device = tool_shed.container.devices.DEV_ACT_PUMP
			elif choice == 3:
				container.update_rqst.device = tool_shed.container.devices.DEV_ACT_VALVE
			else:
				container = None
		except ValueError:
			print( 'Not an integer choice! Try again.' )
			container = None

		if container:
			q_out.put( container )
