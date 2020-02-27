#!/usr/bin/env python

"""
DOCSTRING


"""



from .context import interface


def main():

	server = "WNDWPRDDB"
	database_name = "Data_and_Policy"

	cnn = interface.get_server_connection(server, database_name)

	print(cnn)

	# get_data_from_server(server, SQL_filepath)

if __name__ == '__main__':
	main()