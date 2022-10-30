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
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from os.path import exists
from tkinter.scrolledtext import ScrolledText
import json
from pathlib import Path
import cutter
import glob
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
        print("here")
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
            BoilerplateInfo=st.get("1.0", tk.END)
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
    def cut_clip():
        video_file = filedialog.askopenfilename(title = "Select a WAV File",
                                          filetypes = (("video files",
                                                        "*.mkv*"),
                                                       ("all files",
                                                        "*.*")))
        name = Path(video_file).stem
        head, tail = os.path.split(video_file)
        cc=cutter.clipCutter()
        cc.set_min_clip_dur(1)
        cc.add_cut_video_to_timeline(video_file)
        cc.export_xml(os.path.join(head,name+"-cut.xml"))
        cc._cleanup()
    def cut_folder():
        folder = filedialog.askdirectory()
        
        cc=cutter.clipCutter()
        name=os.path.split(folder)[-1]
        cc.set_min_clip_dur(1)
        files=glob.glob(os.path.join(folder,"*.mkv"))
        files.sort(key=os.path.getmtime)
        for file in files:
            print(file)
            cc.add_cut_video_to_timeline(file)
        print(folder)
        print(name)
        print(os.path.join(folder,(name+"-cut.xml")))
        cc.export_xml(os.path.join(folder,(name+"-cut.xml")))
    window = Tk()
    window.title('Youtube Video Publishing Tools')
    label_file_explorer = Label(window,
                            text = "Video Prep Tools",
                            width = 20, height = 2)
    csvButton = Button(window,
                        text = "Markers to Clipboard",
                        command = findCSV,
                        width=20)
    waveButton = Button(window,
                        text = "WAV to Translation",
                        command = transcribeVid,
                        width=20)
    cut_button = Button(window,
                        text = "Cut Clip",
                        command = cut_clip,
                        width=20)
    super_cut_button = Button(window,
                        text = "Cut Folder",
                        command = cut_folder,
                        width=20)
    button_exit = Button(window,
                     text = "Exit",
                     command = exit,
                        width=20)
    lbl_entry = Label(window,
                            text = "Description Tools",
                            width = 50, height = 2)
    st = ScrolledText(window, width=75, height = 5, relief="raised")
    st.insert(tk.INSERT,BoilerplateInfo)
    label_file_explorer.grid(column = 1, row = 1, columnspan=3)
  
    
  
    waveButton.grid(column = 1, row = 2)
    cut_button.grid(column = 2, row = 2)
    super_cut_button.grid(column = 3, row = 2)
  
    lbl_entry.grid(column = 1,row =3, columnspan=3)
    st.grid(column = 1,row =4, columnspan=3)
    csvButton.grid(column = 1, row = 5,columnspan=3)
    button_exit.grid(column = 1,row = 6, columnspan=3)
        
