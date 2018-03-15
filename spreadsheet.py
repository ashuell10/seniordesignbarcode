import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
import pygame
import pygame.camera
import pyzbar.pyzbar
from PIL import Image
from tesserocr import PyTessBaseAPI

#globalvariables
row = 2

idvalue = 0
name = "tempname"
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
    sheet.update_cell(row, 4, teacher)
    sheet.update_cell(row, 5, datetime.datetime.now())

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
    print(api.GetUTF8Text())

def zero_pad_integer(integer):
    return "{:0>2d}".format(integer)

#finish the entry for hall pass
def finishhallpassentry():
    sheet.update_cell(row, 6, datetime.datetime.now())
    #TIME DURATION COLUMN
    out = sheet.cell(row, 5).value
    ins = sheet.cell(row, 6).value
    #Format numbers below 10 with padding
    exouthour = "07" #str(out[11:13])
    exoutmin = "05" #str(out[14:16])
    exinshour = "09" #str(ins[11:13])
    exinsmin = "03" #str(ins[14:16])
    #outhour
    if (exouthour[0:1] == 0):
        outhour = zero_pad_integer(int(exouthour[1:2]))
    else:
        outhour = int(exouthour)
    #outmin
    if (exoutmin[0:1] == 0):
        outmin = zero_pad_integer(int(exoutmin[1:2]))
    else:
        outmin = int(exoutmin)
    #inshour
    if (exinshour[0:1] == 0):
        inshour = zero_pad_integer(int(exinshour[1:2]))
    else:
        inshour = int(exinshour)
    #insmin
    if (exinsmin[0:1] == 0):
        insmin = zero_pad_integer(int(exinsmins[1:2]))
    else:
        insmin = int(exinsmin)
    if (insmin - outmin < 0):
        tempmindif = insmin - outmin
        mindif = 60 + tempmindif
        hourdif = (inshour - outhour) - 1
    else:
        hourdif = inshour - outhour
        mindif = insmin - outmin
        
    if (mindif >= 10):
        dif = (str(hourdif) + ":" + str(mindif))
    else:
        dif = (str(hourdif) + ":0" + str(mindif))
    sheet.update_cell(row, 7, dif)
    #print
    print("hourdif is " + str(hourdif))
    print("mindif is " + str(mindif))
    print("dif is " + str(dif))
    #LATE MINS COMLUM
    mindifnow = mindif - 10
    print("mindifnow is " + str(mindifnow))
    if (mindifnow >= 10): 
        sheet.update_cell(row, 8, (str(hourdif) + ":" + str(mindifnow)))
    elif (mindifnow <= 9 and mindifnow > 0):
        sheet.update_cell(row, 8, (str(hourdif) + ":0" + str(mindifnow)))
    elif (mindifnow == 0):
        sheet.update_cell(row, 8, (str(hourdif) + ":00"))
    else:
        if (hourdif == 0):
            sheet.update_cell(row, 8, "00:00")
        else:
            mindifnew = 60 + mindif
            hourdif = hourdif - 1
            sheet.update_cell(row, 8, (str(hourdif) + ":" + str(mindifnew)))
    # XXX jrheard look at this
    global row
    row = row + 1
    print("row is " + str(row))
    
    
# Extract and print all of the values
def listrecords():
    list_of_records = sheet.get_all_records()
    print(list_of_records)

    


#MEAT OF PROGRAM

sheet = setupgooglesheet()
print('done with google sheets stuff')
#setteachername()
print("starting hp entry")
newentry(sheet, row)
#print('taking picture')
#takepic()
#print("took picture")
#print("decoded value is", decodeid())
#readname()
#print("tesseract found this text in the picture: ", name)
print("finishing hp entry")
finishhallpassentry()
print("finished hp entry")
print("starting 2nd hp entry")
newentry(sheet, row)
print("finishing 2nd hp entry")
finishhallpassentry()
print("finished 2nd hp entry")
