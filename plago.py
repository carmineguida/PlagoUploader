################################################################################
# plago.py - Originally coded by: Carmine T. Guida
################################################################################

import os
import sys
import requests
import csv
import urllib
import time
import base64

import tarfile
import zipfile

base = "https://gatech.instructure.com"

token = ""
canvasProfile = {}
canvasCourses = []
canvasCourseUsers = []
canvasCourseAssignments = []
courseAssignmentSubmissions = []
course = ""
assignment = ""

course_name = ""
assignment_name = ""

plago_base = "http://plago.cc.gatech.edu/api/"
plago_apikey = ""
plago_batch_id = ""

################################################################################

def PlagoAPIPost(url, params):
    global base
    global token
    global perPage

    headers = {"Authorization": "Bearer " + plago_apikey}
    response = requests.post(plago_base + url, headers=headers, json=params)

    if (response.status_code != requests.codes.ok):
        print("ERROR HTTP STATUS CODE: " + str(response.status_code))
    else:
        #print (response.text)
        result = response.json()
        status = result["status"]
        if (status == "fatal"):
            print("PlagoAPIPost: A fatal error occurred.")
            exit();
        if (status == "error"):
            print("PlagoAPIPost: ERROR " + result["message"])
            exit();
        return result["data"]

def PlagoBatchAdd(source, source_course_id, source_course_name, source_assignment_id, source_assignment_name):
    global plago_batch_id
    params = {
        "source":source,
        "source_course_id":source_course_id,
        "source_course_name":source_course_name,
        "source_assignment_id":source_assignment_id,
        "source_assignment_name":source_assignment_name
    }

    data = PlagoAPIPost("batch_add", params)
    plago_batch_id = data["id"]

def PlagoBatchEntryAdd(batch_id, source_user_id, source_user_name, data):
    data_base64 = base64.b64encode(data).decode("utf-8")
    params = {
        "batch_id":batch_id,
        "source_user_id":source_user_id,
        "source_user_name":source_user_name,
        "data_base64": data_base64
    }

    PlagoAPIPost("batchentry_add", params)

def PlagoBatchQueue(id):
    params = {
        "id":id
    }

    PlagoAPIPost("batch_queue", params)



################################################################################

def CanvasAPIGet(url):
    global base
    global token
    global perPage

    pageNum = 1

    headers = {"Authorization": "Bearer " + token}

    current = url
    if (current.startswith(base) == False):
        current = base + url
    responseList = []

    while True:
        params = {"page":str(pageNum), "per_page":"100"}
        response = requests.get(current, headers=headers, params=params)

        if (response.status_code != requests.codes.ok):
            print("ERROR HTTP STATUS CODE: " + str(response.status_code))
        else:
            #print("")
            #print("[" + current + "]")
            #print (response.text)
            result = response.json()
            if (isinstance(result, dict)):
                return result
            responseList.extend(result)
            linkCurrent = response.links["current"]
            linkLast = response.links["last"]

            if (linkCurrent["url"] == linkLast["url"]):
                return responseList
            pageNum += 1


def CanvasAPIPut(url, params):
    global base
    global token
    global perPage

    headers = {"Authorization": "Bearer " + token}

    response = requests.put(base + url, headers=headers, data=params)

    if (response.status_code != requests.codes.ok):
        print("ERROR HTTP STATUS CODE: " + str(response.status_code))
    else:
        #print (response.text)
        return response.json()

def CanvasAPIPost(url, params):
    global base
    global token
    global perPage

    headers = {"Authorization": "Bearer " + token}

    response = requests.post(base + url, headers=headers, data=params)

    if (response.status_code != requests.codes.ok):
        print("ERROR HTTP STATUS CODE: " + str(response.status_code))
    else:
        #print (response.text)
        return response.json()

################################################################################

def GetProfile():
    global canvasProfile
    canvasProfile = CanvasAPIGet("/api/v1/users/self/profile")

def GetCourses():
    global canvasCourses
    canvasCourses = CanvasAPIGet("/api/v1/courses")

def GetCourseUsers():
    global canvasCourseUsers
    global course
    canvasCourseUsers = CanvasAPIGet("/api/v1/courses/" + course + "/users")

def GetCourseAssignments():
    global canvasCourseAssignments
    global course
    canvasCourseAssignments = CanvasAPIGet("/api/v1/courses/" + course + "/assignments")

def GetCourseAssignmentSubmissions():
    global courseAssignmentSubmissions
    global course
    global assignment
    courseAssignmentSubmissions = CanvasAPIGet("/api/v1/courses/" + course + "/assignments/" + assignment + "/submissions")

################################################################################

def PromptToken():
    global token
    print("What is your Canvas Token?")
    print("Found in: Canvas > Account > Settings > Approved Integrations: > New Access Token.")
    while len(token) <= 0:
        token = str(input(":")).strip()

def PromptCourse():
    global canvasCourses
    global course
    print("Which Course?")
    for entry in canvasCourses:
        print(str(entry["id"]) + " " + entry["name"])

    print("Type \"all\" to process each course in which you are a TA/instructor.")
    while len(course) <= 0:
        course = str(input(":")).strip()

def PromptAssignment():
    global canvasCourseAssignments
    global assignment
    print("Which Assignment?")
    for entry in canvasCourseAssignments:
        print(str(entry["id"]) + " " + entry["name"])

    print ("Type \"all\" to import submissions from all assignments.")
    while len(assignment) <= 0:
        assignment = str(input(":")).strip()

def FindCourse(id):
    global canvasCourses
    for entry in canvasCourses:
        if (int(entry["id"]) == int(id)):
            return entry
    return None

def FindAssignment(id):
    global canvasCourseAssignments
    for entry in canvasCourseAssignments:
        if (int(entry["id"]) == int(id)):
            return entry
    return None

def FindSubmissionByUser(user):
    global courseAssignmentSubmissions
    user_id = user["id"]
    for entry in courseAssignmentSubmissions:
        if (entry["user_id"] == user_id):
            return entry
    return None


def PromptCourseName():
    global course_name
    print("What is the name of the course (ex: CS1701 The Second Prize)?")
    while len(course_name) <= 0:
        course_name = str(input(":")).strip()

def PromptAssignmentName():
    global assignment_name
    print("What is the name of the assignment (ex: A2)?")
    while len(assignment_name) <= 0:
        assignment_name = str(input(":")).strip()

################################################################################

def ProcessAllCourses():
    global canvasCourses
    global course

    for entry in canvasCourses:
        course = str(entry["id"])
        ProcessCourse()

def ProcessCourse():
    global course
    global assignment

    currentCourse = FindCourse(course)
    print ("\nProcessing Course: " + currentCourse["name"])

    enrollments = currentCourse["enrollments"]
    if (len(enrollments) > 0):
        enrollment = enrollments[0]
        if (enrollment["type"] == "student"):
            print ("Skipping (role = student)")
            return

    GetCourseUsers()

    GetCourseAssignments()

    PromptAssignment()

    if (assignment.lower() == "all"):
        ProcessAllAssignments()
    else:
        ProcessAssignment()

################################################################################

def ProcessAllAssignments():
    global canvasCourseAssignments
    global assignment
    for entry in canvasCourseAssignments:
        assignment = str(entry["id"])
        ProcessAssignment()

def ProcessAssignment():
    global course
    global assignment
    global canvasCourseUsers
    global courseAssignmentSubmissions
    global plago_batch_id

    currentCourse = FindCourse(course)
    currentAssignment = FindAssignment(assignment)

    print ("\nProcessing Assignment: " + currentAssignment["name"])

    print("Fetching list of submissions.")
    GetCourseAssignmentSubmissions()

    if (len(courseAssignmentSubmissions) <= 0):
        print("No assignments submitted.")
        return

    print("Adding CanvasBatch to Plago.")
    PlagoBatchAdd(1, currentCourse["id"], currentCourse["name"], currentAssignment["id"], currentAssignment["name"]) # 1 = Canvas
    print("id: " + str(plago_batch_id))

    for user in canvasCourseUsers:
        submission = DownloadSubmissionByUser(user)
        if (submission is None):
            continue

        print("Adding: " + user["sortable_name"] + " (" + str(len(submission)) + " bytes)")
        PlagoBatchEntryAdd(plago_batch_id, user["id"], user["sortable_name"], submission)

    print("\nQueuing Batch")
    PlagoBatchQueue(plago_batch_id)


def DownloadSubmissionByUser(user):
    submission = FindSubmissionByUser(user)

    if (submission is None):
        return None

    if ("attachments" not in submission):
        return None

    attachments = submission["attachments"]

    final_url = ""
    for attachment in attachments:
        url = attachment["url"]
        if (url == ""):
            continue
        final_url = url

    if (final_url == ""):
        return None

    response = requests.get(final_url)
    return response.content

################################################################################

def Canvas():
    global token
    global course
    global assignment

    PromptToken()

    GetProfile()
    print("Hello, " + canvasProfile["name"])

    GetCourses()

    PromptCourse()

    if (course.lower() == "all"):
        ProcessAllCourses()
    else:
        ProcessCourse()

################################################################################

def TsquareProcessArchive(pdfs):
    global plago_batch_id

    for name in pdfs:
        values = name.split("/")
        temp = values[2].split("(")
        user_name = temp[0]
        user_id = temp[1].replace(")", "")
        print(user_name)
        print ("Extracting...")
        data = archive.read(name)
        print ("Uploading...")
        PlagoBatchEntryAdd(plago_batch_id, user_id, user_name, data)

def Tsquare(filename):
    PromptCourseName()

    print("Opening: " + filename)

    archive = zipfile.ZipFile(filename, "r")
    files = archive.namelist()
    pdfs = []
    for name in files:
        if (name.lower().endswith(".pdf") and "Submission attachment" in name):
            pdfs.append(name)

    count = len(pdfs)
    if (count <= 0):
        print("No pdfs were found.")

    print(str(count) + " pdfs found!")

    sample = pdfs[0].split("/")

    assignment_name = sample[1]

    print("Assignment: " + assignment_name)

    print("Adding TsquareBatch to Plago.")
    PlagoBatchAdd(2, course_name, assignment_name)  # 2 = tsquare
    print("id: " + str(plago_batch_id))

    TsquareProcessArchive(pdfs)

    print("\nQueuing Batch")
    PlagoBatchQueue(plago_batch_id)

################################################################################

def Tony(filename):
    global course_name
    global assignment_name

    PromptCourseName()
    PromptAssignmentName()

    print("Adding TsquareBatch to Plago.")
    PlagoBatchAdd(10, "", course_name, "", assignment_name)  # 10 = custom
    print("id: " + str(plago_batch_id))

    print("Opening: " + filename)
    tar = tarfile.open(filename, "r:gz")
    for member in tar.getmembers():
        if (member.isfile() == False):
            continue
        values = member.name.split("/")
        temp = values[5].split("(")
        user_name = temp[0]
        user_id = temp[1].replace(")", "")
        print(user_name)
        print ("  Extracting...")
        f = tar.extractfile(member)
        if f is None:
            print ("ERROR: Could not read " + member.name)
            continue
        data = f.read()
        print ("  Uploading...")
        PlagoBatchEntryAdd(plago_batch_id, user_id, user_name, data)
        
    print("\nQueuing Batch")
    PlagoBatchQueue(plago_batch_id)

################################################################################

def ProcessMenuOption(option):
    command = ""
    filename = ""
    otherfile = ""
    options = option.split();

    if (len(options) > 0):
        command = options[0].strip().lower()

    if (len(options) > 1):
        filename = options[1].strip()

    if (len(options) > 2):
        otherfile = options[2].strip()

    if (command == "quit" or command == "exit"):
        quit()

    if (command == "canvas"):
        Canvas()
        quit()

    if (command == "tsquare"):
        Tsquare(filename)
        quit()

    if (command == "tony"):
        Tony(filename)
        quit()

def PromptMenu():
    print("Which type of import?")
    print("> canvas")
    print("> tsquare filename.zip")
    print("> tony filename.tar.gz")

    while True:
        option = ""
        while len(option) <= 0:
            option = str(input(":")).strip()
        ProcessMenuOption(option)

################################################################################

def main():
    global token
    global plago_apikey

    if (len(sys.argv) < 2):
        print("usage: plago plago_apikey")
        return

    plago_apikey = sys.argv[1]

    PromptMenu()

    print("\nDone!\n")

################################################################################

main()
