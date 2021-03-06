# Legal Triage

A web application that helps business professionals with business issues, find the appropriate legal professional to address these issues within a company.

## Setup

### Python
Ensure `python3` is installed on your local machine. You can check whether you have Python3 by running `python --version` in your terminal (for Macs) or command prompt (for Windows). 

If you do not have Python3:
* For MacOS, follow these instructions for installation: [Python3 Install Instructions for MacOS](https://installpython3.com/mac/)
* For Windows, follow these instructions for installation: [Python Install Instructions for Windows](https://realpython.com/installing-python/)

### PostgreSQL
In addition to Python, you will need to install PostgreSQL, a relational database management system. This can be done by downloading and installing [version 12.6](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads). At the time of this project's creation on MacOS Big Sur, the application pgAdmin4 does not run on later versions of PostgreSQL, therefore, it is safer to start with *version 12.6*. After running the installer, use the default settings. When you set up a password for Postgres, use `P@55w0rd` as the password for superuser. 

Once you've completed PostgreSQL installation, navigate to application pgAdmin4 to check for proper installation. pgAdmin4 will be used to manage your databases.

### Requirements
Assuming you have cloned this repository to your local machine, navigate to the *pythonlogin* folder within the repository folder. In your terminal or command prompt, run `pip install -r requirements.txt`. This will install the dependencies required by this web application.

### Database Setup
To set up the database with initial data, you can run the `starter.py` file. This can be done by running `python3 starter.py`. The `starter.py` file will create an inital user account (required by the application), batch upload business/legal issue data as well as legal professional information data, and set up your databases for the web application. To change the format or content of upload, see `process_raw_data()` and `insert_legal_professional_info()` in `starter.py`. To check whether batch upload was successful, you can check both the terminal or command prompt, or pgAdmin4 to see if your databases have been populated.

Files included in this repository that should be noted are: 
* `data/legal_professional_info.csv` which contains the legal professional information
* `data/raw_data.xlsx` which contains the batch of data prepared for initial upload in the `starter.py` file.

## Build/Run
To run the web application, in your terminal or command prompt, in the *pythonlogin* folder, run the following:
1. `export FLASK_APP=main.py`
2. `export FLASK_DEBUG=1`
3. `flask run`

This will start up your web application. To view in your browser, navigate to [localhost:5000/pythonlogin](localhost:5000/pythonlogin). You can sign in with the username: **test** and the password: **test**.

## Future Development/Known Issues
#### User Accounts
* There is no differentiation between administrative users and standard users

#### Publishing/Deployment
* Web application is locally run and cannot be shared via URL

#### Search Tool
* For queries with no search results, replace linked email address found in `main.py` line 270.
* Because of `nltk` stemming of input and data, the search tool is limited by its ability to recognize mispelled words
* Currently there are no corrective methods for incorrect or nonexistent search results. Machine learning implementation would be an ideal and powerful feature to add
* There is no feature that balances the load of legal professionals returned in the results list. This means that when business professionals search for a legal professional, they may always pick the same legal professional that appears at the top of the list.

#### Data Upload
* There is no current method for batch data upload
* Data upload features appear on the same page as search tool but should only be accessible to administrative users
* There is no current method to remove or add new legal professionals to the database

## Developers
This project/repo was built as a part of the Comp_Sci 397 course at Northwestern University by Tiffany Lau.
