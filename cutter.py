from numpy import lib, array, nan_to_num, where, logical_or, logical_and, append, logical_not
from pandas import Series
from scipy.io import wavfile
from subprocess import Popen, PIPE
import access_ffprobe as ffprobe
from tempfile import mkdtemp
from shutil import rmtree
from os.path import basename, join
from uuid import uuid4
from math import floor
from queue import Queue


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


class Clipcutter:
    def __init__(self, queue=Queue()):
        self.status_queue = queue
        self.status_queue.put({"percent": 0, "state": "Starting Clip Process"})
        self.silent_thresh_list = [24, 24, 24, 24]  # set by function
        self.enabled_clips = [True, False, False, False]  # set by function
        self.lead_in = 0.1  # seconds set by function
        self.lead_out = 0.1  # seconds set by function
        self.total_lead = 0.2
        self.min_clip_dur = 0.5  # seconds set by function
        self.min_silent_dur = 0.1  # seconds set by function
        self.video_file_name = None  # set by function
        self.metadata = None  # set by import
        self.fps = 60  # set by import
        self.width = 1920  # can be set by importor by function
        self.height = 1080  # can be set by import or set by function
        self.durration = 0  # set by import
        self.working_folder = mkdtemp(prefix="youtubePrep-")  # temp folder so we don't make a mess
        self.audio_tracks = 0  # gets set by audio import
        self.current_frame = 0  # tracking in timeline
        self.clips = []  # for internal only
        self.root_clips = []  # for internal only
        self.default_size = True  # locks if you set a resolution manually

    def set_multi_chan_thres(self, thresh_list):
        self.silent_thresh_list = thresh_list

    def set_enabled_tracks(self, bool_list):
        self.enabled_clips = bool_list

    def set_lead_in(self, lead_in):
        self.lead_in = lead_in
        self.total_lead =self.lead_out+lead_in

    def set_lead_out(self, lead_out):
        self.lead_out = lead_out
        self.total_lead = self.lead_in + lead_out

    def set_min_clip_dur(self, min_clip_dur):
        self.min_clip_dur = min_clip_dur

    def set_min_silent_dur(self, min_silent_dur):
        self.min_silent_dur = min_silent_dur

    def set_timeline_res(self, width, height):
        self.height = height
        self.width = width
        self.default_size = False

    def add_cut_video_to_timeline(self, file_name, cut_channel=1):
        self.status_queue.put({"percent": 20, "state": "getting metadata"})
        self.metadata = ffprobe.FFProbe(file_name)
        self.video_file_name = file_name
        self.audio_tracks = len(self.metadata.audio)
        self.fps = self.metadata.video[0].framerate
        if self.default_size:
            self.width = self.metadata.video[0].width
            self.height = self.metadata.video[0].height
        self.status_queue.put({"percent": 30, "state": "cutting audio"})
        try:
            [start_clips, stop_clips, total_length] = self._cut_audio()
            self.durration += sum(stop_clips - start_clips)
        except:
            [start_clips, stop_clips, total_length] = self._cut_audio()
            self.durration += sum(stop_clips - start_clips)
            start_clips = array([])
            stop_clips = []
            total_length = 0
            self.durration = 0
            print("error")
        self.status_queue.put({"percent": 80, "state": "Compiling Clips"})
        for i in range(start_clips.size):
            self.clips.append({"in": start_clips[i], "out": stop_clips[i], "file_name": file_name})

        return self.clips

    def _cleanup(self):
        rmtree(self.working_folder)
        self.status_queue.put({"percent": 100, "state": "done"})

    def _export_audio(self, chan):
        if self.video_file_name is not None:
            # sample test command, 
            # ffmpeg -i .\ep6c1.mkv -bitexact -map 0:1 -acodec pcm_s16le -ar 22050 -ac 1 audio.wav
            audio_path = join(self.working_folder, "audio{}_{}.wav".format(uuid4(), chan))
            cmd = 'ffmpeg -i "{}" -bitexact -map 0:{} -acodec pcm_s16le -ar 22050 -ac {} {}'.format(
                self.video_file_name,
                chan,
                self.metadata.audio[chan - 1].channels,
                audio_path)

            startupinfo = None
            returnVals = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True).communicate()
            return audio_path

    def _cut_audio(self):
        data = None
        where_loud = None
        active_thresh = []
        for i in range(min(len(self.enabled_clips), len(self.metadata.audio))):
            if self.enabled_clips[i]:
                active_thresh.append(-self.silent_thresh_list[i])

        silent_tresh = max(active_thresh)
        for i in range(min(len(self.enabled_clips), len(self.metadata.audio))):

            if self.enabled_clips[i]:
                print("merging track {}".format(i + 1))
                samplerate, temp_data = wavfile.read(self._export_audio(i + 1))
                print("audio track {} loaded".format(i + 1))

                if len(temp_data.shape) > 1:
                    temp_data = (temp_data[:, 0] + temp_data[:, 1]) / 2
                temp_data = temp_data * 10 ** (silent_tresh / 10) / 10 ** (-self.silent_thresh_list[i] / 10)

                if data is None:
                    data = temp_data
                else:
                    data = (data * i + temp_data) / i + 1

        total_length = data.size / samplerate

        # convert dB to linear
        # 23173 is the standard deviation of a 0 dB tone generated by audancity
        threshold = 23173 * 10 ** (
                    silent_tresh / 10)

        # set up a scanner for 10% of the average of the in vs the out durration
        scan_interval = (self.total_lead ) / 20

        # set window for scanning
        window = int(scan_interval * samplerate)

        # window standard deviation
        window_std = nan_to_num(Series(data).rolling(window).std().to_numpy(), nan=0)
        window_std[1:window] = window_std[window + 1]  ## managing intro where the window  is not valid

        if where_loud is None:
            # checks where peak to peak is greater than loud threshold
            where_loud = where(window_std > threshold, True, False)
        else:
            where_loud_temp = where(window_std > threshold, True, False)
            where_loud = logical_or(where_loud_temp, where_loud)

        # Find edges where there is a transition between loud and quite
        edges = where_loud[:-1] != where_loud[1:]

        # find rising edges by checking where the signal was loud and hand just transitioned
        rising = logical_and(where_loud[1:], edges)

        # find falling edges by checking where the signal is quiet and has just transitioned
        falling = logical_and(logical_not(where_loud[1:]), edges)

        # get timestamps of edges
        index_of_rising_edges = where(rising)[0]

        index_of_falling_edges = where(falling)[0]

        if index_of_rising_edges.size > index_of_falling_edges.size:
            index_of_falling_edges = append(index_of_falling_edges, [edges.size - 1])

        if index_of_rising_edges.size == 0:
            index_of_rising_edges = array([0])
            index_of_falling_edges = array([data.size])
        if index_of_rising_edges[0] < index_of_falling_edges[0]:
            index_of_rising_edges = append(index_of_rising_edges, [rising.size + self.min_silent_dur * samplerate + 1])

            # line is there to ensure that if the vidoe was loud at the beginning it is not incorrectly removed
            index_of_falling_edges = append([-self.min_silent_dur * samplerate - 1], index_of_falling_edges)
        dur_quiet = index_of_rising_edges - index_of_falling_edges

        # Calculate silent durrations
        # check that it is quiet long enough
        quiet_long_enough = where(dur_quiet > self.min_silent_dur * samplerate, True, False)

        # remove edges related to short silences
        index_of_rising_edges = index_of_rising_edges[quiet_long_enough]
        index_of_falling_edges = index_of_falling_edges[quiet_long_enough[:index_of_falling_edges.size]]

        # calculate loud durrations
        if index_of_falling_edges.size > 1:
            index_of_falling_edges = append(index_of_falling_edges[1:], index_of_falling_edges[0])
            dur_loud = index_of_falling_edges - index_of_rising_edges
            # check if it is loud long enough
            loud_long_enough = where(dur_loud > self.min_clip_dur * samplerate, True, False)
            # remove clips that are too short
            index_of_rising_edges = index_of_rising_edges[loud_long_enough]
            index_of_falling_edges = index_of_falling_edges[loud_long_enough[:index_of_falling_edges.size]]

        # calculate remaining clip durations
        rising_times = index_of_rising_edges / samplerate - self.lead_in
        falling_times = index_of_falling_edges / samplerate + self.lead_out

        # corrects for the negative time that would show up if the video was loud at start.
        if rising_times[0] < 0:
            rising_times[0] = 0

        print(["video length (S)", "number of clips"])
        print([total_length, len(rising_times)])

        return [rising_times, falling_times, total_length]

    def export_edl(self, edl_file_path, name=None):
        self.status_queue.put({"percent": 95, "state": "Exporting EDL"})
        if name is None:
            name = basename(edl_file_path).split(".")[0]

        # self.clips.append({"in":start_clips[i],"out":stop_clips[i]"file_name":file_name})
        with open(edl_file_path, "w+") as file:
            file.write("TITLE: {}\n\r".format(name))
            file.write("FCM: NON-DROP FRAME\n\n")
            i = 1
            current_time = 3600
            for clip in self.clips:
                clip_time_in = self.time_to_time_stamp(clip["in"])
                clip_time_out = self.time_to_time_stamp(clip["out"])
                timeline_time_in = self.time_to_time_stamp(current_time)
                current_time += clip["out"] - clip["in"]
                timeline_out = self.time_to_time_stamp(current_time)
                file.write("{:03d}  AX       V     C        {} {} {} {}\n".format(i, clip_time_in, clip_time_out,
                                                                                  timeline_time_in, timeline_out))
                file.write("* FROM CLIP NAME: {}\n\n".format(clip["file_name"]))
                i += 1

    def time_to_time_stamp(self, time):
        hours = floor(time / 3600)
        minutes = floor((time - hours * 3600) / 60)
        seconds = floor(time - hours * 3600 - minutes * 60)
        frames = floor((time - hours * 3600 - minutes * 60 - seconds) * self.fps)
        timestamp = "{:02d}:{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds, frames)
        return timestamp
