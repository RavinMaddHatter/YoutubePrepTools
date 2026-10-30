import translator_2 as Translator
import glob
from queue import Queue
from threading import Thread
from time import sleep
import os
folder = "W:\\Bluey (2018)\\sort me"
model = "base"
transcribe_queue = Queue()
print("queue sent")

def progress_bar(operation_name, update_queue):
    complete = False
    while not complete:
        sleep(0.01)
        if not update_queue.empty():
            update = update_queue.get()
            print(f'{update["percent"]}/t:{update["state"]}')
            
            complete = (update["state"] == "done")



print("start")
translator = Translator.Translator

for file in glob.glob(folder+"\\*.mp4"):
    out_name = file.replace(".mp4",".txt")
    if not os.path.exists(out_name):
        transcribe_queue = Queue()
        popup = Thread(target=progress_bar, args=("Transcribing Video", transcribe_queue,))
        popup.start()
        print(file)
        trans = translator(transcribe_queue, model)
        print("running model")
        trans.audio_to_text(file)
        print("file complete")
    else:
        print("skipping {file}")
