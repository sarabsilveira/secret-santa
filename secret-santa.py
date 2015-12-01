# coding=utf-8
__author__ = 'sslr'

from random import randint
import itertools
import os.path
import sys
import re

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


def save_draw(filename, assigned_friends):
	filepath, file_extension = os.path.splitext(filename)
	f = open(filepath + '.draw','w')
	f.write(str(assigned_friends) + '\n')
	f.close()

def randomise(people):

	assigned_friends = dict()
	restart = True

	print 'Finding friends...'

	while restart:

		restart = False

		for family, members in people.iteritems():
			other_people = get_others(people, family)

		
			for person in members:

				merged = list(set(itertools.chain(*people.values())) - set(assigned_friends.values()))

				restart_message = ''

				if merged == [person]:
					restart_message = '\''+person.name+'\' is the only one left'

				if set(merged) <= set(members):
					restart_message = 'there are only family members of \''+person.name+'\' left (\''+str(members)+'\')'

				if restart_message:
					print 'Restarting because ' + restart_message + ' ...'
					restart = True
					break 

				secret_friend = get_friend(person, other_people, assigned_friends.values())
				assigned_friends[person] = secret_friend

			if restart:
				break


	return assigned_friends

def get_friend(me, possible_friends, assigned_friends):

	friend = None
	assigned = False
	prev_assigned = possible_friends

	while not assigned:
		index = randint(0, len(possible_friends)-1)
		friend = possible_friends[index]

		if not assigned_friends:
			assigned = True
		else:
			assigned = not friend in assigned_friends and (friend != me)

	return friend

def get_others(others, not_family):

	other_people = []

	for key, value in others.iteritems():
		if key != not_family:
			other_people.extend(value)

	return other_people


def read_draw_file(filename):
	return eval(open(filename).read())


def read_file(filename):

	people = dict()

	try:
		current_file = open(filename, 'r')
		file_text = current_file.read()

		split = file_text.split("\n")

		for string in split:
			if string:
				split = string.split('=')
				family_name = split[0]
				names = split[1].split(';')
				full_names = split[2].split(';')
				emails = split[3].split(';')
				people.setdefault(family_name, [])
				members = []

				for name, full_name, email in zip(names, full_names, emails):
					person = Person(family_name, name, full_name, email)
					members.append(person)
				
				people[family_name] = members

	except Exception:
		print 'Error reading the file containing the people. Exiting...' 
		exit()

	return people

def email_credentials():
	try:
		current_file = open('credentials', 'r')
		file_text = current_file.read()
		return file_text.split("\n")
	except Exception:
		print 'Error reading the credentials file. Exiting...' 
		exit()


def send_emails(assigned_friends):

	credentials = email_credentials()
	server = connect_to_server(credentials)
	print 'Sending emails...'

	for person, friend in assigned_friends.iteritems():
		send_email(server, credentials[0], person.email, person.full_name, friend.full_name)

	server.quit()

def send_email(server, from_addr, my_email, my_name, friend_name):
	print '\tSending email to ' + my_name + ' (' + my_email + ')'
	try:
		header  = 'From: ' + from_addr + '\n'
		header += 'Subject: ' + my_name + ', your secret santa friend is...\n\n'
		message = header + '\n' + friend_name
		problems = server.sendmail(from_addr, my_email, message)

		if problems:
			print 'Problem while sending to ' + my_name
	except Exception, e:
		print '\tAn exception occurred while sending email to ' + my_name + ' (' + my_email + ').'
		print str(e)

def connect_to_server(credentials):
	import smtplib
	smtpserver = 'smtp.gmail.com:587'
	
	login = credentials[0]
	password = credentials[1]
	
	server = smtplib.SMTP(smtpserver)
	server.starttls()
	server.login(login,password)

	return server

# ------------------------- Running functions ---------------------------------

def run_draw(filename, send_email):
	people = read_file(filename)
	assigned_friends = randomise(people)
	save_draw(filename, assigned_friends)

	if send_email:
		send_emails(assigned_friends)

	print 'Draw finished!'

def resend_email(filename, person_name, new_email):
	draw = read_draw_file(filename)

	credentials = email_credentials()
	server = connect_to_server(credentials)

	for me in draw:
		if me == person_name:
			friend = draw[me]
			print 'Resending email...'
			send_email(server, credentials[0], new_email, me, friend)
			break

	server.quit()

	print 'Finished resending email to ' + person_name

def exit():
	print 'Usage: secret_santa.py -f <filename> [-e] [-r "<full name>" <email>]'
	print '\t-f <filename> - sets the filename that contains the peoples names involved in the draw'
	print '\t-e - sends an email to each person after the draw'
	print '\t-r "<full name>" <email> - resends the email to the person requesting it'
	sys.exit()

class Person(object):

	def __init__(self, family, name, full_name, email):
		self.family = family
		self.name = name
		self.email = email
		self.full_name = full_name

	def __str__(self):
		return self.full_name

	def __repr__(self):
		return "'" + self.full_name + "'"

if __name__ == '__main__':

	if len(sys.argv) == 3 and (sys.argv[1] != '-f' or not sys.argv[2]):
			exit()
	elif len(sys.argv) == 4 and (sys.argv[1] != '-f' or (sys.argv[3] != '-e' and sys.argv[3] != '-r')):
		exit()
	elif len(sys.argv) == 6 and (sys.argv[3] == '-r' and EMAIL_REGEX.match(sys.argv[5])):
		resend_email(sys.argv[2], sys.argv[4], sys.argv[5])
		sys.exit()
	elif len(sys.argv) > 6 or len(sys.argv) < 3:
		exit()

	run_draw(sys.argv[2], sys.argv[3] == '-e' if len(sys.argv) == 4 else False)
