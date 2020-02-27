#!/usr/bin/env python

"""
DOCSTRING


"""

import time
import datetime

import pyodbc

import pandas as pd
import backoff # this will help avoid Quote exceeded errors when making REST requests
import logging

import httplib2
import os
import sys

from apiclient import discovery
from apiclient.http import MediaFileUpload
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client import file 
from googleapiclient.errors import HttpError

try:
	import argparse
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

# If modifying these scopes, delete your previously saved credentials
SCOPES = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/spreadsheets'

def get_server_connection(server, database_name):
	'''
	Tries to connect to the SQL database. Attempts connection
	with driver SQL Server Native Client 10.0 and 11.0. Returns cursor.
	'''
	cnn = False
	try:
		# make connection to GIS database
		conn_info = 'DRIVER=SQL Server Native Client 10.0;' # ms sql server2008
		conn_info = conn_info + 'SERVER={};'.format(server) # server name goes here
		conn_info = conn_info + 'DATABASE_NAME={};'.format(database_name) # database name goes here
		conn_info = conn_info + 'Trusted_Connection=yes' # use windows authentication
		cnn = pyodbc.connect(conn_info)
		print("Connected with SQL Server Native Client 10.0.\n")
	except pyodbc.Error as e1:
		try:
			conn_info = 'DRIVER=SQL Server Native Client 11.0;' # ms sql server2012
			conn_info = conn_info + 'SERVER={};'.format(server) # server name goes here
			conn_info = conn_info + 'DATABASE_NAME={};'.format(database_name) # database name goes here
			conn_info = conn_info + 'Trusted_Connection=yes' # use windows authentication
			cnn = pyodbc.connect(conn_info)
			print("Connected with SQL Server Native Client 11.0.\n")
		except pyodbc.Error as e2:
			print("Error: {}".format(e2))

	return cnn

def get_credentials(client_secret_file, application_name):
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir, 'drive-python.json')
	# print(credential_path)
	store = oauth2client.file.Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(client_secret_file, SCOPES)
		flow.user_agent = application_name
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

credentials = get_credentials()
http = credentials.authorize(httplib2.Http())

# this is for Drive API
serviceDrive = discovery.build('drive', 'v3', http=http)

# this is for Sheets API
serviceSheets = discovery.build('sheets', 'v4', http=http)

def backoff_hdlr(details):
	print("\nBacking off {wait:0.1f} seconds afters {tries} tries "
		"calling function {target}\n".format(**details))

def batch_request_callback(request_id, response, exception):
	if exception is not None:
	# Do something with the exception
		print("There was an error: {}".format(exception))
	else:
		pass

def get_data_from_server(server, SQL_filepath):

	# get server connection to WNDWPRDDB
	cnn = get_server_connection(server=server)

	if not cnn:
		print("Error: {} server connection does not exist.".format(server))
		return False

	# get query strings from files
	with open(SQL_filepath, 'r') as f:
		query = f.read()

	print("Retrieving data from SQL server... ")
	dataframe = pd.read_sql(query, cnn)

	cnn.close() # close connection

	return dataframe


@backoff.on_exception(backoff.expo, HttpError, on_backoff=backoff_hdlr)
def create_spreadsheet(spreadsheet_name, parent_folder_list, canShare='false', custom_metadata=None,):
	"""

	"""
	# metadata for new spreadsheet
	body = {
		'name': spreadsheet_name,
		'parents' : parent_folder_list,
		'mimeType': 'application/vnd.google-apps.spreadsheet',
		'copyRequiresWriterPermission' : 'false',	# changed from 'viewersCanCopyContent', which is now deprecated
		'capabilities.canShare' : canShare,			# indicate whether users can share this file with others
		'properties' : {}
	}

	if custom_metadata:
		for key, value in custom_metadata:
			body['properties'][key] = value

	# create spreadsheet, get file id (for permissions)
	# print("\tCreating spreadsheet: {}".format(spreadsheet_name))
	file = serviceDrive.files().create(body=body, fields='id').execute()
	sheet_id = file.get('id')

	return sheet_id