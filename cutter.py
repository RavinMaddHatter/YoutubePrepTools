#metadata=FFProbe('F:\\Videos\\skyblock but\\EP 6\\ep6c1.mkv')
#ffmpeg -i .\ep6c1.mkv -bitexact -map 0:1 -acodec pcm_s16le -ar 22050 -ac 1 audio.wav
import numpy as np
import scipy.io
import pandas as pd
from scipy.io import wavfile
import time


##delete this junk
from jumpcutter.clip import Clip
from jumpcutter.clip import xmlGen
cut="silent"
cutThresh=0.02
durThres=0.5
failureTol=0.1
space=0.1
minClip=0.5
start=time.time()
input_path="F:\\Videos\\skyblock but\\EP 6\\ep6c1.mkv"
output_path=input_path.replace(".mkv",".xml")
generator=xmlGen(str(input_path),
                        str(output_path),
                        cutThresh,
                       durThres,
                       failureTol,
                       space,
                       minClip,
                       cut,
                       audioChannels=1)
print(time.time()-start)
## stop delete



silent_thresh=24 #dB
lead_in=0.05 #seconds
lead_out=0.05 #seconds
min_clip_dur=0.5#seconds
min_silent_dur=0.1#seconds




file_name="C:\\Users\\camer\\OneDrive\\Documents\\GitHub\\youtubePrep\\audio.wav"


def computeCuts(file_name):
    samplerate, data = wavfile.read(file_name) # bring in wave file
    if len(data.shape)==1:
        return computeCutsMono(data,samplerate)
    else:
        data=(data[:,0]+data[:,1])/2
        return computeCutsMono(data,samplerate)

def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)
def computeCutsMono(data,samplerate):
    # Calculate signal p-p
    max_delta=(int(data.max())-int(data.min()))
    # convert dB to linear
    threshold=max_delta*(10**(-silent_thresh/10))
    #set up a scanner for 10% of the min clip duration
    scan_interval=min_clip_dur/10
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
    quiet_long_enough = np.where(dur_quiet > min_silent_dur*samplerate,True,False)
    # remove edges related to short silences
    index_of_rising_edges = index_of_rising_edges[quiet_long_enough]
    index_of_falling_edges=index_of_falling_edges[quiet_long_enough[:index_of_falling_edges.size]]
    # calculate loud durrations
    dur_loud=index_of_falling_edges-index_of_rising_edges[:index_of_falling_edges.size]
    # check if it is loud long enough
    loud_long_enough = np.where(dur_loud > min_clip_dur*samplerate,True,False)
    #remove clips that are too short
    index_of_rising_edges = index_of_rising_edges[loud_long_enough]
    index_of_falling_edges=index_of_falling_edges[loud_long_enough[:index_of_falling_edges.size]]
    #calculate remaining clip durations
    rising_times = index_of_rising_edges / samplerate - lead_in
    falling_times = index_of_falling_edges / samplerate - lead_out
    durs=falling_times-rising_times
    print(durs)
    return [rising_times,falling_times]
        
    
start=time.time()
[index_of_rising_edges,index_of_falling_edges] = computeCuts(file_name)
print(time.time()-start)
