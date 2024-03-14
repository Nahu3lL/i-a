import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import ImageDraw, Image
import pymysql
import DBpassword

found = False
file_path = 'C:/Users/NahuelADMIN/Downloads/FACA000040001342.pdf'

#connect to the database
conn = pymysql.connect(
    host='localhost',
    user='root',
    password=DBpassword.password,
    db='company_data_test',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

#checks EKS w\DB

def get_eks_info(conn):
    with conn.cursor() as cursor:
        sql = "SELECT ID, EKS FROM company_information ORDER BY ID"
        cursor.execute(sql)

        for row in cursor.fetchall():
            eks = int(row['EKS'])
            #print(f"EKS value: {eks}")
            if eks == 0:
                get_distributed_company_info(conn)
            elif eks == 1:    #this is an exception key for rotated invoices
                rotationS = True
                rotation(conn, rotationS)
                get_distributed_company_info(conn)
            elif eks == 2:
                flag = True
            else:
                print('fatal error, check Status Key')

def rotation(conn, rotationS):    #checks the direction it should rotate the image
    with conn.cursor() as cursor:
        sql = "SELECT ID, ROTATIOND FROM company_information ORDER BY ID"
        cursor.execute(sql)

    for row in cursor.fetchall():
        rotationd = row['ROTATIOND']
        if rotationS:
            if rotationd == 0:
                turn_left = True
            else:
                turn_right = True
        else: 
            print ('something went wrong, please check the code')

#compares the ocr it got with CC and saves the ID which flagged the found

def get_distributed_company_info(conn):
    global found
    found_id = None
    ocr_texts = []

    with conn.cursor() as cursor:
        sql = "SELECT ID, CUIT, CC, CCPN FROM company_information ORDER BY ID"
        cursor.execute(sql)

        for row in cursor.fetchall():
            cuit_coordinate = row['CC']
            cuit_coordinate = tuple(map(int, cuit_coordinate.split(', ')))
            cuit_page_number = row['CCPN']
            cuitpn = int(cuit_page_number) - 1
            cuit_number = row['CUIT'].strip()

            invoice = extract_images_from_pdf(file_path, turn_left=False, turn_right=False)[cuitpn]
            cropped_image = invoice.crop(cuit_coordinate)
            ocr_text = perform_ocr(cropped_image)
            ocr_texts.append(ocr_text)

            ocr_text = ocr_text.strip("[]' \n")

            if ocr_text == cuit_number:
                found = True
                found_id = row['ID']
                #print (found_id)
                invoice_data_extraction_by_id(conn, found_id)
                break

    return found_id, ocr_texts

# extract all other important values based on the ID saved

def fetch_coordinates_by_id(conn, found_id):
    with conn.cursor() as cursor:
        sql = "SELECT TVC, INC, EDC FROM company_information WHERE ID = %s"
        cursor.execute(sql, (found_id,))
        row = cursor.fetchone()
        if row:
            coordinates = {column: tuple(map(int, row[column].split(', '))) for column in row}
            return coordinates
    return None

def convert_pn_to_int_by_id(conn, found_id):
    with conn.cursor() as cursor:
        sql = "SELECT TVCPN, INCPN, EDCPN FROM company_information WHERE ID = %s"
        cursor.execute(sql, (found_id,))
        row = cursor.fetchone()
        if row:
            pn_int = {column[:-2]: int(value) - 1 for column, value in row.items()}
            return pn_int
    return None

def invoice_data_extraction_by_id(conn, found_id):
    coordinates = fetch_coordinates_by_id(conn, found_id)
    pn_int = convert_pn_to_int_by_id(conn, found_id)

    if coordinates and pn_int:
        tvc_coordinate = coordinates['TVC']
        inc_coordinate = coordinates['INC']
        edc_coordinate = coordinates['EDC']
        tvc_page_number = pn_int['TVC']
        inc_page_number = pn_int['INC']
        edc_page_number = pn_int['EDC']
        
        tvc_ocr = perform_ocr(extract_images_from_pdf(file_path, turn_left=False, turn_right=False)[tvc_page_number].crop(tvc_coordinate))
        inc_ocr = perform_ocr(extract_images_from_pdf(file_path, turn_left=False, turn_right=False)[inc_page_number].crop(inc_coordinate))
        edc_ocr = perform_ocr(extract_images_from_pdf(file_path, turn_left=False, turn_right=False)[edc_page_number].crop(edc_coordinate))
        
        #print (tvc_ocr, inc_ocr, edc_ocr)
        load_to_db(conn, tvc_ocr, inc_ocr, edc_ocr)
        return tvc_ocr, inc_ocr, edc_ocr
    
    return None

def load_to_db(conn, tvc_ocr, inc_ocr, edc_ocr):
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO global_invoices_information (value, number, expiration) VALUES (%s, %s, %s)", (tvc_ocr, inc_ocr, edc_ocr))
        conn.commit()

#image processing

def extract_images_from_pdf(file_path, turn_left=False, turn_right=False):

    if turn_left:
        images = [img.transpose(Image.ROTATE_90) for img in images]
    elif turn_right:
        images = [img.transpose(Image.ROTATE_270) for img in images]
    else:
        images = convert_from_path(file_path)

    return images


def perform_ocr(image):
    text = pytesseract.image_to_string(image)
    return text

#disconnect db 

def close_connection(conn, found):
    if found:
        conn.close()

get_eks_info(conn)