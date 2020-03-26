# SQL Google Interface

This project provides an easy set of tools to transfer data between a SQL database and Google Drive. It was developed at Portland Public Schools (PPS) in Portland, OR to help administrators and analysts programatically share sensitive data with schools. For example, this interface allows analysts to create simple python scripts that pull data from an internal database and populate individual school folders on the Google Drive. Users can format spreadsheets, upload graphs, change permissions, and so forth.

The advantage of using Google Drive to communicate with schools is:
1. School principals, secretaries, and administrators are familiar with Google Drive
2. School districts frequently already have security contracts in place with Google

## Getting Started

These instructions will get you a copy of the project up and running on your local machine. Note that you need Python 3.6 or higher (Python 2.7 is not supported.)

### Installing

Getting up an running takes three steps:
1. First, we need to install the actual Python package (and dependencies)
2. Next we need to obtain credentials from Google so you can access and modify server resources
3. Lastly, we need to create a text file containing information for connecting to your internal database

#### Installing the Python package

First, open a command prompt and install the package using PIP. This will automatically install dependencies (which are listed below if you'd rather install them independently):

```
pip install sql-google-interface
```

You can check that the package has been installed by examining your installed python packages:

```
pip freeze
```

#### Obtaining Google credentials

Go to the [Google API console](https://console.developers.google.com/). If your organization already has a project, ask the project owner to grant you member permissions. Otherwise, create a new project for your organization and call it something like "SQL-google-interface".

Navigate to the project, and [enable the Google Drive and Google Sheets API's](https://support.google.com/googleapi/answer/6158841?hl=en).

Create credentials!
1. Go to the "Credentials" tab on the left-hand sidebar
2. Click "Create Credentials" -> "OAuth client ID"
3. Select "Other" as the Application Type. For the name, use something like "your-name-client-id".
4. After clicking create, download the client ID, rename it to ```client_secret.json```, and place it in your ```C:/``` drive.

#### Obtaining Google credentials

Create a text file called ```server_connection_data.txt``` and place it in a directory like ```C:\connection_data\```.

This file should look like:

```
server = [server_name]
database = [database_name]
```

All done! You are ready to run the basic tests.

### Prerequisites

If you're interested, here is a list of package dependencies

```
backoff
google-api-python-client
numpy
pyodbc
pandas
```

## Running the tests

This repository comes with some basic tests to make sure your server connections and Google credentials are working appropriately.

Download ```./tests/basic_test.py```. Make sure the script contains the correct paths to your ```client_secret.json``` and ```server_connection_data.txt``` files.

```
client_secret_file = "C:/client_secret.json"
connection_data = "C:/connection_data/server_connection_data.txt"
```

Next, ```cd``` into the appropriate directory and run the ```basic_test.py``` file. (The first time this is run, you'll need to authorize your credentials by following the OAuth authorization flow. This only happens once, after which you can delete your ```client_secret.json``` file.)

## Usage example

Here is a short example script that takes data from a SQL database and uploads it into a google sheet. If it has already been run today, it deletes the current spreadsheet and creates a new one. Notice how custom metadata is used to identify files.

```
from datetime import date
from sql_google_interface import interface

server = <your-server-name>
database_name = <your-database-name>
parent_folder_id = <parent-folder-id>
SQL_filepath = "./data.sql"
client_secret_file = "C:/client_secret.json"

# get the connection to the SQL server and get data
cnn = interface.get_server_connection(server, database_name)
dataframe = interface.get_data_from_server(cnn, SQL_filepath)
cnn.close()

# get credentials for uploading data
credentials = interface.get_credentials(client_secret_file)

# create a drive and sheets service to interact with Google
drive_service = interface.get_drive_service(credentials=credentials, service_type='drive')
sheets_service = interface.get_drive_service(credentials=credentials, service_type='sheets')

# Create filename using month abbreviation, day, and year
today = date.today().strftime("%b-%d-%Y")
data_filename = "Data run {}".format(today)

# search to see if a file has already been uploaded today; if so delete it
file_data_from_search = interface.get_files_from_drive(drive_service=drive_service,
	parent_id=parent_folder_id,
	custom_metadata={"data-date" : today})

file_ids_from_search = [item['id'] for item in file_data_from_search]
if file_ids_from_search:
	print("There has already been a file created today. I will overwrite it with new data.")
	interface.delete_drive_files_by_ID(drive_service=drive_service, list_of_file_ids=file_ids_from_search)

sheet_id = interface.create_spreadsheet(drive_service=drive_service,
	spreadsheet_name=data_filename,
	parent_folder_list=[parent_folder_id],
	custom_metadata={"data-date" : today})
print("Created spreadsheet with id {}".format(sheet_id))

# upload data to the spreadsheet
interface.populate_spreadsheet_from_df(sheets_service, sheet_id, dataframe)

# format the spreadhseet
interface.format_spreadsheet(sheets_service, sheet_id, wrap_strategy="WRAP")
```

## Built With

* [Google Drive API](https://developers.google.com/drive) - The API used to communicate with Google Drive
* [Google Sheets API](https://developers.google.com/sheets) - The API used to interact with the contents of Google sheets

## Authors

* **Will Kearney** - *Initial work* - [GitHub](https://github.com/wtkearney)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* **Shawn Helm** - *Principal Analyst at PPS* - [PPS Analytics Homepage](https://www.pps.net/Page/940)
