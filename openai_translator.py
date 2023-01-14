from whisper import load_model, _MODELS
from os.path import splitext
from os.path import exists
from os import getcwd
import urllib.request


class translator:
    def __init__(self):
        path="https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt"
        print("getting openai speach model")
        if not exists("base.pt"):
            urllib.request.urlretrieve(_MODELS["base"], "base.pt")
        self.model = load_model("base",download_root=getcwd())
        print("model found")
    def audioToText(self,fileName):
        print("starting translation")
        result = self.model.transcribe(fileName)
        name, extension = splitext(fileName)
        with open(name+".txt", "w+") as text_file:
            text_file.write(result["text"])

