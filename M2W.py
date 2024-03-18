from barcode import*
import pymysql
import DBpassword
from datetime import datetime

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


def dOF(year, month, day):
    currentDate = datetime(year, month, day)
    return currentDate.timetuple().tm_yday


def selectS():
    productCodeS = "SELECT * FROM productgen ORDER BY PRODUCTCODE DESC LIMIT 1"
    descriptionCodeS = "SELECT * FROM descriptiongen ORDER BY DESCRIPTIONCODE DESC LIMIT 1"
    blCodeS = "SELECT * FROM blgen ORDER BY BLCODE DESC LIMIT 1"
    clientCodeS = "SELECT CLIENTCODE FROM clientinfo WHERE CLIENTE = %s"

    return productCodeS, descriptionCodeS, blCodeS, clientCodeS

def querryS():
    productQ = "INSERT INTO productgen (PRODUCTCODE, PRODUCT) VALUES (%s, %s)"
    descriptionQ = "INSERT INTO descriptiongen (DESCRIPTIONCODE, DESCRIPTION) VALUES (%s, %s)"
    blQ = "INSERT INTO blgen (BLCODE, BL) VALUES (%s, %s)"
    barcodeQ = "INSERT INTO barcodereg (BARCODE, COMMENT) VALUES (%s, %s)"

    return productQ, descriptionQ, blQ, barcodeQ

def status():
    addproduct = False
    adddescription = False
    addbl = False
    oldcode = False
    
    return addproduct, adddescription, addbl, oldcode


def submit():
    try:
        # Fetch new data
        _, nextProductCode, _, nextDescriptionCode, _, nextBlCode, _, _, _= newData()
        productQ, descriptionQ, blQ, barcodeQ, _= querryS()
        newProduct = qProduct()
        newDescription = qDescription()
        newBl = qBl()
        finalBarCode = codeAmount()

        # Execute all the queries in a single transaction
        with conn.cursor() as cursor:
            cursor.execute(productQ, (nextProductCode, newProduct))
            cursor.execute(descriptionQ, (nextDescriptionCode, newDescription))
            cursor.execute(blQ, (nextBlCode, newBl))
            cursor.execute(barcodeQ, (finalBarCode, str(input("¿Quiere agregar algún comentario?"))))

        # Prompt for confirmation before committing changes
        confirmation = str(input("¿Desea guardar los cambios?  (S\\N)")).lower() == 's'
        
        if confirmation():
            conn.commit()
            print("Cambios guardados exitosamente.")
        else:
            print("Cambios descartados.")
            print (finalBarCode)

    # Rollback changes if any exception occurs
    except Exception as e:
        conn.rollback()  
        print("Error al realizar la operación:", e)


def newData():
    addproduct, adddescription, addbl, _= status()
    productCodeS, descriptionCodeS, blCodeS, _= selectS()

    sql_queries = [productCodeS, descriptionCodeS, blCodeS]
    results = []

    for query in sql_queries:
        cursor.execute(query)
        result = cursor.fetchone()
        if result is not None:
            results.append(result[0])
        else:
            results.append(None)

    print(results)

    currentProduct, currentDescription, currentBl = results
        
    if addproduct:
        currentProductInt = int(currentProduct, 16)
        nextProductCodeInt = currentProductInt + 1
        nextProductCodeHex = format(nextProductCodeInt, '05X')  # Asegura que tenga 5 dígitos hexadecimales
        nextProductCode = f"{nextProductCodeHex}"

    if adddescription:
        currentDescriptionInt = int(currentDescription, 16)
        nextDescriptionCodeInt = currentDescriptionInt + 1
        nextDescriptionCodeHex = format(nextDescriptionCodeInt, '05X')  # Asegura que tenga 5 dígitos hexadecimales
        nextDescriptionCode = f"{nextDescriptionCodeHex}"

    if addbl:
        currentBlInt = int(currentBl, 16)
        nextBlCodeInt = currentBlInt + 1
        nextBlCodeHex = format(nextBlCodeInt, '04X')  # Asegura que tenga 4 dígitos hexadecimales
        nextBlCode = f"{nextBlCodeHex}"

    submit()

    return nextProductCodeInt, nextProductCode, nextDescriptionCodeInt, nextDescriptionCode, nextBlCodeInt, nextBlCode, currentProduct, currentDescription, currentBl


def codeAmount():
    newBarCode, _= barCodeBuilder()
    _, _, knownBarCode, oldcode = starter()

    quantity = int(input("¿Cuantos productos identicos van a haber con este codigo?"))

    if oldcode:
        finalBarCode = f"{knownBarCode + "-" + quantity}"
    else:
        finalBarCode = f"{newBarCode + "-" + quantity}"
    
    print(finalBarCode)
    newData()

    return finalBarCode


def barCodeBuilder():
    _, nextProductCode, _, nextDescriptionCode, _, nextBlCode, _, _, _= newData()
    _, oldProductCode, addproduct = qProduct()
    _, oldDescriptionCode, adddescription = qDescription()
    _, oldBlCode, addbl = qBl()
    clientCode, _, _, _= starter()

    if addproduct:
            product = nextProductCode
    else: product = oldProductCode

    if adddescription:
            description = nextDescriptionCode
    else: description = oldDescriptionCode

    if addbl:
            bl = nextBlCode
    else: 
        bl = oldBlCode

    dateY = int(input("Ingre el año en el que quiera que figure esta carga: "))
    dateM = int(input("Ingre el mes en el que quiera que figure esta carga: "))
    dateD = int(input("Ingre la fecha en el que quiera que figure esta carga: "))
    cDate = f"{dateD + "-" + dateM + "-" + dateY}"
    dateC = dOF(dateY, dateM, dateD)

    newBarCode = f"{clientCode + "-" + product + "-" + description + "-" + bl + "-" + dateC}"
    print(newBarCode)
    
    codeAmount()

    return newBarCode, cDate


def qBl():
    _, _, addbl, _= status()

    ND = str(input("¿Quiere agregar un BL nuevo o usar uno existente? (N\\E):")).lower() == 'n'

    if ND:
        newBl = str(input("Ingrese el BL nuevo: "))
        addbl = True
        barCodeBuilder()
        return newBl
    else: 
        COW = str(input("¿Quiere buscar por codigo o Bl? (C\\B)")).lower() == 'c'

        if COW:
            oldBlCode = str(input("Ingrese el codigo del BL: "))
            queryC = "SELECT BL FROM blgen WHERE BLCODE = %s"
            cursor.execute(queryC, (oldBlCode,))
            oldBlCode = cursor.fetchone()

            conf = str(input("¿Es " + oldBlCode + "? (S\\N)")).lower() == 's'

            if conf:
                barCodeBuilder()
                return oldBlCode
            else: 
                print("No existe ese codigo, reviselo y vuelva a intentar")
                qBl()

        else: 
            oldBlW = str(input("Ingrese el BL: "))
            queryW = "SELECT BLCODE FROM blgen WHERE BL = %s"
            cursor.execute(queryW, (oldBlW,))
            oldBlCode = cursor.fetchone()

            if oldBlCode == "":
                print("No existe ese BL, reviselo y vuelva a intentar")
                qBl()
            else:
                barCodeBuilder()
                return oldBlW, oldBlCode, addbl
            
def qDescription():
    _, adddescription, _, _= status()

    ND = str(input("¿Quiere agregar una descripcion nueva o usar una existente? (N\\E):")).lower() == 'n'

    if ND:
        newDescription = str(input("Ingrese la descripcion nueva: "))
        adddescription = True
        qBl()
        return newDescription
    else:
        COW = str(input("¿Quiere buscar por codigo o descripcion? (C\\D)")).lower() == 'c'

        if COW:
            oldDescriptionCode = str(input("Ingrese el codigo de la descripcion: "))
            queryC = "SELECT DESCRIPTION FROM descriptiongen WHERE DESCRIPTIONCODE = %s"
            cursor.execute(queryC, (oldDescriptionCode,))
            oldDescriptionCode = cursor.fetchone()

            conf = str(input("¿Es " + oldDescriptionCode + " lo que buscabas? (S\\N)")).lower() == 's'

            if conf:
                qBl()
                return oldDescriptionCode
            else: 
                print("No existe ese codigo, reviselo y vuelva a intentar")
                qDescription()

        else: 
            oldDescriptionW = str(input("Ingrese la descripcion: "))
            queryW = "SELECT DESCRIPTIONCODE FROM descriptiongen WHERE DESCRIPTION = %s"
            cursor.execute(queryW, (oldDescriptionW,))
            oldDescriptionCode = cursor.fetchone()

            if oldDescriptionCode == "":
                print("No existe esa descripcion, revisela y vuelva a intentar")
                qDescription()
            else:
                qBl()
                return oldDescriptionW, oldDescriptionCode, adddescription

            
def qProduct():
    addproduct, _, _, _= status()

    NP = str(input("¿Quiere agregar un producto nuevo o usar uno existente? (N\\E):")).lower() == 'n'

    if NP:
        newProduct = str(input("Inrgrese el producto nuevo: "))
        addproduct = True
        qDescription()
        return newProduct
    else:
        COW = str(input("¿Quiere buscar por codigo o producto? (C\\P)")).lower() == 'c'

        if COW:
            oldProductCode = str(input("Ingrese el codigo del producto: "))
            queryC = "SELECT PRODUCT FROM productgen WHERE PRODUCTCODE = %s"
            cursor.execute(queryC, (oldProductCode,))
            oldProductCode = cursor.fetchone()

            conf = str(input("¿Es " + oldProductCode + " lo que buscabas? (S\\N)")).lower() == 's'

            if conf:
                qDescription()
                return oldProductCode
            else: 
                print("No existe ese codigo, reviselo y vuelva a intentar")
                qProduct()
            
        else: 
            oldProductW = str(input("Ingrese el producto: "))
            queryW = "SELECT PRODUCTCODE FROM productgen WHERE PRODUCT = %s"
            cursor.execute(queryW, (oldProductW,))
            oldProductCode = cursor.fetchone()

            if oldProductCode == "":
                print("No existe ese producto, reviselo y vuelva a intentar")
                qProduct()
            else:
                qDescription()
                return oldProductW, oldProductCode, addproduct
            

def starter():
    _, _, _, clientCodeS = selectS()
    _, _, _, oldcode = status()
    
    clientName = str(input("Enter the client name: "))

    cursor.execute(clientCodeS, (clientName,))
    clientCode = cursor.fetchone()['CLIENTCODE']

    if clientCode != "":
        org = input("¿Quiere crear un codigo nuevo o agrandar uno ya existente? (N\\E):").lower() == 'e'

        if org:
            question = str(input("¿Sabe el codigo entero? (S\\N):")).lower() =='n'

            if question:
                qProduct()
            else: 
                knownBarCode = str(input("Ingrese el codigo: "))
                oldcode = True
                codeAmount()
        else:
            qProduct()
    else:
        print("Nombre no encontrado, revise errores de ortografía e intente de nuevo o hable con un superior si es un cliente nuevo")
        starter()

    return clientCode, clientName, knownBarCode, oldcode



if __name__ == "__main__":
    starter()