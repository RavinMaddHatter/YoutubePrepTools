import time
t1=time.time()
from time import sleep
from threading import Thread
import cutter
import openai_translator as Translator
from queue import Queue
from csv import DictReader
from pyperclip import copy
from json import dump, load
from tkinter import Tk, Label, Button, INSERT, Scale, IntVar, Checkbutton, END
from tkinter import filedialog, Entry, DoubleVar, ttk, Toplevel, StringVar, OptionMenu
from os.path import exists, split, join, getmtime
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
from glob import glob
print(time.time()-t1)
confFile="youtubeDescription.json"
data=None
BoilerplateInfo=None
slider_defaults = None
sliders_enabled = None
audioChans=6
translator=Translator.translator
def updateSave(in_space, out_space,min_silent, min_clip,model):
    data["model"]=model
    data["boilerplate"]=BoilerplateInfo
    data["in_space"]=in_space
    data["out_space"]=out_space
    data["min_clip"]=min_clip
    data["min_silent"]=min_silent
    data["sliders_enabled"]=sliders_enabled
    data["slider_defaults"]=slider_defaults
    
    with open(confFile,"w+") as file:
        dump(data,file, indent=2)
if exists(confFile):
    with open(confFile) as file:
        data = load(file)
        BoilerplateInfo = data["boilerplate"]
        
        print("loaded sliders")
        sliders_enabled = data["sliders_enabled"]
        slider_defaults = data["slider_defaults"]
        print(data)

if BoilerplateInfo == None:
    BoilerplateInfo="Default Test For Your Youtube Description/n"
if slider_defaults == None:
    slider_defaults = []
    sliders_enabled = []
    for i in range(audioChans):
        slider_defaults.append(-24)
        sliders_enabled.append(False)
    sliders_enabled[0]=True
   
if data == None:
    data={}
    data["model"]="base"
    data["in_space"]=0.1
    data["out_space"]=0.1
    data["min_clip"]=1
    data["min_silent"]=0.1
    updateSave(0.1, 0.1,0.1, 1,"base")
elif "model" not in data.keys():
    data["model"]="base"

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
        copy(BoilerplateInfo+"\n\r\n\rChapters: \n\r"+"\n\r".join(self.markers))
    def stringToFile(self,name):
        with open(name, "w+") as text_file:
            text_file.write("\n\r".join(self.markers))
        

if __name__=="__main__":
    def progress_bar(operation_name,update_queue):
        popup = Toplevel(height=100,width=500)
        status_text=StringVar()
        popup_description = Label(popup, textvariable = status_text)
        popup_description.grid(row=0,column=0)
        progress = 0
        progress_var = DoubleVar()
        progress_bar = ttk.Progressbar(popup, variable=progress_var, maximum=100)
        progress_bar.grid(row=1, column=0)
        complete=False
        while not complete:
            sleep(0.01)
            if not update_queue.empty():
                update=update_queue.get()
                progress_var.set(update["percent"])
                status_text.set(update["state"])
                popup.update()
                popup.focus_force()
                complete =( update["state"] == "done")
        popup.destroy()
        popup.update()
    def findCSV():
        filename = filedialog.askopenfilename(title = "Select a CSV File",
                                          filetypes = (("CSV files",
                                                        "*.CSV*"),
                                                       ("all files",
                                                        "*.*")))
        try:
            BoilerplateInfo=st.get("1.0", END)
            mk=markerProcessor(filename)
            mk.stringToClipboard()
            print("markers in clipboard")
        except Exception as e:
            print("Failed")
            print(e)
    def transcribeProcess(transcribe_queue,filename):
        trans=translator(transcribe_queue,selected_model.get())
        trans.audioToText(filename)
    def transcribeVid():
        filename = filedialog.askopenfilename(title = "Select a WAV File",
                                          filetypes = (("WAV files",
                                                        "*.WAV*"),
                                                       ("all files",
                                                        "*.*")))
        try:
            transcribe_queue=Queue()
            popup=Thread(target=progress_bar,args=("Transcribing Video",transcribe_queue,))
            popup.start()
            trans=Thread(target=transcribeProcess,args=(transcribe_queue,filename,))
            trans.start()
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
    def cut_clip_process(queue,video_file):
        name = Path(video_file).stem
        head, tail = split(video_file)
        cc=cutter.clipCutter(queue)
        try:
            do_settings(cc)
            cc.add_cut_video_to_timeline(video_file)
            cc.export_edl(join(head,name+"-cut.edl"))
            cc._cleanup()
        except Exception as e:
            print(e)
            cc._cleanup()
    def cut_clip():
        video_file = filedialog.askopenfilename(title = "Select a WAV File",
                                          filetypes = (("video files",
                                                        "*.mkv*"),
                                                       ("all files",
                                                        "*.*")))
        
        cut_queue=Queue()
        popup=Thread(target=progress_bar,args=("Cutting Video",cut_queue,))
        popup.start()
        trans=Thread(target=cut_clip_process,args=(cut_queue,video_file,))
        trans.start()
    def cut_folder_process(queue,folder):
        cc=cutter.clipCutter(queue)
        try:
            name=split(folder)[-1]
            do_settings(cc)
            files=glob(join(folder,"*.mkv"))
            files.sort(key=getmtime)
            for file in files:
                print(file)
                cc.add_cut_video_to_timeline(file)
            print(join(folder,(name+"-cut.edl")))
            cc.export_edl(join(folder,(name+"-cut.edl")))
            cc._cleanup()
        except Exception as e:
            print(e)
            cc._cleanup()
    def cut_folder():
        folder = filedialog.askdirectory()
        cut_queue=Queue()
        popup=Thread(target=progress_bar,args=("Cutting Video",cut_queue,))
        popup.start()
        trans=Thread(target=cut_folder_process,args=(cut_queue,folder,))
        trans.start()
    def save():
        for i in range(audioChans):
            slider_defaults[i] = sliders[i].get()
            sliders_enabled[i] = slider_chks[i].get()
        
        updateSave(lead_in.get(), lead_out.get(),min_silent_dur_var.get(), clip_dur.get(),selected_model.get())
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
                        text = "Transcribe WAV",
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
    st.insert(INSERT,BoilerplateInfo)
    options = ["tiny", "base", "small", "medium", "large"]
    model_label = Label(window,text = "Speach Model Size",width = 15, height = 2)
    selected_model = StringVar()
    selected_model.set(data["model"])
    model_select = OptionMenu( window , selected_model , *options )
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
    audio_lb = Label(window,text = "Audio Tools",width = 15, height = 2)
    row=1
    label_file_explorer.grid(column = 1, row = row, columnspan=audioChans)
    row+=1
  
    
    cut_button.grid(column = 0, row = row,columnspan=3)
    super_cut_button.grid(column = 3, row = row,columnspan=3)
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
    
    audio_lb.grid(column = 1, row = row,columnspan=6)
    row+=1
    model_label.grid(column = 0, row = row,columnspan=2)
    model_select.grid(column = 2, row = row,columnspan=1)
    waveButton.grid(column = 3, row = row,columnspan=3)
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
