import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cv2
import datetime
import io
import os
import pygame
import pygame.camera
import pyzbar.pyzbar
from PIL import Image
import SimpleCV
import time
import traceback
import re

# TODOS 4/26/18
# how do we find the latest unused row?
#     ally says (and JR agrees): write code that checks the spreadsheet (forloop until you find first empty row?)
# what happens if/when the program crashes? (RESOLVED WITH MAIN_LOOP APPROACH)
#   TODO TODO XXXXXX: TEST TO MAKE SURE THIS ACTUALLY WORKS, MAYBE MANUALLY TRIGGER AN ERROR SOMEHOW
# related: how do we _find out_ that it crashed, and how do we figure out _why_ it did that so we can improve the program?

# TODO - sometimes the barcode is scanned as a word
# TODO RELATED TO THAT: try to reproduce the bug so we can fix it!





os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/pi/Barcode/client_secret.json'

from google.cloud import vision
from google.cloud.vision import types


client = vision.ImageAnnotatorClient()

#Check pic in folder monday and then maybe separate out the names

#globalvariables
row = 2
stored_image_counter = 1

idvalue = 0
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

#find first empty row
def findfirstemptyrow():
    for i, col_value in enumerate(sheet.col_values(1)):
        if col_value == "":
            global row
            row = i + 1
            break

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
    sheet.update_cell(localrow, 1, lastname)
    sheet.update_cell(localrow, 2, firstname)
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
    # NOTE: Only call this function if we've successfully found a student ID, since it costs a tiny tiny tiny amount of money.

    # Load up the image.
    with io.open('filename.jpg', 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    # Make the API request.
    response = client.document_text_detection(image)

    if response.text_annotations:
        # Extract the name from the response.
        # `text` will look like eg 'Senators\nCURTIS FIELDS\nID# 549466\nGr\n'.
        text = response.text_annotations[0].description

        lines = text.split('\n')
        lines = lines[lines.index('Senators'):]
        name_lines = [
            line
            for line in lines
            if line.isupper()
            and not line.startswith('ID#')
            and line.lower() != 'senators'
            and len(line) > 3
            # TODO - come back and figure out how to make this more general
            and not line.startswith('JUN ')
        ]
        if name_lines and len(name_lines) == 1:
            # Sometimes this can look like 'ALEXANDRIA SHUELL O',
            # so we want to remove any extraneous numbers.
            name = name_lines[0]
            name = re.sub(r"[0-9]", "", name).strip()
            namesplit = name.split(" ")
            global lastname
            lastname = namesplit[-1]
            global firstname
            firstname = " ".join(namesplit[:-1])
            return name
        else:
            print("We didn't see anything resembling a name in {}!".format(text))
            global lastname
            lastname = "ERROR"
            global firstname
            firstname = "ERROR"
    else:
        print("Google vision API wasn't able to extract a name from this image!")
        global lastname
        lastname = "ERROR"
        global firstname
        firstname = "ERROR"


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

    

def main_loop():
    while True:
        img = takepic(cam)
        decodeid()
        if (idvalue != ""):
            # We've found an image with a barcode in it! Save the image for later analysis.
            global stored_image_counter
            img.save('saved_images/{}.jpg'.format(stored_image_counter))
            stored_image_counter += 1

            name = readname()
            if name:
                print("goog found this text in the picture: ", name)
                print("First Name: ", firstname, "Last Name: ", lastname)
            else:
                print("goog couldn't find a name in this picture")
                global lastname
                lastname = "ERROR"
                global firstname
                firstname = "ERROR"
            print("finishing hp entry")

            readentry(sheet,idvalue)
            readname()
            time.sleep(5)

        time.sleep(1)


#PROGRAM

sheet = setupgooglesheet()
cam = initializecam()
setteachername()
findfirstemptyrow()
print("row is ", row)

while True:
    try:
        main_loop()
    except Exception as e:
        # TODO - figure out how to log this to a file
        traceback.print_exc()
        with open('logfile.txt', 'a') as f:
            f.write('{}: oh no, the program crashed with this error: {}'.format(datetime.datetime.now(), e))



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
