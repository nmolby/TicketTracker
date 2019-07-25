import pyodbc
server = 'ticket-tracker.database.windows.net'
database = 'Ticket Tracker'
username = 'nmolby'
password = 'Il0veMicr0s0ft'
driver= '{ODBC Driver 17 for SQL Server}'
cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()
cursor.execute("SELECT * FROM Teams")
row = cursor.fetchone()
while row:
    print (str(row[0] + str(row[1])))
    row = cursor.fetchone()