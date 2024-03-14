from barcode import*
import pymysql
import DBpassword

# Connect to the MySQL database
conn = pymysql.connect(
    host='localhost',
    user='root',
    password=DBpassword.password,
    db='mupemat1',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()



def last_code_retrieved(clientname):

    productcode = "SELECT * FROM productgen ORDER BY PRODUCTCODE DESC LIMIT 1"
    descriptioncode = "SELECT * FROM descriptiongen ORDER BY DESCRIPTIONCODE DESC LIMIT 1"
    blcode = "SELECT * FROM blgen ORDER BY BLCODE DESC LIMIT 1"
    clientcode = "SELECT CLIENTCODE FROM clientinfo WHERE CLIENTE = %s"

    cursor.execute(productcode)
    currentproduct = cursor.fetchone()['PRODUCTCODE']

    cursor.execute(descriptioncode)
    currentdescription = cursor.fetchone()['DESCRIPTIONCODE']

    cursor.execute(blcode)
    currentbl = cursor.fetchone()['BLCODE']

    cursor.execute(clientcode, (clientname,))
    clientcode = cursor.fetchone()['CLIENTCODE']

    get_client_code(currentproduct, currentdescription, currentbl, clientcode)

    return currentproduct, currentdescription, currentbl, clientcode, clientname