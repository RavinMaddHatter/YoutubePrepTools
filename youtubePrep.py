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
import win32gui
import re
import keyboard
import time
confFile="youtubeDescription.json"
def updateSave(in_space, out_space,min_silent, min_clip):
    data={}
    data["boilerplate"]=BoilerplateInfo
    data["in_space"]=in_space
    data["out_space"]=out_space
    data["min_clip"]=min_clip
    data["min_silent"]=min_silent
    with open(confFile,"w+") as file:
        json.dump(data,file, indent=2)
if exists(confFile):
    with open(confFile) as file:
        data=json.load(file)
        BoilerplateInfo=data["boilerplate"]
else:
    print("no config file found setting defaults")
    data={}
    BoilerplateInfo="temp boilerplate links and such"
    updateSave(0.05, 0.05,0.1, 1)
    
    
    


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
    default_level=-24
    class WindowMgr:
        """Encapsulates some calls to the winapi for window management"""

        def __init__ (self):
            """Constructor"""
            self._handle = None

        def find_window(self, class_name, window_name=None):
            """find a window by its class_name"""
            self._handle = win32gui.FindWindow(class_name, window_name)

        def _window_enum_callback(self, hwnd, wildcard):
            """Pass to win32gui.EnumWindows() to check all the opened windows"""
            if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
                self._handle = hwnd

        def find_window_wildcard(self, wildcard):
            """find a window whose title matches the wildcard regex"""
            self._handle = None
            win32gui.EnumWindows(self._window_enum_callback, wildcard)

        def set_foreground(self):
            """put the window in the foreground"""
            win32gui.SetForegroundWindow(self._handle)
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

    def fix_audio():
        w = WindowMgr()
        w.find_window_wildcard(".*DaVinci Resolve.*")
        w.set_foreground()
        time.sleep(0.1)
        for i in range(num_clips.get()):
            keyboard.press_and_release('f')
            time.sleep(0.05)
            keyboard.press_and_release('f10')
            time.sleep(0.1)
    def do_settings(cc):
        levels=[]
        chans=[]
        for i in range(len(sliders)):
            levels.append(-sliders[i].get())
            chans.append(slider_chks[i].get()==1)
        cc.set_multi_chan_thres(levels)
        cc.set_lead_in(lead_in.get())
        cc.set_lead_out(lead_out.get())
        cc.set_min_clip_dur(clip_dur.get())
        cc.set_enabled_tracks(chans)
        cc.set_min_silent_dur(min_silent_dur_var.get())
    def cut_clip():
        video_file = filedialog.askopenfilename(title = "Select a WAV File",
                                          filetypes = (("video files",
                                                        "*.mkv*"),
                                                       ("all files",
                                                        "*.*")))
        name = Path(video_file).stem
        head, tail = os.path.split(video_file)
        cc=cutter.clipCutter()
        do_settings(cc)
        cc.add_cut_video_to_timeline(video_file)
        cc.export_xml(os.path.join(head,name+"-cut.xml"))
        num_clips.set(len(cc.clips))
        cc._cleanup()
    def cut_folder():
        folder = filedialog.askdirectory()
        cc=cutter.clipCutter()
        name=os.path.split(folder)[-1]
        do_settings(cc)
        files=glob.glob(os.path.join(folder,"*.mkv"))
        files.sort(key=os.path.getmtime)
        print("cutting files:")
        for file in files:
            print(file)
            cc.add_cut_video_to_timeline(file)
        print("combined file")
        print(os.path.join(folder,(name+"-cut.xml")))
        cc.export_xml(os.path.join(folder,(name+"-cut.xml")))
        num_clips.set(len(cc.clips))
        cc._cleanup()
    def save():
        updateSave(lead_in.get(), lead_out.get(),min_silent_dur_var.get(), clip_dur.get())
    def exit():
        window.destroy()
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
    fix_audio_button = Button(window,
                        text = "Fix Audio Tracks",
                        command = fix_audio,
                        width=20)
    button_exit = Button(window,
                     text = "Exit",
                     command = exit,
                        width=20)
    
    button_save = Button(window,
                     text = "Save",
                     command = save,
                        width=20)
    lbl_entry = Label(window,
                            text = "Description Tools",
                            width = 50, height = 2)
    st = ScrolledText(window, width=75, height = 5, relief="raised")
    st.insert(tk.INSERT,BoilerplateInfo)
    audioChans=6
    sliders=[]
    sliders_lb=[]
    sliders_ch=[]
    slider_chks=[]
    for i in range(audioChans):
        sliders_lb.append(Label(window,
                            text = "ch {}".format(i+1),
                             height = 2))
        sliders.append(Scale(window, from_=0, to=-50))
        sliders[i].set(default_level)
        slider_chks.append(IntVar())
        slider_chks[i].set(0)
        sliders_ch.append(Checkbutton(window,variable=slider_chks[i]))
    slider_chks[0].set(1)
    num_clips=IntVar()
    num_clips_ent=Entry(window,textvariable=num_clips, width=10)
    lead_in=DoubleVar()
    
    ld_in_ent=Entry(window,textvariable=lead_in, width=10)
    in_lb = Label(window,text = "In Space",width = 15, height = 2)
    lead_out=DoubleVar()
    
    ld_out_ent=Entry(window,textvariable=lead_out, width=10)
    out_lb = Label(window,text = "Out Space",width = 15, height = 2)
    clip_dur=DoubleVar()
    clip_dur_ent=Entry(window,textvariable=clip_dur, width=10)
    dur_lb = Label(window,text = "Min Clip Length",width = 15, height = 2)
    min_silent_dur_var=DoubleVar()
    min_silent_dur_ent=Entry(window,textvariable=min_silent_dur_var, width=10)
    silent_lb = Label(window,text = "Min Silent Dur",width = 15, height = 2)
    lead_in.set(data["in_space"])
    lead_out.set(data["out_space"])
    clip_dur.set(data["min_clip"])
    min_silent_dur_var.set(data["min_silent"])
    row=1
    label_file_explorer.grid(column = 1, row = row, columnspan=audioChans)
    auto_clicker = Label(window,text = "Fix Davinci",width = 15, height = 2)
    row+=1
  
    waveButton.grid(column = 1, row = row,columnspan=2)
    cut_button.grid(column = 3, row = row,columnspan=2)
    super_cut_button.grid(column = 5, row = row,columnspan=2)
    row+=1
    for i in range(len(sliders)):
        sliders_lb[i].grid(column = i+1,row =row)
        sliders[i].grid(column = i+1,row =row+1)
        sliders_ch[i].grid(column = i+1,row =row+2)
    row+=3
    in_lb.grid(column = 1,row =row)
    out_lb.grid(column = 2,row =row)
    dur_lb.grid(column = 3,row =row)
    silent_lb.grid(column = 4,row =row)
    row+=1
    ld_in_ent.grid(column = 1,row =row)
    ld_out_ent.grid(column = 2,row =row)
    clip_dur_ent.grid(column = 3,row =row)
    min_silent_dur_ent.grid(column = 4,row =row)
    row+=1
    auto_clicker.grid(column = 1,row =row, columnspan=audioChans)
    row+=1
    num_clips_ent.grid(column = 1,row =row)
    fix_audio_button.grid(column = 2,row =row, columnspan=5)
    row+=1
    lbl_entry.grid(column = 1,row =row, columnspan=audioChans)
    row+=1
    st.grid(column = 1,row =row, columnspan=audioChans)
    row+=1
    csvButton.grid(column = 1, row = row,columnspan=audioChans)
    row+=1
    button_save.grid(column = 1, row = row)
    button_exit.grid(column = 2,row = row, columnspan=audioChans-1)
    window.mainloop()
