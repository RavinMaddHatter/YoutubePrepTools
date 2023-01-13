import whisper
from os.path import splitext
class translator:
    def __init__(self):
        print("getting openai speach model")
        self.model = whisper.load_model("base")
        print("model found")
    def audioToText(self,fileName):
        print("starting translation")
        result = self.model.transcribe(fileName)
        name, extension = splitext(fileName)
        with open(name+".txt", "w+") as text_file:
            text_file.write(result["text"])


if __name__ == "__main__":
    trans=translator()

    trans.audioToText("Test Files\\test.wav")
