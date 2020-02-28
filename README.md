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
pyodbc
pandas
backoff
google-api-python-client
```

## Running the tests

This repository comes with some basic tests to make sure your server connections and Google credentials are working appropriately.

Download ```./tests/basic_test.py```. Make sure the script contains the correct paths to your ```client_secret.json``` and ```server_connection_data.txt``` files.

```
client_secret_file = "C:/client_secret.json"
connection_data = "C:/connection_data/server_connection_data.txt"
```

Next, ```cd``` into the appropriate directory and run the ```basic_test.py``` file. (The first time this is run, you'll need to authorize your credentials by following the OAuth authorization flow. This only happens once, after which you can delete your ```client_secret.json``` file.)

## Built With

* [Google Drive API](https://developers.google.com/drive) - The API used to communicate with Google Drive
* [Google Sheets API](https://developers.google.com/sheets) - The API used to interact with the contents of Google sheets

## Authors

* **Will Kearney** - *Initial work* - [GitHub](https://github.com/wtkearney)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* **Shawn Helm** - *Principal Analyst at PPS* - [PPS Analytics Homepage](https://www.pps.net/Page/940)