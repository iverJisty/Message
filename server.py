#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import select
import json
import argparse
from time import gmtime, strftime

def parse_cmd():
	parser =argparse.ArgumentParser()
	parser.add_argument('host', help='IP or Hostname')
	parser.add_argument('-p', metavar='port', type=int, default=22345, 
			help='TCP port (default 22345')
	args = parser.parse_args()
	address = (args.host, args.p)
	return address



class Server():
	def __init__(self, address):
		self.addr = address
		self.srv_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.srv_sock.bind(address)
		self.srv_sock.listen(50)
		self.mailbox = []
		self.registered_user = { 
			"ken" : "12345",
			"jane" : "23456",
			"john" : "zxcvb",
			"sandy" : "xcvbn"
		}
		self.current_users = []

	def identify_user(self,user,conn):
		pair = (user,conn)
		if pair in self.current_users:
			return True
		else:
			return False

	def find_user(self,user):
		for pair in self.current_users:
			if user in pair:
				return pair[1]	# reciver's fd
		return False
	
	def	user_valid(self,user):
		if user in self.registered_user:
			return True
		else:
			return False

if __name__ == '__main__':
	
	read = []
	write = []	# this will be empty(?
	exp = []	# this will be empty(?
	trace = []	# fd to trace
	clients = []
	addr = parse_cmd()
	print("{}".format(addr))
	serv = Server(addr)

	# add the sock to select
	trace.append(serv.srv_sock)
	
	# if s found in list => it can be read
	while 1:
		read , write, exp = select.select( trace,[],[],0)	# only add read list
		for s in read :
			#print("{}".format(s))
			if s is serv.srv_sock:   # when a client connect to server
				conn, client_addr = s.accept()
				trace.append(conn)	# add client to trace
				clients.append(conn)	
				print("Client {} connected".format(client_addr))
			else:
				receive_data = s.recv(4096)
				if receive_data == b'':
					print("Client {} disconnect".format(client_addr))
					trace.remove(s)
						
				else:
					mesg = json.loads(receive_data.decode('UTF-8'))
				
					if mesg['type'] == 'login':
						user = mesg['user']
						passwd = mesg['pass']
						if user in serv.registered_user and serv.registered_user[user] == passwd:
							send_msg = { "type":"login","from":"Server", "msg":"Login Success"}
							serv.current_users.append((user,conn))
							
						else :
							send_msg = { "type":"login","from":"Server" , "msg":"Login Failed" }
		
						s.send(json.dumps(send_msg).encode('UTF-8'))
					
					elif mesg['type'] == 'send':
						if serv.identify_user(mesg['user'],s):
							user = mesg['user']
							if serv.user_valid(mesg['sendto']) : #check user exist 
								print("{} exist".format(mesg['sendto']))	
								sendto = serv.find_user(mesg['sendto'])
							
								data = mesg['msg']
								send_msg = { "type":"send","from":user,"msg":data }
									
								if sendto == False:		# add timestamp if leave a message
									send_msg['time'] = strftime("%Y-%m-%d %H:%M:%S")
									serv.mailbox[msg['sendto']] = send_msg
								sendto.send( json.dumps(send_msg).encode('UTF-8') )
							else:
								send_msg = { "type":"error", "from":"Server", "msg":"User " + mesg['sendto']+" current not available" }
								s.send( json.dumps(send_msg).encode('UTF-8'))
					
					elif mesg['type'] == 'listuser':
						if serv.identify_user(mesg['user'],s):
							send_userlist = []
							for pair in serv.current_users:
								send_userlist.append(pair[0])
							
							send_msg = { "type":"listuser","from":"Server", "msg":send_userlist }
							s.send(json.dumps(send_msg).encode('UTF-8'))

					elif mesg['type'] == 'broadcast':
						if serv.identify_user(mesg['user'],s):
							send_msg = { "type":"broadcast", "from":mesg['user'], "msg":mesg['msg'] }
							encode_msg = json.dumps(send_msg).encode('UTF-8')

							for pair in serv.current_users:
								pair[1].send(encode_msg)

					elif mesg['type'] == 'logout':
						if serv.identify_user(mesg['user'],s):
							to_remove = (mesg['user'],s)
							send_msg = { "type":"logout","from":"Server","msg":"Logout Success" }
							s.send(json.dumps(send_msg).encode('UTF-8'))
							serv.current_users.remove(to_remove)

							
