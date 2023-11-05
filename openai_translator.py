from whisper import load_model, _MODELS
from os.path import splitext
from os.path import exists
from os import getcwd
from datetime import timedelta
import urllib.request


class Translator:
    def __init__(self, transcribe_queue, model):
        self.status_queue = transcribe_queue
        self.status_queue.put({"percent": 0.0, "state": "Getting Model"})
        path = "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt"

        if not exists(model + ".pt"):
            urllib.request.urlretrieve(_MODELS[model], model + ".pt")

        self.model = load_model(model, download_root=getcwd())
        self.status_queue.put({"percent": 25, "state": "Model Found"})

    def audio_to_text(self, fileName):
        print("starting translation")
        self.status_queue.put({"percent": 33, "state": "Starting Translation"})
        try:
            result = self.model.transcribe(fileName)
            name, extension = splitext(fileName)
            self.status_queue.put({"percent": 95, "state": "writing test"})
            with open(name + ".txt", "w+") as text_file:
                text_file.write(result["text"])

            segments = result['segments']
            self.status_queue.put({"percent": 33, "state": "Starting Translation"})
            for segment in segments:
                start_time = str(0) + str(timedelta(seconds=int(segment['start']))) + ',000'
                end_time = str(0) + str(timedelta(seconds=int(segment['end']))) + ',000'
                text = segment['text']
                segment_id = segment['id'] + 1
                segment = f"{segment_id}\n{start_time} --> {end_time}\n{text[1:] if text[0] is ' ' else text}\n\n"

                srt_filename = name + ".srt"
                with open(srt_filename, 'a', encoding='utf-8') as srtFile:
                    srtFile.write(segment)

        except Exception as e:
            print(e)
        self.status_queue.put({"percent": 100, "state": "done"})
