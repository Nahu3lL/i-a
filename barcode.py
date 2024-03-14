import pymysql
import DBpassword
from datetime import datetime
from M2W import*

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

addclient = False
addproduct = False
adddescription = False
addbl = False
oldcode = False

def date():
    today = datetime.today()

    year = today.year
    month = today.month
    day = today.day

    datelog = day + month + year

    return datelog

def increment_code(cursor, currentproduct, currentdescription, currentbl, clientcode):
    if addproduct:
        last_three_digits = currentproduct[-3:]  # Extract the last three characters
        last_three_digits = last_three_digits.lstrip('0')  # Strip leading zeros
        nextproduct = int(last_three_digits) + 1
        nextproductcode = f"{clientcode}-{nextproduct:03d}"  # Format with leading zeros

    if adddescription:
        last_five_digits = currentdescription[-5:]  # Extract the last five characters
        last_five_digits = last_five_digits.lstrip('0')  # Strip leading zeros
        nextdescription = int(last_five_digits) + 1
        nextdescriptioncode = f"{clientcode}-{nextdescription:05d}"  # Format with leading zeros

    if addbl:
        last_three_digits = currentbl[-3:]  # Extract the last three characters
        last_three_digits = last_three_digits.lstrip('0')  # Strip leading zeros
        nextbl = int(last_three_digits) + 1
        nextblcode = f"{clientcode}-{nextbl:03d}"  # Format with leading zeros

    new_row(cursor, increment_code, qproduct, qdescription, qbl, clientcode)
    barcodebuilder(clientcode, sproduct, sdescription, sbl, increment_code, date, currentproduct, currentdescription, currentbl)
    return nextproduct, nextproductcode, nextdescription, nextdescriptioncode, nextbl, nextblcode

def new_row(cursor, increment_code, qproduct, qdescription, qbl, clientcode):
    if addproduct:
        newproduct = qproduct()
        nextproductcode = increment_code(cursor, clientcode)
        query = "INSERT INTO productgen (PRODUCTCODE, PRODUCT) VALUES (%s, %s)"
        cursor.execute(query, (nextproductcode, newproduct))
        conn.commit()

    if adddescription:
        newdescription = qdescription()
        nextdescriptioncode = increment_code(cursor, clientcode)
        query = "INSERT INTO descriptiongen (DESCRIPTIONCODE, DESCRIPTION) VALUES (%s, %s)"
        cursor.execute(query, (nextdescriptioncode, newdescription))
        conn.commit()

    if addbl:
        newbl = qbl()
        nextblcode = increment_code(cursor, clientcode)
        query = "INSERT INTO blgen (BLCODE, BL) VALUES (%s, %s)"
        cursor.execute(query, (nextblcode, newbl))
        conn.commit()

def get_client_code(currentproduct, currentdescription, currentbl, clientcode):

    if clientcode != "":
        if oldcode:
            qoldcode(currentproduct, currentdescription, currentbl, clientcode)
        else:
            qproduct(currentproduct, currentdescription, currentbl, clientcode)
    else:
        print("Nombre no encontrado, revise errores de ortografía o hable con un superior si es un cliente nuevo")
        clientcode = None

def qoldcode(currentproduct, currentdescription, currentbl, clientcode):
    knowncode = ""
    question = str(input("¿Sabe el codigo entero o quiere que lo volvamos a armar juntos? (lo sé\\armar):")).lower() =='armar'

    if question:
        qproduct(currentproduct, currentdescription, currentbl, clientcode)
    else: 
        knowncode = str(input("Ingrese el codigo: "))
        expandbarcode(barcodebuilder)
        return knowncode 

def qproduct(currentproduct, currentdescription, currentbl, clientcode):
    global addproduct
    question = str(input("¿Quiere agregar un producto nuevo o usar uno existente? (nuevo\\existente):")).lower() == 'nuevo'

    if question:
        newproduct = str(input("Enter product:"))
        qdescription(currentproduct, currentdescription, currentbl, clientcode)
        addproduct = True
    else: sproduct()

    return newproduct
    
def qdescription(currentproduct, currentdescription, currentbl, clientcode):
    global adddescription
    question = str(input("¿Quiere agregar una descripcion nueva o usar una existente? (nuevo\\existente):")).lower() == 'nuevo'

    if question:
        newdescription = str(input("Enter description:"))
        qbl(cursor, currentproduct, currentdescription, currentbl, clientcode)
        adddescription = True
    else: sdescription()

    return newdescription

def qbl(cursor, currentproduct, currentdescription, currentbl, clientcode):
    global addbl
    newbl = ""
    question = str(input("¿Quiere agregar un BL nuevo o usar uno existente? (nuevo\\existente):")).lower() == 'nuevo'

    if question:
        newbl = str(input("Enter bl:"))
        increment_code(cursor, currentproduct, currentdescription, currentbl, clientcode)
        addbl = True
        return newbl
    else: 
        sbl()
        newbl = None

def sproduct():
    oldproduct = str(input("Ingrese el producto: "))

    query = "SELECT PRODUCTCODE FROM productgen WHERE PRODUCT = %s"
    cursor.execute(query, (oldproduct,))
    oldproductcode = cursor.fetchone()

    if oldproductcode:
        qdescription()
    else: 
        print("El producto que ingresó no devolvió esultados, corrija errores de ortagrafia y vuelva a intentar o salga del programa")
        sproduct()

    return oldproductcode

def sdescription():
    olddescription = str(input("Ingrese la descripcion: "))

    query = "SELECT DESCRIPTIONCODE FROM descriptiongen WHERE DESCRIPTION = %s"
    cursor.execute(query, (olddescription,))
    olddescriptioncode = cursor.fetchone()

    if olddescriptioncode:
        qbl()
    else: 
        print("La descripcion que ingresó no devolvió esultados, corrija errores de ortagrafia y vuelva a intentar o salga")
        sdescription()

    return olddescriptioncode

def sbl(clientcode, currentproduct, currentdescription, currentbl):
    oldbl = str(input("Ingrese el bl: "))

    query = "SELECT BLCODE FROM blgen WHERE BL = %s"
    cursor.execute(query, (oldbl,))
    oldblcode = cursor.fetchone()

    if oldblcode:
        barcodebuilder(clientcode, sproduct, sdescription, sbl, increment_code, date, currentproduct, currentdescription, currentbl)
    else: 
        print("El bl que ingresó no devolvió esultados, corrija errores de ortagrafia y vuelva a intentar o salga")
        sbl()

    return oldblcode

def barcodebuilder(clientcode, sproduct, sdescription, sbl, increment_code, date, currentproduct, currentdescription, currentbl):
    global oldcode
    datec = date()
    nextproduct, nextdescription, nextbl = increment_code(cursor, currentproduct, currentdescription, currentbl, clientcode)
    oldproduct = sproduct()
    olddescription = sdescription()
    oldbl = sbl()
    newproduct = ""
    newdescription = ""
    newbl = ""
    newbarcode = ""
    oldbarcode = ""

    if oldcode:
        oldbarcode = clientcode + "-" + oldproduct + "-" + olddescription + "-" + oldbl + "-" + "1"
        question = input("¿Es este el codigo que buscabas: {oldbarcode}? (si\\no)").lower()== 'si'

        if question:
            expandbarcode()
            return oldbarcode
        else: 
            print("vuelva a intentar o cierre el programa")
            oldbarcode = ""
            starter()
    else: 
        if addproduct:
            newproduct = increment_code(nextproduct)
            addproduct = False
        else: newproduct = oldproduct

        if adddescription:
            newdescription = increment_code(nextdescription)
            adddescription = False
        else: newdescription = olddescription

        if addbl:
            newbl = increment_code(nextbl)
            addbl = False
        else: newbl = oldbl

        newbarcode = clientcode + "-" + newproduct + "-" + newdescription + "-" + newbl + "-" + datec + "-1"
        print("Este es tu nuevo codigo: {newbarcode}")
        expandbarcode()
        return newbarcode

def expandbarcode(barcodebuilder):
    global oldcode
    oldbarcode, newbarcode = barcodebuilder()
    gcode1 = oldbarcode[:14]
    gcode2 = newbarcode[:14]
    question = int(input("¿Cuantos productos identicos van a haber en esta carga?"))

    if oldcode:
        codeamount = gcode1[3:] + question - 1
        finalcode1 = gcode1 + codeamount
        print(finalcode1)
        return finalcode1
    else:
        codeamount = gcode2[3:] + question - 1
        finalcode2 = gcode1 + codeamount
        print(finalcode2)
        return finalcode2
        
#def logreg(cursor, barcodebuilder):
    codetolog = barcodebuilder()

    query = "INSERT INTO barcodereg (BARCODE) VALUES (%s)"
    data = ("Value1", "Value2")
    cursor.execute(query, data)
    conn.commit()
    cursor.close()
    conn.close()

def starter():
    global oldcode
    org = input("¿Quiere crear un codigo nuevo o usar uno viejo? (nuevo\\viejo):").lower() == 'viejo'

    if org:
        oldcode = True
        clientname = str(input("Enter the client name: "))
        last_code_retrieved(clientname)
    else:
        clientname = str(input("Enter the client name: "))
        last_code_retrieved(clientname)

    return clientname


if __name__ == '__main__':
    starter()