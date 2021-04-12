from flask import Flask, render_template, request, redirect, url_for, session
#from flask_mysqldb import MySQL
#import MySQLdb.cursors
import re
import psycopg2
import csv
import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import pandas as pd;
from sqlalchemy import create_engine
import sqlalchemy
import numpy

app = Flask(__name__)
app.config['DEBUG'] = True

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['host'] = '127.0.0.1'
app.config['user'] = 'postgres'
app.config['password'] = 'P@55w0rd'
app.config['dbname'] = 'pythonlogin'
app.config['UPLOAD_EXTENSIONS'] = ['.csv']

# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests
@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']

        # Check if account exists using PostgreSQL
        conn = psycopg2.connect(host='127.0.0.1', dbname='postgres', user='postgres', password='P@55w0rd')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()

        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'

    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if account exists using PostgreSQL
        conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='P@55w0rd')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()

        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            conn.commit()
            msg = 'You have successfully registered!'

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/pythonlogin/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='P@55w0rd')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        print('account: ', account[1])
        return render_template('profile.html', account=account, username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        # search by business issue
        search = request.form['search']

        conn = psycopg2.connect(host='127.0.0.1', dbname='legal_search', user='postgres', password='P@55w0rd')
        cursor = conn.cursor()

        ps = PorterStemmer()
        tokenized_input = word_tokenize(search)
        stemmed_input = []

        for w in tokenized_input:
            stemmed_input.append(ps.stem(w))

        stemmed_input = ' '.join(stemmed_input)

        cursor.execute("SELECT set_limit(0.3);")
        conn.commit()

        engine = create_engine('postgresql://postgres:P@55w0rd@127.0.0.1:5432/legal_search')
        dbConnection = engine.connect();

        filtered_legal_issues = pd.read_sql(("""
            SELECT legal_issue
                ,similarity(business_issue_stemmed, %(search)s) AS similarity
                ,business_issue_id
            FROM business_legal
            WHERE business_issue_stemmed %% %(search)s
            ORDER BY similarity DESC;"""),
        dbConnection, params={"search":stemmed_input})

        if not filtered_legal_issues.empty:

            filtered_legal_issues.to_sql(
                'filtered_legal_issues',
                con=engine,
                index=False,
                if_exists='replace'
            )

            filtered_legal_ids = pd.read_sql(("""
                SELECT DISTINCT legal_issue_id
                    ,filtered_legal_issues.legal_issue
                    ,similarity
                FROM legal_issues, filtered_legal_issues
                WHERE filtered_legal_issues.legal_issue = legal_issues.legal_issue;"""),
            dbConnection)

            filtered_legal_ids.to_sql(
                'filtered_legal_ids',
                con=engine,
                index=False,
                if_exists='replace'
            )

            filtered_legal_professional_ids = pd.read_sql(("""
                SELECT DISTINCT legal_professional_id
                    ,filtered_legal_ids.legal_issue
                    ,similarity
                FROM professional_legal, filtered_legal_ids
                WHERE filtered_legal_ids.legal_issue_id = professional_legal.legal_issue_id
                ORDER BY similarity DESC;"""),
            dbConnection)

            filtered_legal_professional_ids.to_sql(
                'filtered_legal_professional_ids',
                con=engine,
                index=False,
                if_exists='replace'
            )

            final_legal_professionals = pd.read_sql(("""
                SELECT DISTINCT ON (legal_professional_info.legal_professional_id) legal_professional_info.legal_professional_id
                    ,(first_name || ' ' || last_name) AS name
                    ,title
                    ,legal_department
                    ,email
                    ,phone_number
                    ,similarity
                    ,filtered_legal_professional_ids.legal_issue
                FROM legal_professional_info, filtered_legal_professional_ids
                WHERE filtered_legal_professional_ids.legal_professional_id = legal_professional_info.legal_professional_id;"""),
            dbConnection)

            final_legal_professionals = final_legal_professionals.sort_values(by='similarity', ascending=False)
            final_legal_professionals.to_sql(
                'final_legal_professionals',
                con=engine,
                index=False,
                if_exists='replace'
            )

            cursor.execute("""
                SELECT name
                    ,title
                    ,legal_department
                    ,email
                    ,phone_number
                    ,similarity
                    ,legal_issue_list
                    ,legal_issue
                FROM final_legal_professionals
                JOIN professional_issues_list ON professional_issues_list.legal_professional = final_legal_professionals.name
                ORDER BY similarity DESC;""")
            conn.commit()
            data = cursor.fetchall()

            if len(data) == 0:
                message = 'No results found'
                email = "mailto:tiffanylau2021@u.northwestern.edu?subject=Legal%20Triage%20Correction:%20"+ request.form['search'] + "&body=Query%20should%20return:%20"
                return render_template('home.html',
                                        username=session['username'],
                                        prev_query=request.form['search'],
                                        message=message,
                                        email=email)

            data = [list(professional) for professional in data]
            for professional in range(len(data)):
                data[professional].append(data[professional][3])
                data[professional][3] = "mailto:"+data[professional][3]+"?subject="+request.form['search']

            return render_template('home.html',
                                    data=data,
                                    prev_query=request.form['search'],
                                    username=session['username'])
        else:
            message = 'No results found'
            email = "mailto:tiffanylau2021@u.northwestern.edu?subject=Legal%20Triage%20Correction:%20"+ request.form['search'] + "&body=Query%20should%20return:%20"
            return render_template('home.html',
                                    username=session['username'],
                                    prev_query=request.form['search'],
                                    message=message,
                                    email=email)
    return render_template('home.html', username=session['username'])

@app.route('/add_legal_issue', methods=['GET', 'POST'])
def add_legal_issue():
    message=''
    flag = 0
    if request.method == "POST":
        business_issue = request.form['businessissue']
        legal_issue = request.form['legalissue']
        lawyer_name = request.form['lawyername']

        engine = create_engine('postgresql://postgres:P@55w0rd@127.0.0.1:5432/legal_search')
        dbConnection = engine.connect();

        conn = psycopg2.connect(host='127.0.0.1', dbname='legal_search', user='postgres', password='P@55w0rd')
        cursor = conn.cursor()

        print("legal issue ", legal_issue)
        cursor.execute("""SELECT legal_professional_id
            FROM legal_professional_info
            WHERE (first_name || ' ' || last_name) = %s;""", (lawyer_name,))
        conn.commit()
        legal_professional_id = cursor.fetchone()
        print("legal_professional_id ", legal_professional_id[0])

        cursor.execute("""SELECT legal_issue_id
            FROM legal_issues
            WHERE legal_issues.legal_issue = %s;
        """, (legal_issue,))
        conn.commit()
        legal_issue_id = cursor.fetchone()

        if legal_issue_id == None:
            cursor.execute("INSERT INTO legal_issues (legal_issue) VALUES (%s);", (legal_issue,))
            conn.commit()

            cursor.execute("""SELECT legal_issue_id
                FROM legal_issues
                WHERE legal_issues.legal_issue = %s;
            """, (legal_issue,))
            conn.commit()
            legal_issue_id = cursor.fetchone()
            print("legal_issue_id ", legal_issue_id[0])

            cursor.execute("""INSERT INTO professional_legal (legal_issue_id, legal_professional_id) VALUES (%s, %s);""",
                (legal_issue_id[0], legal_professional_id[0],))
            conn.commit()

            ps = PorterStemmer()
            tokenized_input = word_tokenize(business_issue)
            stemmed_input = []
            for w in tokenized_input:
                stemmed_input.append(ps.stem(w))

            print(stemmed_input)
            stemmed_input = ' '.join(stemmed_input)
            print(stemmed_input)

            cursor.execute("INSERT INTO business_legal (business_issue, business_issue_stemmed, legal_issue) VALUES (%s, %s, %s);",
                (business_issue, stemmed_input, legal_issue,))
            conn.commit()

            professional_issues = pd.read_sql(("""
                SELECT DISTINCT (first_name || ' ' || last_name) legal_professional
                    ,legal_issue
                FROM professional_legal
                    ,legal_professional_info
                    ,legal_issues
                WHERE legal_issues.legal_issue_id = professional_legal.legal_issue_id
                AND legal_professional_info.legal_professional_id = professional_legal.legal_professional_id;"""),
            dbConnection)

            professional_issues.to_sql(
                'professional_issues',
                con=engine,
                index=False,
                if_exists='replace'
            )

            professional_issues_list = pd.read_sql(("""
                SELECT legal_professional,
                       string_agg(legal_issue, ', ' ORDER BY legal_professional) legal_issue_list
                FROM professional_issues
                GROUP BY legal_professional
                ORDER BY legal_professional;"""),
            dbConnection)

            professional_issues_list.to_sql(
                'professional_issues_list',
                con=engine,
                index=False,
                if_exists='replace'
            )

            message = "This entry was saved"
        else:
            message = "This legal issue already exists. Try adding data in "
            flag = 1

    return render_template('add_legal_issue.html', message=message, username=session['username'], flag=flag)

@app.route('/add_business_issue', methods=['GET', 'POST'])
def add_business_issue():
    message=''
    if request.method == "POST":
        business_issue = request.form['businessissue']
        legal_issue = request.form['legalissue']

        ps = PorterStemmer()
        tokenized_input = word_tokenize(business_issue)
        stemmed_input = []
        for w in tokenized_input:
            stemmed_input.append(ps.stem(w))

        print(stemmed_input)
        stemmed_input = ' '.join(stemmed_input)
        print(stemmed_input)

        conn = psycopg2.connect(host='127.0.0.1', dbname='legal_search', user='postgres', password='P@55w0rd')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO business_legal (business_issue, business_issue_stemmed, legal_issue) VALUES (%s, %s, %s);",
            (business_issue, stemmed_input, legal_issue,))
        conn.commit()

        message = "This entry was saved"

    return render_template('add_business_issue.html', message=message, username=session['username'])

if __name__ == '__main__':
    app.debug = True
    app.run()
