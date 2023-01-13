import boto3
from botocore.exceptions import ClientError
import os

class translator:
    def __init__(self,s3Bucket="audioprocessing",profile="default"):
        self.s3Bucket=s3Bucket
        self.session = boto3.Session(profile_name=profile)
        self.transcribe_client = self.session.client('transcribe')
        self.s3_client = self.session.client('s3')
    def audioToText(self,fileName):
        print("uploading file")
        obj_name=self.uploadFile(fileName)
        job_name=str(uuid.uuid4())
        url="s3://{}/{}".format(self.s3Bucket,obj_name)
        name, extension = os.path.splitext(fileName)
        self.handle=self.transcribe(job_name,url)
        self.jsonTranslate=json.loads(requests.get(self.handle).content.decode('ascii'))
        with open(name+"_raw_translation.json","w+") as file:
            json.dump(self.jsonTranslate,file)
        self.text=self.jsonTranslate["results"]["transcripts"][0]["transcript"]
        
        
        
        with open(name+".txt", "w+") as text_file:
            text_file.write(self.text)
        self.deleteFile(obj_name)
    def uploadFile(self,fileName,object_name=None):
        if object_name is None:
            object_name = os.path.basename(fileName)
        try:
            response = self.s3_client.upload_file(fileName, self.s3Bucket, object_name)
        except ClientError as e:
            logging.error(e)
            return "FAILED"
        return object_name
    def deleteFile(self, filename):
        try:
            self.s3_client.delete_object(Bucket = self.s3Bucket, Key = filename)
        except ClientError as e:
            logging.error(e)
            return False
        return True
    def transcribe(self,job_name, file_uri):
        self.transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': file_uri},
            MediaFormat='wav',
            LanguageCode='en-US'
        )

        max_tries = 360
        while max_tries > 0:
            max_tries -= 1
            job = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = job['TranscriptionJob']['TranscriptionJobStatus']
            if job_status in ['COMPLETED', 'FAILED']:
                print(f"Job {job_name} is {job_status}.")
                
                if job_status == 'COMPLETED':
                    return job['TranscriptionJob']['Transcript']['TranscriptFileUri']
                break
            else:
                print(f"Waiting for {job_name}. Current status is {job_status}.")
            time.sleep(10)
