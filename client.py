#!/usr/bin/env python3

import socket
import select
import sys
import getpass
import json
import argparse

def parse_cmd():
	parser =argparse.ArgumentParser()
	parser.add_argument('host', help='IP or Hostname')
	parser.add_argument('-p', metavar='port', type=int, default=22345, 
			help='Connect port (default 22345')
	args = parser.parse_args()
	address = (args.host, args.p)
	return address

class Client():
	
	def __init__(self,address):
		self.cli_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.cli_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		self.cli_sock.connect(address)
	
if __name__ == '__main__':

	
	trace = []
	read = []
	write = []
	excp = []
	addr = parse_cmd()
	client = Client(addr)
	


	user = input("Username : ")
	passwd = getpass.getpass("Password : ")
	send_packet = { "type":"login", "user":user , "pass":passwd }
	
	client.cli_sock.sendall(json.dumps(send_packet).encode('UTF-8'))

	trace.append(client.cli_sock)
	trace.append(sys.stdin)
	
	while True:
		read,write,excp = select.select( trace, [], [] ,0 )

		for s in read:
			print(">")
			if s is client.cli_sock:	# get message from server
				data = json.loads(s.recv(4096).decode('UTF-8'))
				if data['type'] == 'login' and data['from'] == 'Server':
					if data['msg'] == 'Login Success':
						print(data['msg'])
						login_success = True
						print("chat > ",end='')
					elif data['msg'] == 'Login Failed':
						print(data['msg'])
						login_success = False
						sys.exit()		# server will get empty message

				elif login_success == True:
					if data['type'] == 'listuser' and data['from'] == 'Server':
						user_list = data['msg']
						print("-----------")
						for u in user_list:
							print(u)
						print("-----------")	
					
					elif data['type'] == 'broadcast':
						print("Broadcast Message from {} --> ".format(data['from']),end='')
						print("\" {} \" ".format(data['msg']))

					elif data['type'] == 'send':
						print("Message from {} --> ".format(data['from']),end='')
						print("\" {} \" ".format(data['msg']))

					elif data['type'] == 'logout':
						if data['from'] == 'Server' and data['msg'] == 'Logout Success':
							sys.exit()		
							

			else:						# user input the command
				data = s.readline()
				parse_data = data.split("\n")[0].split(" ")
				
				send_msg = { "type" : parse_data[0], "user":user }
#print(parse_data)
				
				if send_msg['type'] == 'send':
					send_msg['sendto'] = parse_data[1]
					send_msg['msg'] = parse_data[2]
					client.cli_sock.send( json.dumps(send_msg).encode('UTF-8'))

				elif send_msg['type'] == 'listuser':	
					client.cli_sock.send( json.dumps(send_msg).encode('UTF-8'))
						
				elif send_msg['type'] == 'broadcast':
					send_msg['msg'] = parse_data[1]
					client.cli_sock.send( json.dumps(send_msg).encode('UTF-8'))
						
				elif send_msg['type'] == 'logout':
					client.cli_sock.send( json.dumps(send_msg).encode('UTF-8'))
				

