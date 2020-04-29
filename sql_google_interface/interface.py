#!/usr/bin/env python

"""
DOCSTRING


"""


import backoff # this will help avoid Quote exceeded errors when making REST requests
import datetime
import httplib2
import json
import numpy as np
import oauth2client
import os
import pandas as pd
import pyodbc
import sys
import time
from apiclient import discovery
from apiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from oauth2client import client
from oauth2client import tools
from oauth2client import file


def read_connection_data_from_external_file(filepath, separator="="):
	"""Reads SQL server connection information from an external file.
	Keeping this information external is potentially important for security
	reasons.

	Currently this method is capable of utilizing .txt and .json file types.
	Other file types can be added as needed by the end users.

	The format of this file should be:
		server = [server_name]
		database = [database_name]

	Arguments:
		filepath -- the location of the connection file (e.g. "C:/
			connection_data/server_connection_data.txt")
		separator -- the delimiter (default "=")
	Returns:
		The server, database as strings
	"""
	if filepath.endswith(".txt"):
		with open(filepath, 'r') as f:
			connection_data = f.readlines()
			f.close()

		connection_data_dict = dict()

		# clean strings and split on delimiter
		for entry in connection_data:
			# strip whitespace and trailing new lines
			entry_cleaned = entry.replace(" ", "").strip("\n")
			split_string = entry_cleaned.split(separator)
			connection_data_dict[ split_string[0] ] = split_string[1]
	elif filepath.endswith(".json"):
		with open(filepath, "r") as f:
			connection_data_dict = json.load(f)
			f.close()
	else:
		raise ImportError("The Connection data file, specified by the filepath parameter, is neither a .txt or .json file.")
		exit(0)

	if ("server" not in connection_data_dict) or ("database" not in connection_data_dict):
		raise ValueError("Connection data file must contain server and database_name, formated like:\n\nserver = server_name\ndatabase = database_name\n")
		exit(0)

	server = connection_data_dict["server"]
	database = connection_data_dict["database"]
	# print("Server={}\nDatabase={}".format(server, database))

	return server, database

def get_server_connection(server, database_name):
	"""Tries to connect to the SQL database.
	Attempts connection with driver SQL Server Native Client 10.0 and 11.0 and
	a generic pyodbc sql server connection.

	Arguments:
		server -- the name of the server
		database_name -- the name of the database
	Returns:
		The connection object
	"""

	def try_connection(driver):
		try:
			conn_info = 'DRIVER={};'.format(driver)
			conn_info += 'SERVER={};'.format(server)
			conn_info += 'DATABASE_NAME={};'.format(database_name)
			conn_info += 'Trusted_Connection=yes'
			cnn = pyodbc.connect(conn_info)
		except pyodbc.Error as e:
			print("Error: {}".format(e))
			return None
		return cnn

	driver_strings = ["SQL Server Native Client 10.0", "SQL Server Native Client 11.0", "{SQL Server}"]

	cnn = None
	for driver in driver_strings:
		cnn = try_connection(driver)
		if cnn:
			print("Connected with {}".format(driver))
			return cnn

	print("Error, cannot connect to SQL server.")
	exit()

def get_credentials(client_secret_file=None, application_name="SQL-google-interface", stored_credentials_dir="C:/credentials/"):
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Arguments:
		client_secret_file -- location of the client secret file. (e.g. "C:/client_secret.json")
			This only needs to be specified the first time the application is run.
		application_name -- the name of the application (default "SQL-google-interface")
		stored_credentials_dir -- the location where credentials will be stored (default "C:/credentials/")
	Returns:
		Credentials, the obtained credential.
	"""

	# If modifying these scopes, delete your previously saved credentials
	scopes = [
		'https://www.googleapis.com/auth/drive',
		'https://www.googleapis.com/auth/spreadsheets']

	if not os.path.exists(stored_credentials_dir):
		os.makedirs(stored_credentials_dir)
	credential_path = os.path.join(
		stored_credentials_dir,
		'sql-drive-interface-credentials.json')

	store = oauth2client.file.Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(client_secret_file, scopes)
		flow.user_agent = application_name
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

def get_drive_service(credentials, service_type, version=None):
	"""Retrieves the service used for making requests to

	Arguments:
		credentials -- Google API credentials
		service_type -- either "drive" or "sheets"
		version -- the version you are using (default None; this is automatically set depending on the service_type)
	Returns:
		The requested service
	"""

	if service_type not in ['drive', 'sheets']:
		raise ValueError("'service_type' argument must be 'drive' or 'sheets'.")
		exit(0)

	if not version:
		if service_type == 'drive':
			version = 'v3'
		elif service_type == 'sheets':
			version = 'v4'

	http = credentials.authorize(httplib2.Http())

	return discovery.build(service_type, version, http=http)

def backoff_hdlr(details):
	"""This is called when a function is backed off."""
	print("\nBacking off {wait:0.1f} seconds afters {tries} tries "
		"calling function {target}\n".format(**details))

def batch_request_callback(request_id, response, exception):
	"""Callback funnction for batch requests."""
	if exception is not None:
	# Do something with the exception
		print("There was an error: {}".format(exception))
	else:
		pass

def get_data_from_server(server_connection, SQL_filepath):
	"""Gets data from a SQL server in the form of a pandas dataframe

	Arguments:
		server_connection -- the connection to the server
		SQL_filepath -- filepath to a SQL query
	Returns:
		A pandas dataframe containing the requested data
	"""
	if not server_connection:
		print("Error: {} server connection does not exist.".format(server_connection))
		return False

	# get query strings from files
	with open(SQL_filepath, 'r') as f:
		query = f.read()

	# print("Retrieving data from SQL server... ")
	dataframe = pd.read_sql(query, server_connection)

	for col in dataframe:
		if dataframe[col].dtype == "datetime64[ns]":
			dataframe[col] = dataframe[col].apply(lambda x: x.strftime('%Y-%m-%d') if not pd.isnull(x) else '')

	# replace NaN and NaT with empty strings
	dataframe.fillna('', inplace=True)

	return dataframe

def clean_dataframe(dataframe):
	"""Type checks data in a pandas dataframe using numpy's select method.

	Arguments:
		dataframe -- the dataframe to be cleaned
	Returns:
		A pandas dataframe containing the cleaned data
	"""

	data = dataframe.copy().fillna("") # deal with the nulls first

	for column in data.columns.to_list():
	    conditions = [
	        (data[column].dtype == np.object),
	        (data[column].dtype == np.int64),
	        (
	            (data[column].dtype == "<M8[ns]") |
	            (data[column].dtype == np.datetime64) |
	            (data[column].dtype == datetime.datetime) |
	            (data[column].dtype == datetime.date)
	        )
	    ]
	    choices = [
	        data[column], # Python 3.x defaults to utf-8 so no need to force it
	        data[column].astype(str), # Convert all int and float values to str
			# convert any flavor of datetime object into a string containing
			# only year, month, and day in the YYYY-mm-dd format
	        data[column].dt.date.astype(str)
	    ]
	    data[column] = np.select(conditions, choices, "TYPE ERROR")

	return data

@backoff.on_exception(backoff.expo, HttpError, on_backoff=backoff_hdlr)
def get_files_from_drive(drive_service, name=None, substring_name=None, mime_type=None, custom_metadata=None, parent_id=None, trashed=False, result_fields=["name", "id"]):
	"""Gets files from Google Drive based on various search criteria

	Arguments:
		drive_service -- a Google Drive service
		name -- name of file(s) being searched for (default None)
		mime_type -- MIME type of file(s) being searched for, e.g. 'application/vnd.google-apps.folder' (default None)
		parent_id -- the ID of the parent folder for the file(s) being searched for (default None)
		trashed -- whether or not the file being searched for is trashed (default False)
		result_fields -- specifies what data is returns (default ["name", "id"])
	Returns:
		A dictionary containing the requested fields of the files found using the specified search criteria
	"""
	query_list = []
	if name:
		query_list.append("name = '{}'".format(name))

	if substring_name:
		query_list.append("name contains '{}'".format(substring_name))

	if mime_type:
		if mime_type == "folder":
			query_list.append("mimeType = 'application/vnd.google-apps.folder'")
		elif mime_type == "file":
			query_list.append("mimeType = 'application/vnd.google-apps.file'")
		else:
			raise ValueError("'mime_type' argument must be 'folder' or 'file'.")
			exit(0)

	if custom_metadata:
		for key, value in custom_metadata.items():
			q = "properties has {key='" + key + "' and value='" + value + "'}"
			query_list.append(q)

	if parent_id:
		query_list.append("'{}' in parents".format(parent_id))

	if trashed == False:
		query_list.append("trashed = false")
	elif trashed == True:
		query_list.append("trashed = true")


	q = query_list[0]
	for criterion in query_list[1:]:
		q = q + " and " + criterion

	result_fields_string = ','.join(result_fields)

	result = []
	page_token = None
	while True:
		try:
			param = {}
			if page_token:
				files = drive_service.files().list(q=q,
					spaces='drive',
					pageToken=page_token,
					fields='nextPageToken, files({})'.format(result_fields_string)).execute()
			else:
				files = drive_service.files().list(q=q,
					spaces='drive',
					fields='nextPageToken, files({})'.format(result_fields_string)).execute()

			result.extend(files['files'])
			page_token = files.get('nextPageToken')
			if not page_token:
				break
		except HttpError as e:
			print('An error occurred: {}'.format(e))
			break

	return result

def create_permissions(drive_service, file_id):
	"""
	This function is not functional yet.
	"""

	pass

@backoff.on_exception(backoff.expo, HttpError, on_backoff=backoff_hdlr)
def create_file(drive_service, file_name, mime_type, parent_folder_list=None, can_share='false', custom_metadata=None):
	"""Creates a file (note that foldors are treated the same as files)

	Arguments:
		drive_service -- a Google Drive service
		file_name -- the name of the file
		mime_type -- must be 'folder', 'spreadsheet', or 'document'
		parent_folder_list -- a list of parent IDs
		can_share -- indicates whether users can share this file with others (default 'false')
		custom_metadata -- a dictionary of key value pairs that allows you to create custom metadata. This might
			make it easy to search for these files later, for example.
	Returns:
		The sheet ID of the new file
	"""

	if mime_type == "folder":
		mime_type_api = 'application/vnd.google-apps.folder'
	elif mime_type == "spreadsheet":
		mime_type_api = 'application/vnd.google-apps.spreadsheet'
	elif mime_type == "document":
		mime_type_api = 'application/vnd.google-apps.document'
	else:
		raise ValueError("'mime_type' argument must be 'folder', 'spreadsheet', or 'document'")
		exit(0)

	# metadata for new spreadsheet
	body = {
		'name': file_name,
		'mimeType': mime_type_api,
		'copyRequiresWriterPermission' : 'false',	# changed from 'viewersCanCopyContent', which is now deprecated
		'capabilities.canShare' : can_share,			# indicate whether users can share this file with others
		'properties' : {}
	}

	if parent_folder_list:
		body['parents'] = parent_folder_list

	if custom_metadata:
		for key, value in custom_metadata.items():
			body['properties'][key] = value

	# create spreadsheet, get file id (for permissions)
	# print("\tCreating spreadsheet: {}".format(spreadsheet_name))
	file = drive_service.files().create(body=body, fields='id').execute()
	file_id = file.get('id')

	return file_id

@backoff.on_exception(backoff.expo, HttpError, on_backoff=backoff_hdlr)
def delete_drive_files_by_ID(drive_service, list_of_file_ids):
	"""Batch deletes files from a list of file IDs.

	Arguments:
		drive_service -- a Google Drive service
		list_of_file_ids -- a list of file IDs to delete
	"""

	batch = drive_service.new_batch_http_request(callback=batch_request_callback)
	for fileID in list_of_file_ids:
		#print('File ID: %s' % file.get('name'))
		batch.add(drive_service.files().delete(fileId=fileID))

	batch.execute()

@backoff.on_exception(backoff.expo, HttpError, on_backoff=backoff_hdlr)
def format_spreadsheet(sheet_service, sheet_id, wrap_strategy=None):
	"""Format's a spreadsheet for easier data reading (e.g. freezes top tow, makes header bold, wraps text)


	Arguments:
		sheet_service -- a Google sheets service
		sheed_id -- the ID of the sheet to be formatted
		wrap_strategy -- the wrap strategy used. See: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#wrapstrategy
	"""

	requests = []

	# always format header row
	requests.append({
	  "repeatCell": {
		"range": {
		  "sheetId": 0,
		  "startRowIndex": 0,
		  "endRowIndex": 1
		},
		"cell": {
		  "userEnteredFormat": {
			"textFormat": {
			  "bold": True
			}
		  }
		},
		"fields": "userEnteredFormat(textFormat)"
	  }
	})

	# freeze the top row
	requests.append({
	  "updateSheetProperties": {
		"properties": {
		  "sheetId": 0,
		  "gridProperties": {
			"frozenRowCount": 1
		  }
		},
		"fields": "gridProperties.frozenRowCount"
	  }
	})

	# # wrap text
	if wrap_strategy:

		requests.append({
		  "repeatCell": {
			"range": {
			  "sheetId": 0,
			  "startRowIndex": 1,
			  "endRowIndex": 500,
			  "startColumnIndex": 0,
			  "endColumnIndex": 27
			},
			"cell": {
			  "userEnteredFormat": {
				"wrapStrategy": wrap_strategy
			  }
			},
			"fields": "userEnteredFormat.wrapStrategy"
		  }
		})

	batchUpdateRequest = {'requests': requests}

	sheet_service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=batchUpdateRequest).execute()

	return sheet_id

@backoff.on_exception(backoff.expo, HttpError, on_backoff=backoff_hdlr)
def populate_spreadsheet_from_df(sheets_service, sheet_id, dataframe):
	"""Populates a spreadsheet with data from a pandas dataframe

	Arguments:
		sheets_service -- a Google Sheets service
		sheet_id -- the ID of the sheet to populate
		dataframe -- athe pandas dataframe containing the data
	Returns:
		The sheet ID of the spreadsheet
	"""
	dataframe_cleaned = dataframe.values.tolist()

	# do lots of type checking -- there's probably a better (faster) way to do this, but it works for now
	for row in dataframe_cleaned:
		for idx in range(len(row)):
			if type(row[idx]) is str:
				continue
			elif type(row[idx]) is int or type(row[idx]) is float:
				row[idx] = str(row[idx])
			elif row[idx] == None or row[idx] == "NULL":
				row[idx] = ""
			elif type(row[idx]) is datetime.date:
				row[idx] = row[idx].isoformat()
			else:
				# print("Type error")
				row[idx] = "TYPE_ERROR"

	# write data to spreadsheet
	dataframe_cleaned.insert(0, list(dataframe.columns.values))
	data_json = {'values': dataframe_cleaned}

	sheets_service.spreadsheets().values().update(spreadsheetId=sheet_id, range='A1', body=data_json, valueInputOption='RAW').execute()

	return sheet_id


@backoff.on_exception(backoff.expo, HttpError, on_backoff=backoff_hdlr)
def insert_file_into_folder(drive_service, folder_id, file_id):
	"""Insert a file into a folder.
	Args:
		folder_id: ID of the folder to insert the file into.
		file_id: ID of the file to insert.
	"""
	drive_service.files().update(fileId=file_id, addParents=folder_id, fields='id, parents').execute()

if __name__ == '__main__':
	try:
		import argparse
		flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
	except ImportError:
		flags = None
