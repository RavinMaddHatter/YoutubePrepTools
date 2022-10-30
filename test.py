import subprocess
import xml.etree
import xml.etree.cElementTree as ElementTree

class ffprobe:
    def __init__(self,executable, filename):
        '''Runs ``ffprobe`` executable over ``filename``, returns parsed XML

        Parameters:

            executable (str): Full path leading to ``ffprobe``
            filename (str): Full path leading to the file to be probed

        Returns:

            xml.etree.ElementTree: containing all parsed elements

        '''

        cmd = [
            executable,
            '-v', 'quiet',
            '-print_format', 'xml', #here is the trick
            '-show_format',
            '-show_streams',
            filename,
            ]
        parsed_xml=ElementTree.fromstring(subprocess.check_output(cmd))
        self.audio=[]
        self.video=[]
        for streams in parsed_xml.findall("streams"):
            for stream in streams.findall("stream"):
                if stream.get("codec_type") == "audio":
                    self.audio.append(audio(stream))
                elif stream.get("codec_type") == "video":
                    self.video.append(video(stream))
                    
class video:
    def __init__(self, xml):
        
        self.index=xml.get("index")
        self.framerate=xml.get("avg_frame_rate")
        self.width=xml.get("width")
        self.height=xml.get("height")
        self.codec=xml.get("codec_name")
        pass
class audio:
    def __init__(self, xml):
        print(xml.keys())
        pass

test=ffprobe("ffprobe", 'F:\\Videos\\skyblock but\\EP 6\\ep6c1.mkv')
