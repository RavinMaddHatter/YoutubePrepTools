import subprocess
import xml.etree.cElementTree as ElementTree


class FFProbe:
    def __init__(self, filename):
        """
        Runs ``ffprobe`` executable over ``filename``, returns parsed XML

        Parameters:

            filename (str): Full path leading to the file to be probed

        Returns:

            xml.etree.ElementTree: containing all parsed elements

        """
        executable = "ffprobe"
        cmd = [
            executable,
            '-v', 'quiet',
            '-print_format', 'xml',  # here is the trick
            '-show_format',
            '-show_streams',
            filename,
        ]
        parsed_xml = ElementTree.fromstring(subprocess.check_output(cmd, shell=True))
        self.audio = []
        self.video = []
        for streams in parsed_xml.findall("streams"):
            for stream in streams.findall("stream"):
                if stream.get("codec_type") == "audio":
                    self.audio.append(Audio(stream))
                elif stream.get("codec_type") == "video":
                    self.video.append(Video(stream))


class Video:
    def __init__(self, xml):
        self.index = xml.get("index")
        fr = float(xml.get("avg_frame_rate").split("/")[0]) / float(xml.get("avg_frame_rate").split("/")[1])
        self.framerate = fr
        self.width = xml.get("width")
        self.height = xml.get("height")
        self.codec = xml.get("codec_name")
        pass


class Audio:
    def __init__(self, xml):
        self.codec = xml.get("codec_name")
        self.sample_rate = xml.get("sample_rate")
        self.channels = xml.get("channels")
        pass
