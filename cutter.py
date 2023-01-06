import numpy as np
import scipy.io
import pandas as pd
from scipy.io import wavfile
import time
import subprocess
#import ffprobe
import access_ffprobe as ffprobe
import tempfile
import shutil
from os import path
import os
import uuid
import xml.etree.cElementTree as ElementTree

def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)
class clipCutter:
    def __init__(self):
        self.silent_thresh_list=[24,24,24,24]# set by function
        self.enabled_clips=[True, False, False, False] # set by function
        self.lead_in=0.05 #seconds set by function
        self.lead_out=0.05 #seconds set by function
        self.min_clip_dur=0.5#seconds set by function
        self.min_silent_dur=0.1#seconds set by function
        self.video_file_name=None # set by function
        self.metadata=None#set by import
        self.fps=60#set by import
        self.width=1920#can be set by importor by function
        self.height=1080#can be set by import or set by function
        self.durration=0#set by import
        self.working_folder = tempfile.mkdtemp(prefix="youtubePrep-")#temp folder so we don't make a mess
        self.audio_tracks=0#gets set by audio import
        self.tree = ElementTree.Element("xmeml", {"version": "5"})
        self.current_frame = 0 #tracking in timeline
        self.clips=[] # for internal only
        self.root_clips=[]#for internal only
        self.default_size=True#locks if you set a resolution manually
    def set_multi_chan_thres(self,thresh_list):
        self.silent_thresh_list = thresh_list
    def set_enabled_tracks(self,bool_list):
        self.enabled_clips = bool_list
    def set_lead_in(self,lead_in):
        self.lead_in=lead_in
    def set_lead_out(self,lead_out):
        self.lead_in=lead_out
    def set_min_clip_dur(self,min_clip_dur):
        self.min_clip_dur=min_clip_dur
    def set_min_silent_dur(self,min_silent_dur):
        self.min_silent_dur=min_silent_dur
    def set_timeline_res(self,width, height):
        self.height = height
        self.width = width
        self.default_size=False
    def add_cut_video_to_timeline(self,file_name,cut_channel=1):
        self.metadata=ffprobe.FFProbe(file_name)
        self.video_file_name=file_name
        
        self.audio_tracks=len(self.metadata.audio)
        self.fps = self.metadata.video[0].framerate
        if self.default_size:
            self.width = self.metadata.video[0].width
            self.height = self.metadata.video[0].height
        try: 
            [start_clips,stop_clips, total_length] = self._cut_audio()
            self.durration += sum(stop_clips-start_clips)
        except:
            [start_clips,stop_clips, total_length] = self._cut_audio()
            self.durration += sum(stop_clips-start_clips)
            start_clips=np.array([])
            stop_clips=[]
            total_length=0
            self.durration=0
            print("error")
        
        head, tail = os.path.split(file_name)
        root_name=path.splitext(tail)[0]
        for i in range(start_clips.size):
            handle="{}-{}".format(root_name,i)
            self.clips.append({"handle":handle,"in":start_clips[i],"out":stop_clips[i],"root":root_name,"file_name":file_name,"root_dur":total_length})

        return self.clips
    def _cleanup(self):
        shutil.rmtree(self.working_folder)
    def _export_audio(self,chan):
        if self.video_file_name is not None:
            # sample test command, 
            #ffmpeg -i .\ep6c1.mkv -bitexact -map 0:1 -acodec pcm_s16le -ar 22050 -ac 1 audio.wav
            
            audio_path=path.join(self.working_folder,"audio{}_{}.wav".format(uuid.uuid4(),chan))
            cmd = 'ffmpeg -i "{}" -bitexact -map 0:{} -acodec pcm_s16le -ar 22050 -ac {} {}'.format(self.video_file_name,
                                                                                                  chan,
                                                                                                  self.metadata.audio[chan].channels,
                                                                                                  audio_path)
            startupinfo = None
            subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).wait()  ##needs clean up and error handling, but skipping for now.
            return audio_path
    def _cut_audio(self):
        self.enabled_clips
        self.silent_thresh_list
#        self._import_audio_chan()
        data=None
        where_loud=None
        active_thresh=[]
        for i in range(min(len(self.enabled_clips),len(self.metadata.audio))):
            if self.enabled_clips[i]:
                active_thresh.append(-self.silent_thresh_list[i])
            
        silent_tresh=max(active_thresh)
        for i in range(min(len(self.enabled_clips),len(self.metadata.audio))):
            if self.enabled_clips[i]:
                samplerate, temp_data = wavfile.read(self._export_audio(i+1))
                if len(temp_data.shape)>1:
                    temp_data=(temp_data[:,0]+temp_data[:,1])/2
                temp_data=temp_data*10**(silent_tresh/10)/10**(-self.silent_thresh_list[i]/10)
                if data is None:
                    data=temp_data
                else:
                    data=(data*i+temp_data)/i+1
                    
        totalLength=data.size/samplerate
        # Calculate signal p-p
        max_delta=(int(data.max())-int(data.min()))
        # convert dB to linear
        threshold=max_delta*(10**(silent_tresh/10))
        #set up a scanner for 10% of the average of the in vs the out durration 
        scan_interval=(self.lead_in+self.lead_out)/20
        #set window for scanning
        window=int(scan_interval*samplerate)
        # window scans max value
        maxes= np.nan_to_num(pd.Series(data).rolling(window).max().to_numpy(), nan=0)
        # window scann min values
        mins=np.nan_to_num(pd.Series(data).rolling(window).min().to_numpy(), nan=0)
        # calculates peak to peak for each window
        max_vs_min = maxes - mins
        if where_loud is None:
            #checks where peak to peak is greater than loud threshold
            where_loud = np.where(max_vs_min > threshold,True,False)
        else:
            where_loud_temp = np.where(max_vs_min > threshold,True,False)
            where_loud = np.logical_or(where_loud_temp,where_loud)
        #Find edges where there is a transition between loud and quite
        edges = where_loud[:-1] != where_loud[1:]
        #find rising edges by checking where the signal was loud and hand just transitioned
        rising = np.logical_and(where_loud[1:], edges)
        #find falling edges by checking where the signal is quiet and has just transitioned
        falling = np.logical_and(np.logical_not(where_loud[1:]),edges)
        #get timestamps of edges 
        index_of_rising_edges = np.where(rising)[0]
        index_of_falling_edges = np.where(falling)[0]

        
        if (index_of_rising_edges.size > index_of_falling_edges.size):
            index_of_falling_edges=np.append(index_of_falling_edges,[edges.size-1])
            
##        elif (index_of_rising_edges.size < index_of_falling_edges.size):
##            index_of_rising_edges=np.append([0],index_of_rising_edges)
        if index_of_rising_edges.size==0:
            index_of_rising_edges=np.array([0])
            index_of_falling_edges=np.array([data.size])
        if (index_of_rising_edges[0]<index_of_falling_edges[0]):
            index_of_rising_edges=np.append(index_of_rising_edges,[edges.size])
            index_of_falling_edges=np.append([0],index_of_falling_edges)
            dur_quiet=index_of_rising_edges-index_of_falling_edges
            
        #Calculate silent durrations
        # check that it is quiet long enough
        quiet_long_enough = np.where(dur_quiet > self.min_silent_dur*samplerate,True,False)

        
        # remove edges related to short silences
        index_of_rising_edges = index_of_rising_edges[quiet_long_enough]
        index_of_falling_edges=index_of_falling_edges[quiet_long_enough[:index_of_falling_edges.size]]
        # calculate loud durrations
        if index_of_falling_edges.size>1:
            index_of_falling_edges=np.append(index_of_falling_edges[1:],index_of_falling_edges[0])
            dur_loud=index_of_falling_edges-index_of_rising_edges
            # check if it is loud long enough
            loud_long_enough = np.where(dur_loud > self.min_clip_dur*samplerate,True,False)
            #remove clips that are too short
            index_of_rising_edges = index_of_rising_edges[loud_long_enough]
            index_of_falling_edges=index_of_falling_edges[loud_long_enough[:index_of_falling_edges.size]]
        
        #calculate remaining clip durations
        rising_times = index_of_rising_edges / samplerate - self.lead_in
        falling_times = index_of_falling_edges / samplerate - self.lead_out
        print(["video length (S)","number of clips"])
        print([totalLength,len(rising_times)])
        return [rising_times,falling_times,totalLength]
    def export_xml(self,xml_file_path):
        head, tail = os.path.split(self.video_file_name)
        
        root_name=path.splitext(tail)[0]
        
        self._xml_headder(root_name,int(self.durration*self.fps))
        for clip in self.clips:
            self._add_video_clip(clip)
            self._add_audio_clip(clip)
            self.current_frame+=int((clip["out"]-clip["in"])*self.fps)
        with open(xml_file_path, "wb") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8" ?>\n<!DOCTYPE xmeml>\n'.encode(
                    "utf8"
                )
            )
            ElementTree.indent(self.tree, space="\t", level=0)
            ElementTree.ElementTree(self.tree).write(f, "utf-8")
    def _add_audio_clip(self,clip):
        clipItem = ElementTree.SubElement(self.at, "clipitem", {"id": clip["root"]})
        ElementTree.SubElement(clipItem, "name").text = clip["root"]
        ElementTree.SubElement(clipItem, "duration").text = str(clip["root_dur"])
        self._add_rate(clipItem)
        ElementTree.SubElement(clipItem, "start").text = str(self.current_frame)
        ElementTree.SubElement(clipItem, "stop").text = str(self.current_frame + int((clip["out"]-clip["in"])*self.fps))
        ElementTree.SubElement(clipItem, "enabled").text = "TRUE"
        ElementTree.SubElement(clipItem, "in").text = str(int(clip["in"]*self.fps))
        ElementTree.SubElement(clipItem, "out").text = str(int(clip["out"]*self.fps))
        ElementTree.SubElement(clipItem, "file", {"id": clip["root"]}
        )
        sourceTrack = ElementTree.SubElement(clipItem, "sourcetrack")
        ElementTree.SubElement(sourceTrack, "mediatype").text = "audio"
        ElementTree.SubElement(sourceTrack, "trackindex").text = str(1)#fix if i fix audio track count

        vidLink = ElementTree.SubElement(clipItem, "link")
        ElementTree.SubElement(vidLink, "linkclipref").text = clip["root"]
        ElementTree.SubElement(vidLink, "mediatype").text = "video"
        
        ElementTree.SubElement(self.at, "enabled").text = "TRUE"
        ElementTree.SubElement(self.at, "locked").text = "FALSE"
    def _add_video_clip(self, clip):
        clipItem = ElementTree.SubElement(self.vt, "clipitem",{"id":clip["handle"]})
        ElementTree.SubElement(clipItem, "name").text = clip["root"] + "cut"
        file = ElementTree.SubElement(clipItem, "file", {"id": clip["root"]})
        ElementTree.SubElement(file, "duration").text = str(clip["root_dur"])
        self._add_rate(clipItem)
        ElementTree.SubElement(clipItem, "start").text = str(self.current_frame)
        ElementTree.SubElement(clipItem, "stop").text = str(self.current_frame+int((clip["out"]-clip["in"])*self.fps))
        ElementTree.SubElement(clipItem, "enabled").text = "TRUE"
        ElementTree.SubElement(clipItem, "in").text = str(int(clip["in"]*self.fps))
        ElementTree.SubElement(clipItem, "out").text = str(int(clip["out"]*self.fps))
        
        if clip["root"] not in self.root_clips:
            self.root_clips.append(clip["root"])
            ElementTree.SubElement(file, "duration").text = str(clip["root_dur"])
            self._add_rate(file)
            ElementTree.SubElement(file, "out").text = clip["root"]
            pathToFile = "file://localhost/{}".format("/".join(os.path.split(clip["file_name"])))
            ElementTree.SubElement(file, "pathurl").text = pathToFile
            tc = ElementTree.SubElement(file, "timecode")
            ElementTree.SubElement(tc, "string").text = "00:00:00:00"
            ElementTree.SubElement(tc, "displayformat").text = "NDF"
            self._add_rate(tc)
            med = ElementTree.SubElement(file, "media")
            vid = ElementTree.SubElement(med, "video")
            ElementTree.SubElement(vid, "duration").text = str(clip["root_dur"])
            sc = ElementTree.SubElement(vid, "samplecharacteristics")
            ElementTree.SubElement(sc, "width").text = str(self.width)
            ElementTree.SubElement(sc, "height").text = str(self.height)
            aud = ElementTree.SubElement(med, "audio")
            ElementTree.SubElement(aud, "channelcount").text = str(1)#Fix if i fix audio channels
        ElementTree.SubElement(clipItem, "compositemode").text = "normal"
        ##Filter to play the video

        filt1 = ElementTree.SubElement(clipItem, "filter")
        ElementTree.SubElement(filt1, "enabled").text = "TRUE"
        ElementTree.SubElement(filt1, "start").text = "0"
        ElementTree.SubElement(filt1, "end").text = str(clip["root_dur"])
        eff1 = ElementTree.SubElement(filt1, "effect")
        ElementTree.SubElement(eff1, "name").text = "Basic Motion"
        ElementTree.SubElement(eff1, "effectid").text = "basic"
        ElementTree.SubElement(eff1, "effecttype").text = "motion"
        ElementTree.SubElement(eff1, "mediatype").text = "video"
        ElementTree.SubElement(eff1, "effectcategory").text = "motion"
        parm1a = ElementTree.SubElement(eff1, "parameter")
        ElementTree.SubElement(parm1a, "name").text = "Scale"
        ElementTree.SubElement(parm1a, "parameterid").text = "scale"
        ElementTree.SubElement(parm1a, "value").text = "100"
        ElementTree.SubElement(parm1a, "valuemin").text = "0"
        ElementTree.SubElement(parm1a, "valuemax").text = "10000"
        parm1b = ElementTree.SubElement(eff1, "parameter")
        ElementTree.SubElement(parm1b, "name").text = "Center"
        ElementTree.SubElement(parm1b, "parameterid").text = "center"
        parm1bval = ElementTree.SubElement(parm1b, "value")
        ElementTree.SubElement(parm1bval, "horiz").text = "0"
        ElementTree.SubElement(parm1bval, "vert").text = "0"
        parm1c = ElementTree.SubElement(eff1, "parameter")
        ElementTree.SubElement(parm1c, "name").text = "Rotation"
        ElementTree.SubElement(parm1c, "parameterid").text = "rotation"
        ElementTree.SubElement(parm1c, "value").text = "0"
        ElementTree.SubElement(parm1c, "valuemin").text = "-100000"
        ElementTree.SubElement(parm1c, "valuemax").text = "100000"
        parm1d = ElementTree.SubElement(eff1, "parameter")
        ElementTree.SubElement(parm1d, "name").text = "Anchor Point"
        ElementTree.SubElement(parm1d, "parameterid").text = "centerOffset"
        parm1dval = ElementTree.SubElement(parm1d, "value")
        ElementTree.SubElement(parm1dval, "horiz").text = "0"
        ElementTree.SubElement(parm1dval, "vert").text = "0"
        ##Filter to crop
        filt2 = ElementTree.SubElement(clipItem, "filter")
        ElementTree.SubElement(filt2, "enabled").text = "TRUE"
        ElementTree.SubElement(filt2, "start").text = "0"
        ElementTree.SubElement(filt2, "end").text = str(clip["root_dur"])
        eff2 = ElementTree.SubElement(filt2, "effect")
        ElementTree.SubElement(eff2, "name").text = "Crop"
        ElementTree.SubElement(eff2, "effectid").text = "crop"
        ElementTree.SubElement(eff2, "effecttype").text = "motion"
        ElementTree.SubElement(eff2, "mediatype").text = "video"
        ElementTree.SubElement(eff2, "effectcategory").text = "motion"
        parm2a = ElementTree.SubElement(eff2, "parameter")
        ElementTree.SubElement(parm2a, "name").text = "left"
        ElementTree.SubElement(parm2a, "parameterid").text = "left"
        ElementTree.SubElement(parm2a, "value").text = "0"
        ElementTree.SubElement(parm2a, "valuemin").text = "0"
        ElementTree.SubElement(parm2a, "valuemax").text = "100"
        parm2b = ElementTree.SubElement(eff2, "parameter")
        ElementTree.SubElement(parm2b, "name").text = "right"
        ElementTree.SubElement(parm2b, "parameterid").text = "right"
        ElementTree.SubElement(parm2b, "value").text = "0"
        ElementTree.SubElement(parm2b, "valuemin").text = "0"
        ElementTree.SubElement(parm2b, "valuemax").text = "100"
        parm2b = ElementTree.SubElement(eff2, "parameter")
        ElementTree.SubElement(parm2b, "name").text = "top"
        ElementTree.SubElement(parm2b, "parameterid").text = "top"
        ElementTree.SubElement(parm2b, "value").text = "0"
        ElementTree.SubElement(parm2b, "valuemin").text = "0"
        ElementTree.SubElement(parm2b, "valuemax").text = "100"
        parm2b = ElementTree.SubElement(eff2, "parameter")
        ElementTree.SubElement(parm2b, "name").text = "bottom"
        ElementTree.SubElement(parm2b, "parameterid").text = "bottom"
        ElementTree.SubElement(parm2b, "value").text = "0"
        ElementTree.SubElement(parm2b, "valuemin").text = "0"
        ElementTree.SubElement(parm2b, "valuemax").text = "100"
        ##Filter to set opacity
        filt3 = ElementTree.SubElement(clipItem, "filter")
        ElementTree.SubElement(filt3, "enabled").text = "TRUE"
        ElementTree.SubElement(filt3, "start").text = "0"
        ElementTree.SubElement(filt3, "end").text = str(clip["root_dur"])
        eff3 = ElementTree.SubElement(filt3, "effect")
        ElementTree.SubElement(eff3, "name").text = "Opacity"
        ElementTree.SubElement(eff3, "effectid").text = "opacity"
        ElementTree.SubElement(eff3, "effecttype").text = "motion"
        ElementTree.SubElement(eff3, "mediatype").text = "video"
        ElementTree.SubElement(eff3, "effectcategory").text = "motion"
        parm3a = ElementTree.SubElement(eff3, "parameter")
        ElementTree.SubElement(parm3a, "name").text = "opacity"
        ElementTree.SubElement(parm3a, "parameterid").text = "opacity"
        ElementTree.SubElement(parm3a, "value").text = "100"
        ElementTree.SubElement(parm3a, "valuemin").text = "0"
        ElementTree.SubElement(parm3a, "valuemax").text = "100"

        vidLink = ElementTree.SubElement(clipItem, "link")
        ElementTree.SubElement(vidLink, "linkclipref").text = clip["root"]

        
        lin = ElementTree.SubElement(clipItem, "link")
        ElementTree.SubElement(lin, "linkclipref").text = clip["handle"]+"a"
    def _add_new_root_clip(self,root,clip):
        ElementTree.SubElement(file, "duration").text = str(clip["root_dur"])
        self._add_rate(file)
        ElementTree.SubElement(file, "out").text = clip["root"]
        pathToFile = "file://localhost/{}".format("/".join(os.path.split(clip["file_name"])))
        ElementTree.SubElement(file, "pathurl").text = clip["file_name"]
        tc = ElementTree.SubElement(file, "timecode")
        ElementTree.SubElement(tc, "string").text = "00:00:00:00"
        ElementTree.SubElement(tc, "displayformat").text = "NDF"
        self._add_rate(tc)
        med = ElementTree.SubElement(file, "media")
        vid = ElementTree.SubElement(med, "video")
        ElementTree.SubElement(vid, "duration").text = str(clip["root_dur"])
        sc = ElementTree.SubElement(vid, "samplecharacteristics")
        ElementTree.SubElement(sc, "width").text = str(self.width)
        ElementTree.SubElement(sc, "height").text = str(self.height)
        aud = ElementTree.SubElement(med, "audio")
        ElementTree.SubElement(aud, "channelcount").text = str(1)# If i can find a way to davinci imports audio correct i should fix this
    def _add_rate(self, root: ElementTree.Element)->None:
        rat = ElementTree.SubElement(root, "rate")
        ElementTree.SubElement(rat, "timebase").text = str(self.fps)
        ElementTree.SubElement(rat, "ntsc").text = "FALSE"
    def _xml_headder(self,out_name,duration):
        seq = ElementTree.SubElement(self.tree, "sequence")
        name = ElementTree.SubElement(seq, "name").text = (out_name)
        ElementTree.SubElement(seq, "duration").text = str(duration)
        self._add_rate(seq)
        ElementTree.SubElement(seq, "in").text = str(-1)
        ElementTree.SubElement(seq, "out").text = str(-1)
        tc = ElementTree.SubElement(seq, "timecode")
        ElementTree.SubElement(tc, "string").text = "01:00:00:00"
        ElementTree.SubElement(tc, "frame").text = "216000"
        ElementTree.SubElement(tc, "displayformat").text = "NDF"
        self._add_rate(tc)
        med = ElementTree.SubElement(seq, "media")
        video = ElementTree.SubElement(med, "video")
        self.vt = ElementTree.SubElement(video, "track")
        self._set_video_format(video)
        audio = ElementTree.SubElement(med, "audio")
        self.at = ElementTree.SubElement(audio, "track")
    def _set_video_format(self, video: ElementTree.Element)->None:
        form = ElementTree.SubElement(video, "format")
        sampChar = ElementTree.SubElement(form, "samplecharacteristics")
        ElementTree.SubElement(sampChar, "width").text = str(self.width)
        ElementTree.SubElement(sampChar, "height").text = str(self.height)
        ElementTree.SubElement(sampChar, "pixelaspectratio").text = "square"
        self._add_rate(sampChar)
        codec = ElementTree.SubElement(sampChar, "codec")
        appData = ElementTree.SubElement(codec, "appspecificdata")
        ElementTree.SubElement(appData, "appname").text = "Final Cut Pro"
        ElementTree.SubElement(appData, "appmanufacturer").text = "Apple Inc."
        data = ElementTree.SubElement(appData, "data")
        ElementTree.SubElement(data, "qtcodec")
##if __name__ == "__main__":
##    video_file='F:\\Videos\\skyblock but\\EP 6\\ep6c1.mkv'
##    cc=clipCutter()
##    cc.set_min_clip_dur(1)
##    test=cc.add_cut_video_to_timeline(video_file)
##    cc.export_xml("C:\\Users\\camer\\OneDrive\\Documents\\GitHub\\structuraBranch\\YoutubePrepTools\\text.xml")
##    cc._cleanup()

