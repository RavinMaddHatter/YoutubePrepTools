import csv
import pyperclip
import time
import boto3
import urllib.request
import json
import os
from botocore.exceptions import ClientError
import uuid
import sys
from importlib.machinery import SourceFileLoader
import requests
from tkinter import *
from tkinter import filedialog
from os.path import exists
import json
confFile="youtubeDescription.json"
def updateSave():
    data={}
    data["boilerplate"]=BoilerplateInfo
    with open(confFile,"w+") as file:
        json.dump(data,file, indent=2)
if exists(confFile):
    with open(confFile) as file:
        data=json.load(file)
        BoilerplateInfo=data["boilerplate"]
else:
    print("no config file found setting defaults")
    BoilerplateInfo="temp boilerplate links and such"
    updateSave()
    
    
    


class translator:
    def __init__(self,s3Bucket="audioprocessing",profile="default"):
        self.s3Bucket=s3Bucket
        self.session = boto3.Session(profile_name=profile)
        self.transcribe_client = self.session.client('transcribe')
        self.s3_client = self.session.client('s3')
    def audioToText(self,fileName):
        print("uploading file")
        obj_name=self.uploadFile(fileName)
        job_name=str(uuid.uuid4())
        url="s3://{}/{}".format(self.s3Bucket,obj_name)
        name, extension = os.path.splitext(fileName)
        self.handle=self.transcribe(job_name,url)
        self.jsonTranslate=json.loads(requests.get(self.handle).content.decode('ascii'))
        with open(name+"_raw_translation.json","w+") as file:
            json.dump(self.jsonTranslate,file)
        self.text=self.jsonTranslate["results"]["transcripts"][0]["transcript"]
        
        
        
        with open(name+".txt", "w+") as text_file:
            text_file.write(self.text)
        self.deleteFile(obj_name)
    def uploadFile(self,fileName,object_name=None):
        if object_name is None:
            object_name = os.path.basename(fileName)
        try:
            response = self.s3_client.upload_file(fileName, self.s3Bucket, object_name)
        except ClientError as e:
            logging.error(e)
            return "FAILED"
        return object_name
    def deleteFile(self, filename):
        try:
            self.s3_client.delete_object(Bucket = self.s3Bucket, Key = filename)
        except ClientError as e:
            logging.error(e)
            return False
        return True
    def transcribe(self,job_name, file_uri):
        self.transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': file_uri},
            MediaFormat='wav',
            LanguageCode='en-US'
        )

        max_tries = 360
        while max_tries > 0:
            max_tries -= 1
            job = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = job['TranscriptionJob']['TranscriptionJobStatus']
            if job_status in ['COMPLETED', 'FAILED']:
                print(f"Job {job_name} is {job_status}.")
                
                if job_status == 'COMPLETED':
                    return job['TranscriptionJob']['Transcript']['TranscriptFileUri']
                break
            else:
                print(f"Waiting for {job_name}. Current status is {job_status}.")
            time.sleep(10)







class markerProcessor:
    def __init__(self,file):
        self.markers=[]
        with open(file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                time=row["Source In"].split(":")
                time[0]=int(time[0])-1
                if time[0]==0:
                    time.pop(0)
                else:
                    time[0]="{:02d}".format(time[0])
                time.pop()
                time=":".join(time)
                
                self.markers.append(time+" "+row["Notes"])
    def stringToClipboard(self):
        pyperclip.copy(BoilerplateInfo+"\n\r".join(self.markers))
    def stringToFile(self,name):
        with open(name, "w+") as text_file:
            text_file.write("\n\r".join(self.markers))
        

if __name__=="__main__":
    def findCSV():
        filename = filedialog.askopenfilename(title = "Select a CSV File",
                                          filetypes = (("CSV files",
                                                        "*.CSV*"),
                                                       ("all files",
                                                        "*.*")))
        try:
            mk=markerProcessor(filename)
            mk.stringToClipboard()
            print("markers in clipboard")
        except:
            print("Failed")
    def transcribeVid():
        filename = filedialog.askopenfilename(title = "Select a WAV File",
                                          filetypes = (("WAV files",
                                                        "*.WAV*"),
                                                       ("all files",
                                                        "*.*")))
        try:
            trans=translator()
            trans.audioToText(filename)
            print("Finished")
        except:
            print("failed translation")
    window = Tk()
    window.title('Quick Fixer for youtube prep')
    label_file_explorer = Label(window,
                            text = "Youtube Processors",
                            width = 50, height = 2,
                            fg = "blue")
    csvButton = Button(window,
                        text = "CSV to markers",
                        command = findCSV)
    waveButton = Button(window,
                        text = "WAV to Translation",
                        command = transcribeVid)
    button_exit = Button(window,
                     text = "Exit",
                     command = exit)
    label_file_explorer.grid(column = 1, row = 1,columnspan=3)
  
    csvButton.grid(column = 1, row = 2,columnspan=3)
  
    waveButton.grid(column = 1, row = 3, columnspan=3)
  
    button_exit.grid(column = 1,row = 4, columnspan=3)
        
