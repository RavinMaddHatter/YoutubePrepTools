[[TOC]]

# Youtube Video Publishing Tools
This is a set of tools I put together to make youtube video publishing much easier. The tools help cut silence from video clips, transcribe an audio file to a Text file for youtube subtitles, and quickly and efficiently make chapters for your description with boiler plate social media links. Currently only supports MKV files and has been confirmed to work on Davinci Resolve video editing software. 

This project is Free and Open source, and is powered by other opensource projects. 
## Introduction
[![How this works](http://img.youtube.com/vi/npFae43ULP0/0.jpg)](https://youtu.be/npFae43ULP0 "Faster Youtube Video Publishing/Editing Tools using OpenAI and Davinci")

## Prerequisites
To install this took you will first need to install FFMPEG and FFPROBE. FFMEG and FFPROBE are opensource tools that allow for the minipulation of Video and Audio files. FFMPEG and FFPROBE needs to be added to PATCH: variable, how you do that is explained in this video. Installation from Winget or Chocolatey will not suffice on Windows.

[![How to install FFMPEG to path](http://img.youtube.com/vi/r1AtmY-RMyQ/0.jpg)](https://www.youtube.com/watch?v=r1AtmY-RMyQ "Video Title")

Download the file from the latest release

[latest release](https://github.com/RavinMaddHatter/YoutubePrepTools/releases/latest)

## Instructions 
This section is a basic walk through of the features

### Video File Processing 
To begin you will need to know the settings that drive the program. First the audio levels for what defines silent and what defines loud are cut off per channel using the sliders.

![Audio Level Sliders](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/Slider%20Highlighted.png?raw=true)

Enable Tracks using the check box

![Enable Check boxes](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/Enabled%20highllighted.png?raw=true)

In space is the amount of "quiet time" before the the first detected loud sound. Out time is the quiet time after the last detected loud sound in a section of video.

![Enable Check boxes](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/in%20and%20out%20space%20highlighted.png?raw=true)

Min Clip Length is the length of time a "loud section" must be to be kept. Min Silent Duration is the minimum amount of time for a silent section to be deleted.

![Clip lengths](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/Clip%20lenghts%20highlighted.png?raw=true)

Cut Clip applies the settings to a single video file and exports and EDL matching the video file name. A file browser will open for this. Cut Folder applies the cut process to all videos in the folder and creates 1 timeline with the foldername. **Video will be processed as soon as it is selected and window is closed**

![execute cut process](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/cut%20clip%20and%20cut%20folder.png?raw=true)

### Audio Transcription
To automatically transcribe audio, the OpenAI whisper libary is used. To use that library a a model must be chosen. The larger the model, the longer processing and downloading will take. The smaller the model more likely there will be incorrect or failed words.

![Selecting Model](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/model%20select%20highlighted.png?raw=true)

After a model is selected you use the Transcribe WAV button to browse for an audio file. This process may take several minutes, the progress bar does not update while transcribing.

![Browse for audio](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/Transcribe%20highlighted.png?raw=true)

### Description tools

The description tools allows for the keeping of boilerplate data for your youtube description. It is intended for your social media, and general information you typically copy and paist between videos.

![Description tools](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/Template%20Description%20highlighted.png?raw=true)

After exporting the markers from the edit index as CSV (watch intro video for how to do that) the markers can be driectly converted to chapters in the description and appended to the template with the "Makers to clipboard" button.

![Markers to clipboard](https://github.com/RavinMaddHatter/YoutubePrepTools/blob/main/Docs/Makers%20highlighted.png?raw=true)

### Save and exit. 

The save tool saves the current settings, the exit button closes the program.

## social media


[Discord](https://discord.com/invite/M7MHtUab2r)


[Youtube](https://www.youtube.com/channel/UCKHWmRRTGUc0Ssgd3SarD5g)

If you would like tip the devloper of the tool,

[ko-fi](https://ko-fi.com/ravinmaddhatter)
