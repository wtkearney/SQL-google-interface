#!/usr/bin/env python

"""
DOCSTRING


"""

from sql_google_interface import interface

# the first time you are using this application, specify where your client secret file is
# subsequently, it is automatically stored and accessed so you can delete the client secret
client_secret_file = "C:/client_secret.json"
connection_data = "C:/connection_data/server_connection_data.txt"

def test_server_connection():

	print("Testing server connection...")
	server, database_name = interface.read_connection_data_from_external_file(connection_data)

	# open and close a connection to make sure it works
	cnn = interface.get_server_connection(server, database_name)
	cnn.close()

	print("Done!\n")

def test_credentials():

	print("Testing credentials...", end="")

	# The first time this is run, you need to specify where your client secret is
	credentials = interface.get_credentials() # interface.get_credentials(client_secret_file)

	drive_service = interface.get_drive_service(credentials=credentials, service_type='drive')
	sheets_service = interface.get_drive_service(credentials=credentials, service_type='sheets')

	print("Done!\n")

def test_file_creation_and_deletion():

	print("Testing file creation and deletion...")

	credentials = interface.get_credentials()

	drive_service = interface.get_drive_service(credentials=credentials, service_type='drive')

	file_id = interface.create_spreadsheet(service=drive_service,
		spreadsheet_name="test spreadsheet",
		# parent_folder_list=['1dtIlqofnvtXxEhTtNN_mu2yRKuw6Hjxq'],
		custom_metadata={"testKey" : "testValue"})
	print("Created spreadsheet with ID: {}".format(file_id))

	file_data_from_search = interface.get_file_ids_and_names_from_drive(service=drive_service, custom_metadata={"testKey" : "testValue"})
	file_ids_from_search = [item['id'] for item in file_data_from_search]
	print("File IDs from search: {}".format(file_ids_from_search))

	print("Deleting files...")
	interface.delete_drive_files_by_ID(service=drive_service, list_of_file_ids=file_ids_from_search)

	print("Done!\n")

def main():

	test_server_connection()
	test_credentials()
	test_file_creation_and_deletion()

	

if __name__ == '__main__':
	main()