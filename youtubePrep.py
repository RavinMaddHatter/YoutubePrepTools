from csv import DictReader
from pyperclip import copy
import openai_translator as Translator
import json
import requests
import os
import tkinter as tk
from tkinter import *
from tkinter import filedialog
from os.path import exists
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import cutter
import glob
import re
confFile="youtubeDescription.json"
data=None
BoilerplateInfo=None
slider_defaults = None
sliders_enabled = None
audioChans=6
translator=Translator.translator
def updateSave(in_space, out_space,min_silent, min_clip):
    data={}
    data["boilerplate"]=BoilerplateInfo
    data["in_space"]=in_space
    data["out_space"]=out_space
    data["min_clip"]=min_clip
    data["min_silent"]=min_silent
    data["sliders_enabled"]=sliders_enabled
    data["slider_defaults"]=slider_defaults
    
    with open(confFile,"w+") as file:
        json.dump(data,file, indent=2)
if exists(confFile):
    with open(confFile) as file:
        data = json.load(file)
        BoilerplateInfo = data["boilerplate"]
        
        print("loaded sliders")
        sliders_enabled = data["sliders_enabled"]
        slider_defaults = data["slider_defaults"]
        print(sliders_enabled)

if BoilerplateInfo == None:
    BoilerplateInfo="Default Test For Your Youtube Description/n"
if slider_defaults == None:
    slider_defaults = []
    sliders_enabled = []
    for i in range(audioChans):
        slider_defaults.append(-24)
        sliders_enabled.append(True)
if data == None:
    data={}
    updateSave(0.1, 0.1,0.1, 1)
    data["in_space"]=0.1
    data["out_space"]=0.1
    data["min_clip"]=1
    data["min_silent"]=0.1
    

class markerProcessor:
    def __init__(self,file):
        self.markers=[]
        with open(file, newline='') as csvfile:
            reader = DictReader(csvfile, delimiter=',')
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
        copy(BoilerplateInfo+"\n\r".join(self.markers))
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
        except Exception as e:
            print("failed translation")
            print(e)

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
        cc.export_edl(os.path.join(head,name+"-cut.edl"))
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
        print(os.path.join(folder,(name+"-cut.edl")))
        cc.export_edl(os.path.join(folder,(name+"-cut.edl")))
        cc._cleanup()
    def save():
        for i in range(audioChans):
            slider_defaults[i] = sliders[i].get()
            sliders_enabled[i] = slider_chks[i].get()
            
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
    
    sliders=[]
    sliders_lb=[]
    sliders_ch=[]
    slider_chks=[]
    for i in range(audioChans):
        sliders_lb.append(Label(window,
                            text = "ch {}".format(i+1),
                             height = 2))
        sliders.append(Scale(window, from_=0, to=-50))
        sliders[i].set(slider_defaults[i])
        slider_chks.append(IntVar())
        slider_chks[i].set(sliders_enabled[i])
        sliders_ch.append(Checkbutton(window,variable=slider_chks[i]))
    slider_chks[0].set(1)
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
    lbl_entry.grid(column = 1,row =row, columnspan=audioChans)
    row+=1
    st.grid(column = 1,row =row, columnspan=audioChans)
    row+=1
    csvButton.grid(column = 1, row = row,columnspan=audioChans)
    row+=1
    button_save.grid(column = 1, row = row)
    button_exit.grid(column = 2,row = row, columnspan=audioChans-1)
    window.mainloop()
