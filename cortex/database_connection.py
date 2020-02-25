import psycopg2
import os 

# connect to database. Never save your password to a notebook.
connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = '', # secure password entry. Enter DB password in the prompt and press Enter.
    host      = "",
    port      = '5432'
)

# create cursor that is used throughout
try:
    c = connection.cursor()
    print("Connected!")
except Exception as e:
    print("Connection problem chief!\n")
    print(e)