import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="SQL-google-interface", # Replace with your own username
    version="1.4",
    author="William Kearney",
    author_email="wtkearney@gmail.com",
    description="An interface to interact between a SQL database and Google Drive folders",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wtkearney/SQL-google-interface",
    download_url = 'https://github.com/wtkearney/SQL-google-interface/archive/v1.4.tar.gz',
    install_requires=[
        "pyodbc",
        "pandas",
        "backoff",
        "google-api-python-client",
        "oauth2client"],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)

