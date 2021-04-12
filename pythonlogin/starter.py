import psycopg2
import pandas as pd;
from sqlalchemy import create_engine
import sys
import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

param_dic = {
    "host"      : "127.0.0.1",
    "database"  : "legal_search",
    "user"      : "postgres",
    "password"  : "P@55w0rd"
}

connect = "postgresql://%s:%s@%s:5432/%s" % (
    param_dic['user'],
    param_dic['password'],
    param_dic['host'],
    param_dic['database']
)

def connect(params_dic):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params_dic)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1)
    print("Connection successful")
    return conn
conn = connect(param_dic)

def create_account():
    """ Create accounts table and add an initial user account """

    # Create accounts table
    conn = psycopg2.connect(host='127.0.0.1', dbname='postgres', user='postgres', password='P@55w0rd')
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
        	id SERIAL PRIMARY KEY,
          	username varchar(50) NOT NULL,
          	password varchar(255) NOT NULL,
          	email varchar(100) NOT NULL
        );
    """)
    conn.commit()

    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM accounts WHERE username = %s;
    """, ('test',))
    conn.commit()
    user = cur.fetchone()
    
    if user == None:
        # Create test user accounts
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (id, username, password, email) VALUES (1, 'test', 'test', 'test@test.com');
        """)
        conn.commit()
create_account()

def process_raw_data():
    # import raw data from excel spreadsheet
    df = pd.read_excel('../data/raw_data.xlsx')
    df = df.reset_index()

    # rename columns
    df = df.rename(columns={'index':'business_id'})
    df = df.rename(columns={'Business question/issue':'business_issue'})
    df = df.rename(columns={'Potential Legal issue implicated by business question':'legal_issue'})
    df = df.rename(columns={'Legal professional':'legal_professional'})

    # stem the business_issue data
    ps = PorterStemmer()
    df['stemmed_issue'] = df.apply(lambda row: word_tokenize(row['business_issue']), axis=1)
    df['stemmed_issue'] = df.apply(lambda row: [ps.stem(w) for w in row['stemmed_issue']], axis=1)
    df['stemmed_issue'] = df.apply(lambda row: ' '.join(row['stemmed_issue']), axis=1)

    insert_raw_data(df)

def insert_raw_data(df):
    """ Insert raw data to legal_search database """
    engine = create_engine('postgresql://postgres:P@55w0rd@127.0.0.1:5432/legal_search')
    df.to_sql(
        'business_legal_raw',
        con=engine,
        index=False,
        if_exists='replace'
    )
    print("Raw data insert to PostgreSQL successful")

process_raw_data()

def insert_legal_professional_info():
    """ Insert lawyer information to legal_search database """

    # create a lawyer_info table in legal_search database
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS legal_professional_info (
            legal_professional_id SERIAL PRIMARY KEY,
            first_name varchar(255) NOT NULL,
            last_name varchar(255) NOT NULL,
            title varchar(255) NOT NULL,
            legal_department varchar(255),
            email varchar(255) NOT NULL,
            phone_number varchar(255) NOT NULL
        );
    """)
    conn.commit()

    # insert lawyer information from csv file to lawyer_info table
    cur = conn.cursor()
    with open('../data/legal_professional_info.csv', 'r') as f:
        # Notice that we don't need the `csv` module.
        # next(f) # Skip the header row.
        cur.copy_from(f, 'legal_professional_info', sep=',')
    conn.commit()
insert_legal_professional_info()

def create_legal_issues_table():
    """ Create a legal_issues table from business_legal_raw """

    # create a legal_issues table in legal_search database
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS legal_issues (
            legal_issue_id SERIAL PRIMARY KEY ,
            legal_issue varchar(255) NOT NULL
        );
    """)
    conn.commit()

    # insert legal issues into legal_issues table from business_legal_raw table
    cur = conn.cursor()
    cur.execute("""INSERT INTO legal_issues (legal_issue)
        SELECT DISTINCT legal_issue
        FROM business_legal_raw
    """)
    conn.commit()
create_legal_issues_table()

def create_business_legal_table():
    """ Create a business_legal table from business_legal_raw table """

    # create a business_legal table in legal_search database
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS business_legal (
            business_issue_id SERIAL PRIMARY KEY ,
            business_issue varchar(255) NOT NULL,
            business_issue_stemmed varchar(255) NOT NULL,
            legal_issue varchar(255) NOT NULL
        );
    """)
    conn.commit()

    # insert business and legal issues into business_legal table from business_legal_raw table
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO business_legal (business_issue, business_issue_stemmed, legal_issue)
        SELECT business_issue, stemmed_issue, legal_issue
        FROM business_legal_raw;
    """)
    conn.commit()
create_business_legal_table()

def link_issues_to_legal_pro():
    """ Link legal issues from business_legal table to legal professionals from legal_professional_info """

    # create a professional_legal table in legal_search database
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS professional_legal (
            professional_legal_id SERIAL PRIMARY KEY ,
            legal_issue_id int NOT NULL,
            legal_professional_id int NOT NULL
        );
    """)
    conn.commit()

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO professional_legal (legal_issue_id, legal_professional_id)
        SELECT DISTINCT (SELECT legal_issue_id FROM legal_issues li WHERE li.legal_issue = business_legal_raw.legal_issue)
            ,(SELECT legal_professional_id FROM legal_professional_info lpi WHERE (lpi.first_name || ' ' || lpi.last_name) = business_legal_raw.legal_professional)
        FROM business_legal_raw;
    """)
    conn.commit()
link_issues_to_legal_pro()

def create_professional_legal_issues_list():
    """ Create a table the lists the legal issues each legal professional can handle"""

    # create a table that contains a distinct list of legal issues and corresponding legal professional that handle those issues
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE professional_issues AS
        SELECT DISTINCT (first_name || ' ' || last_name) legal_professional
            ,legal_issue
        FROM professional_legal
            ,legal_professional_info
            ,legal_issues
        WHERE legal_issues.legal_issue_id = professional_legal.legal_issue_id
        AND legal_professional_info.legal_professional_id = professional_legal.legal_professional_id;
    """)
    conn.commit()

    # aggregate the list of legal issues handled by each legal professional
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE professional_issues_list AS
        SELECT legal_professional,
               string_agg(legal_issue, ', ' ORDER BY legal_professional) legal_issue_list
        FROM professional_issues
        GROUP BY legal_professional
        ORDER BY legal_professional;
    """)
    conn.commit()
create_professional_legal_issues_list()
