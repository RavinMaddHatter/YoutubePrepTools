#metadata=FFProbe('F:\\Videos\\skyblock but\\EP 6\\ep6c1.mkv')
#ffmpeg -i .\ep6c1.mkv -bitexact -map 0:1 -acodec pcm_s16le -ar 22050 -ac 1 audio.wav
import numpy as np
import scipy.io
import pandas as pd
from scipy.io import wavfile
import time
import subprocess
import ffprobe
import tempfile
import shutil
from os import path





def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)
class clipCutter:
    def __init__(self):
        self.silent_thresh=24 #dB
        self.silent_thresh_list=None
        self.lead_in=0.05 #seconds
        self.lead_out=0.05 #seconds
        self.min_clip_dur=0.5#seconds
        self.min_silent_dur=0.1#seconds
        self.video_file_name=None
        self.metadata=None
        self.working_folder = tempfile.mkdtemp(prefix="youtubePrep-")
        print(self.working_folder )
        self.audio_tracks=0
    def set_multi_chan_thres(self,thresh_list):
        self.silent_thresh_list = thresh_list
    def set_silent_thresh(self,silent_thresh_db):
        self.silent_thresh=silent_thresh
    def set_lead_in(self,lead_in):
        self.lead_in=lead_in
    def set_lead_out(self,lead_out):
        self.lead_in=lead_out
    def set_min_clip_dur(self,min_clip_dur):
        self.min_clip_dur=min_clip_dur
    def import_video(self,file_name):
        self.metadata=ffprobe.FFProbe(file_name)
        self.video_file_name=file_name
        self.audio_tracks=len(self.metadata.audio)
        return self.metadata
    def _cleanup(self):
        shutil.rmtree(self.working_folder)
    def _export_audio(self,chan):
        if self.video_file_name is not None:
            # sample test command, 
            #ffmpeg -i .\ep6c1.mkv -bitexact -map 0:1 -acodec pcm_s16le -ar 22050 -ac 1 audio.wav 
            audio_path=path.join(self.working_folder,"audio{}.wav".format(chan))
            cmd = 'ffmpeg -i "{}" -bitexact -map 0:{} -acodec pcm_s16le -ar 22050 -ac {} {}'.format(self.video_file_name,
                                                                                                  chan,
                                                                                                  self.metadata.audio[chan].channels,
                                                                                                  audio_path)
            subprocess.Popen(cmd).wait() ##needs clean up and error handling, but skipping for now.
            return audio_path
    def _compute_multi_channel_cuts(self,channels):
        if self.silent_thresh_list is None:
            self.silent_thresh_list=[self.silent_thresh] * self.audio_tracks
        start_clips=np.array([])
        stop_clips=np.array([])
        for chan in channels:
            [temp_start,temp_stop]=_compute_cuts(chan)
            start_clips=np.append(start_clips,temp_start)
            stop_clips=np.append(stop_clips,temp_stop)
        dur_quiet=start_clips[:stop_clips.size+1]-np.insert(stop_clips,0,0)
        quiet_long_enough = np.where(quiet_dur > self.min_silent_dur,True,False)
        start_clips=start_clips[quiet_long_enough]
        stop_clips=stop_clips[quiet_long_enough]
        dur_loud=stop_clips-start_clips[:stop_clips.size]
        loud_long_enough = np.where(dur_loud > self.min_clip_dur,True,False)
        start_clips=start_clips[loud_long_enough]
        stop_clips=stop_clips[loud_long_enough]
        return [start_clips,stop_clips]
        
    def _compute_cuts(self,channel):
        samplerate, data = wavfile.read(self._export_audio(channel)) # bring in wave file
        if len(data.shape)==1:
            return self._compute_cuts_mono(data,samplerate)
        else:
            data=(data[:,0]+data[:,1])/2
            return self._compute_cuts_mono(data,samplerate)
    def _compute_cuts_mono(self,data,samplerate):
        # Calculate signal p-p
        max_delta=(int(data.max())-int(data.min()))
        # convert dB to linear
        threshold=max_delta*(10**(-self.silent_thresh/10))
        #set up a scanner for 10% of the min clip duration
        scan_interval=self.min_clip_dur/10
        #set window for scanning
        window=int(scan_interval*samplerate)
        # window scans max value
        maxes= np.nan_to_num(pd.Series(data).rolling(window).max().to_numpy(), nan=0)
        # window scann min values
        mins=np.nan_to_num(pd.Series(data).rolling(window).min().to_numpy(), nan=0)
        # calculates peak to peak for each window
        max_vs_min = maxes - mins
        #checks where peak to peak is greater than loud threshold
        where_loud = np.where(max_vs_min > threshold,True,False)
        #Find edges where there is a transition between loud and quite
        edges = where_loud[:-1] != where_loud[1:]
        #find rising edges by checking where the signal was loud and hand just transitioned
        rising = np.logical_and(where_loud[1:], edges)
        #find falling edges by checking where the signal is quiet and has just transitioned
        falling = np.logical_and(np.logical_not(where_loud[1:]),edges)
        #get timestamps of edges 
        index_of_rising_edges = np.where(rising)[0]
        index_of_falling_edges = np.where(falling)[0]
        #Calculate silent durrations
        dur_quiet=index_of_rising_edges[:index_of_falling_edges.size+1]-np.insert(index_of_falling_edges,0,0)
        # check that it is quiet long enough
        quiet_long_enough = np.where(dur_quiet > self.min_silent_dur*samplerate,True,False)
        # remove edges related to short silences
        index_of_rising_edges = index_of_rising_edges[quiet_long_enough]
        index_of_falling_edges=index_of_falling_edges[quiet_long_enough[:index_of_falling_edges.size]]
        # calculate loud durrations
        dur_loud=index_of_falling_edges-index_of_rising_edges[:index_of_falling_edges.size]
        # check if it is loud long enough
        loud_long_enough = np.where(dur_loud > self.min_clip_dur*samplerate,True,False)
        #remove clips that are too short
        index_of_rising_edges = index_of_rising_edges[loud_long_enough]
        index_of_falling_edges=index_of_falling_edges[loud_long_enough[:index_of_falling_edges.size]]
        #calculate remaining clip durations
        rising_times = index_of_rising_edges / samplerate - self.lead_in
        falling_times = index_of_falling_edges / samplerate - self.lead_out
        return [rising_times,falling_times]

audio_file="C:\\Users\\camer\\OneDrive\\Documents\\GitHub\\youtubePrep\\audio.wav"
video_file='F:\\Videos\\skyblock but\\EP 6\\ep6c1.mkv'
cc=clipCutter()
test=cc.import_video(video_file)
test=cc._compute_cuts(1)
cc._cleanup()
#test=cc.computeCuts(file_name)
