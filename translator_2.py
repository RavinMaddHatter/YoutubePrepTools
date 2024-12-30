from faster_whisper import WhisperModel
from datetime import timedelta
from os.path import splitext
import torch
_MODELS={"base":"NA"}

class Translator:
    def __init__(self, transcribe_queue, model_size):
        self.status_queue = transcribe_queue
        self.status_queue.put({"percent": 10, "state": "Model Found"})
        #if torch.cuda.is_available():
        #    print("using gpu to speed things up")
        #    self.model=WhisperModel(model_size,device="cuda", compute_type="float16")
        #else:
        #    print("using cpu as cuda not found")
        self.model=WhisperModel(model_size,device="cpu", compute_type="int8")
    def audio_to_text(self, fileName):
        print("starting translation")
        self.status_queue.put({"percent": 20, "state": "Setup Transcription"})
        name, extension = splitext(fileName)
        segments, info = self.model.transcribe(fileName, beam_size=5, word_timestamps=True)
        text_results=""
        srt_filename = name + ".srt"
        srt_word_filename = name + "-per-word.srt"
        word_id=0
        self.status_queue.put({"percent": 25, "state": "Executing Transcription"})
        with open(srt_filename,"w+", encoding='utf-8') as srtFile:
            with open(srt_word_filename,"w+", encoding='utf-8') as srtWordFile:
                for segment in segments:
                    percent=int(70*segment.end/info.duration+25)
                    self.status_queue.put({"percent": percent, "state": "Executing Transcription"})
                    start_time = str(0) + str(timedelta(seconds=int(segment.start))) + ',000'
                    end_time = str(0) + str(timedelta(seconds=int(segment.end))) + ',000'
                    text = segment.text
                    segment_id = segment.id + 1
                    segment_text = f"{segment_id}\n{start_time} --> {end_time}\n{text[1:] if text[0] == ' ' else text}\n\n"
                    srtFile.write(segment_text)
                    text_results+=text
                    for word in segment.words:
                        word_id+=1
                        word_text=f"{word_id}\n{word.start} --> {word.end}\n{word.word}\n\n"
                        srtWordFile.write(word_text)
                    
                    
        self.status_queue.put({"percent": 95, "state": "writing text file"})
        with open(name + ".txt", "w+") as text_file:
            text_file.write(text_results)
        self.status_queue.put({"percent": 100, "state": "done"})
if __name__ == "__main__":
    from queue import Queue
    trans=Translator(Queue(),"base")
    trans = trans.audio_to_text("F:\\Videos\\Netherstart skyblock\\EP4\\EP6.mp4")
