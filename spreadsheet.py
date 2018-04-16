import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cv2
import datetime
import os
import pygame
import pygame.camera
import pyzbar.pyzbar
from PIL import Image
from tesserocr import PyTessBaseAPI
import SimpleCV
import time

#globalvariables
row = 2
stored_image_counter = 1

idvalue = 0
name = "tempname"
firstname = "first"
lastname = "last"
teacher = "teacher"

currentlysignedoutstudents = []

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
    sheet.update_cell(1, 5, "Reason")
    sheet.update_cell(1, 6, "Time Out")
    sheet.update_cell(1, 7, "Time In")
    sheet.update_cell(1, 8, "Time (Duration)")
    sheet.update_cell(1, 9, "Late Minutes")
    
    return sheet

#initialize Camera
def initializecam():
    cam = SimpleCV.Camera()

    return cam

#set the teachers name
def setteachername():
    global teacher
    while True:
        teach = raw_input("Enter Teacher Name: ")
        answer = raw_input("Is " + teacher + " correct? YES or NO?: ")
        if answer.lower() == "yes":
            teacher = teach
            break

def find_id_in_signed_out_students(idvalue):
    for i, entry in enumerate(currentlysignedoutstudents):
        if entry['id'] == idvalue:
            return i

    return -1

#read the entry and see if the student is already signed out
def readentry(sheet, idvalue):
    relevant_signed_out_row = None
    
    signed_out_index = find_id_in_signed_out_students(idvalue)
    if signed_out_index > -1:
        relevant_signed_out_row = currentlysignedoutstudents[signed_out_index]

    if relevant_signed_out_row:
        finishhallpassentry(relevant_signed_out_row['row'], relevant_signed_out_row['id'])
    else:
        newentry(sheet, row)

#make a new entry and give reason
def newentry(sheet, localrow):
    sheet.update_cell(localrow, 1, firstname)
    sheet.update_cell(localrow, 2, lastname)
    sheet.update_cell(localrow, 3, idvalue)
    sheet.update_cell(localrow, 4, teacher)
    #comment out for prototype
    """while True:
        reason = raw_input("Enter Reason: ")
        answer = raw_input("Is " + reason + " correct? YES or NO?: ")
        if answer.lower() == "yes":
            break"""
    #added lines
    reason = "BR"
    #continue rest of program
    sheet.update_cell(localrow, 5, reason)
    sheet.update_cell(localrow, 6, datetime.datetime.now())
    #add to currently signed out students
    currentlysignedoutstudents.append({'id' : idvalue, 'row' : localrow})
    #get ready for the next entry and increase row
    global row
    # TODO this doesn't seem to get run more than one time - row is always 3
    row = row + 1
    print("row is " + str(row))

#find what camera is called
def find_camera_path():
    filename = [x for x in os.listdir('/dev/') if x.startswith('video')][0]
    return '/dev/' + filename

#take a pic
def takepic(cam):
    print('taking a picture!')
    img = cam.getImage()
    img.save("filename.jpg")
    return img

#decode the pic for id value
def decodeid():
    image = cv2.imread('filename.jpg')
    newidvalue = str(pyzbar.pyzbar.decode(image))
    
    global idvalue
    idvalue = newidvalue[15:21]
    return idvalue

#decode the pic for a name
def readname():
    api = PyTessBaseAPI()
    api.SetImageFile('filename.jpg')
    #stripoutname
    read = api.GetUTF8Text()
    print(read)
    """identify =
    fbegin =
    fend =
    space = 
    ebegin =
    eend=
    for letters in read:
        if (letter == identify):
            begin =
        if (letter == space
            end ="""
    

def zero_pad_integer(integer):
    return "{:0>2d}".format(integer)

#finish the entry for hall pass
def finishhallpassentry(row, idvalue):
    sheet.update_cell(row, 7, datetime.datetime.now())
    #TIME DURATION COLUMN
    out = sheet.cell(row, 6).value
    ins = sheet.cell(row, 7).value
    #Format numbers below 10 with padding
    exouthour = str(out[11:13])
    exoutmin = str(out[14:16])
    exinshour = str(ins[11:13])
    exinsmin = str(ins[14:16])
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
    sheet.update_cell(row, 8, dif)
    #print
    print("hourdif is " + str(hourdif))
    print("mindif is " + str(mindif))
    print("dif is " + str(dif))
    #LATE MINS COMLUM
    mindifnow = mindif - 10
    print("mindifnow is " + str(mindifnow))
    if (mindifnow >= 10): 
        sheet.update_cell(row, 9, (str(hourdif) + ":" + str(mindifnow)))
    elif (mindifnow <= 9 and mindifnow > 0):
        sheet.update_cell(row, 9, (str(hourdif) + ":0" + str(mindifnow)))
    elif (mindifnow == 0):
        sheet.update_cell(row, 9, (str(hourdif) + ":00"))
    else:
        if (hourdif == 0):
            sheet.update_cell(row, 9, "00:00")
        else:
            mindifnew = 60 + mindif
            hourdif = hourdif - 1
            sheet.update_cell(row, 9, (str(hourdif) + ":" + str(mindifnew)))
    #remove the entry in signed out students
    index = find_id_in_signed_out_students(idvalue)
    currentlysignedoutstudents.pop(index)
    
    
# Extract and print all of the values
def listrecords():
    list_of_records = sheet.get_all_records()
    print(list_of_records)

    

#PROGRAM

sheet = setupgooglesheet()
cam = initializecam()
setteachername()
while True:
    img = takepic(cam)
    decodeid()
    if (idvalue != ""):
        # We've found an image with a barcode in it! Save the image for later analysis.
        img.save('saved_images/{}.jpg'.format(stored_image_counter))
        stored_image_counter += 1

        readentry(sheet,idvalue)
        readname()
        time.sleep(5)

    time.sleep(1)


"""sheet = setupgooglesheet()
cam = initializecam()
print('done with google sheets stuff')
setteachername()
print("starting read entry: 1st time")
takepic(cam)
print("took picture")
print("decoded value is", decodeid())
readentry(sheet, idvalue)
print(row)
raw_input("Ready?")
print("reading id again : 2nd time")
takepic(cam)
print("took picture")
print("decoded value is", decodeid())
readentry(sheet, idvalue)
print(row)
raw_input("Ready?")
print("reading id again: 3rd time")
takepic(cam)
print("took picture")
print("decoded value is", decodeid())
readentry(sheet, idvalue)
print(row)
raw_input("Ready?")
print("reading id again: 4th time")
takepic(cam)
print("took picture")
print("decoded value is", decodeid())
readentry(sheet, idvalue)
print(row)"""


"""readname()
print("tesseract found this text in the picture: ", name)
print("finishing hp entry")"""
