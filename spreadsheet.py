import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
import pygame
import pygame.camera
import pyzbar.pyzbar
from PIL import Image
from tesserocr import PyTessBaseAPI

#look up how to make a spreadsheet instance

#globalvariables
row = 2

idvalue = 0
firstname = "first"
lastname = "last"
teacher = "teacher"

#sets up google sheet stuff
def setupgooglesheet():
    print('program start')

    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("Python Test (Hall Pass)").sheet1


    #Set Up Sheet
    sheet.update_cell(1, 1, "Student's(Last name)")
    sheet.update_cell(1, 2, "Student's(First name)")
    sheet.update_cell(1, 3, "Student's(ID's)")
    sheet.update_cell(1, 4, "Teachers")
    sheet.update_cell(1, 5, "Time Out")
    sheet.update_cell(1, 6, "Time In")
    sheet.update_cell(1, 7, "Time (Duration)")
    sheet.update_cell(1, 8, "Late Minutes")

    print('done messing around with google sheets stuff')

    return sheet

#set the teachers name
def setteachername():
    while True:
        teacher = raw_input("Enter Teacher Name: ")
        answer = raw_input("Is " + teacher + " correct? YES or NO?: ")
        if answer.lower() == "yes":
            break

#make a new entry
def newentry(sheet, row):
    sheet.update_cell(row, 1, firstname)
    sheet.update_cell(row, 2, lastname)
    sheet.update_cell(row, 3, idvalue)
    sheet.update_cell(row, 3, teacher)
    sheet.update_cell(row, 4, datetime.datetime.now())

def find_camera_path():
    filename = [x for x in os.listdir('/dev/') if x.startswith('video')][0]
    return '/dev/' + filename

#take a pic
def takepic():
    pygame.camera.init()
    path = find_camera_path()
    cam = pygame.camera.Camera(path, (640,480))
    cam.start()
    img = cam.get_image()
    pygame.image.save(img,"filename.jpg")

#decode the pic for id value
def decodeid():
    idvalue = pyzbar.pyzbar.decode(Image.open('filename.jpg'))
    return idvalue

#decode the pic for a name
def readname():
    api = PyTessBaseAPI()
    api.SetImageFile('filename.jpg')
    name = api.GetUTF8Text()

#finish the entry for hall pass
def finishhallpassentry():
    sheet.update_cell(row, 5, datetime.datetime.now())
    dif = (sheet.cell(row, 4).value - sheet.cell(row, 5).value)
    sheet.update_cell(row, 6, dif)
    row += 1
    

# Extract and print all of the values
def listrecords():
    list_of_records = sheet.get_all_records()
    print(list_of_records)

#MEAT OF PROGRAM

sheet = setupgooglesheet()
#setteachername()
#print("starting entry")
newentry(sheet, row)
print('taking picture')
takepic()
print("took picture")
print("decoded value is", decodeid())
#readname()
#print("tesseract found this text in the picture: ", api.GetUTF8Text())
