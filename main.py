import json
import os
import cv2
import requests
import pymysql
from typing import List
from fastapi import FastAPI, File, UploadFile
from config.firebase import firebase
from firebase_admin import firestore, credentials, initialize_app
from PIL import Image

app = FastAPI()
storage = firebase.storage()

cred = credentials.Certificate("serviceAccountCredentials.json")
default_app = initialize_app(cred)
db = firestore.client()
file_ref = db.collection("file_links")

class Link:
  def __init__(self, id, link, name):
    self.id = id
    self.link = link
    self.name = name

@app.get("/")
async def root():
  return {"message": "Hello world 2"}

@app.post("/make-frame")
async def uploadVideo(files: List[UploadFile] = File(...)):
  links = []
  
  for i, file in enumerate(files):
    try:
      contents = await file.read()
      with open(file.filename, "wb") as f:
        f.write(contents)
        bucket = storage.bucket
        blob = bucket.blob(file.filename, chunk_size=262144*10)
        blob.upload_from_filename(file.filename)
        blob.make_public()
        link = blob.public_url
        links.append(Link(i+1, link, file.filename))
        f.close()
        os.unlink(file.filename)
    except Exception as err:
      return {"error": str(err)}
    finally:
      await file.close()
  
  try:
    for link in links:
      data = {"link": link.link, "name": link.name}
      file_ref.document().set(data)
  except Exception as err:
    return {"error": str(err)}

  try:
    file_links = []
    docs = db.collection(u"file_links").stream()
    
    for doc in docs:
      data = { "id": doc.id, "file": doc.to_dict() }
      file_links.append(data)

    for link in file_links:
      path = link["file"]["link"]
      file_name = link["file"]["name"]
      save_dir = "frames"
      save_frame(path, file_name, save_dir)

    return file_links
  except Exception as err:
    return { "error": str(err) }

def create_dir(path):
  try:
    if not os.path.exists(path):
      os.makedirs(path)
  except OSError:
    print(f"ERROR: creating directory with name {path}")

def save_frame(path, file_name, dir, gap=50):
  con = pymysql.connect(host="localhost",user="root",password="",db="drug_alcohol")
  save_path = os.path.join(dir, file_name)
  create_dir(save_path)
  url = "https://eastus.api.cognitive.microsoft.com/customvision/v3.0/Prediction/67eb6bde-6855-4c6b-b555-006f273e9239/detect/iterations/Iteration1/image"
  cap = cv2.VideoCapture(path)
  idx = 0
  
  while True:
    ret, frame = cap.read()

    if ret == False:
      cap.release()
      break

    if idx == 0:
      cv2.imwrite(f"{save_path}/{idx}.png", frame)
      with open(f"{save_path}/{idx}.png", "rb") as file:
        headers = {'content-type': 'application/octet-stream', 'Prediction-Key': '154db301ad6844bca3dfcf20cf246a61'}
        response = requests.post(url, data=file, headers=headers)
        data = json.loads(response.text)
        predictions = data["predictions"]
        maxProbability = 0
        tagName = ""
        for pred in predictions:
          
          if (pred["probability"] > maxProbability):
            maxProbability = pred["probability"]
            tagName = pred["tagName"]
        
        print(maxProbability)
        cursor=con.cursor()
        cursor.execute("insert into predicted_data(tagName,maxProbability) value(%s,%s)", (tagName,maxProbability))
        con.commit()
        print(tagName)
        # print(data["predictions"])
        os.unlink(f"{save_path}/{idx}.png")
    else:
      if idx % gap == 0: # 1 % 50 = 0
        cv2.imwrite(f"{save_path}/{idx}.png", frame)
        with open(f"{save_path}/{idx}.png", "rb") as file:
          headers = {'content-type': 'application/octet-stream', 'Prediction-Key': '154db301ad6844bca3dfcf20cf246a61'}
          response = requests.post(url, data=file, headers=headers)
          data = json.loads(response.text)
          predictions = data["predictions"]
          maxProbability = 0
          tagName = ""
          for pred in predictions:
            
            
            if (pred["probability"] > maxProbability):
              maxProbability = pred["probability"]
              tagName = pred["tagName"]
          

           
          
          
          

          print(maxProbability)
          cursor=con.cursor()
          cursor.execute("insert into predicted_data(tagName,maxProbability) value(%s,%s)", (tagName,maxProbability))
          con.commit()
          print(tagName)
          # print(data["predictions"])
          os.unlink(f"{save_path}/{idx}.png")

    idx += 1
  con.close()


@app.get("/pred")
async def getPredictions():
  con = pymysql.connect(host="localhost",user="root",password="",db="drug_alcohol")
  cursor=con.cursor()
  cursor.execute("select * from predicted_data")
  result = cursor.fetchall()

  print(result)

  return result
  


   
    


  # api call -> /
  # https://eastus.api.cognitive.microsoft.com/customvision/v3.0/Prediction/67eb6bde-6855-4c6b-b555-006f273e9239/detect/iterations/Iteration1/image
  # Set Prediction-Key Header to : 154db301ad6844bca3dfcf20cf246a61
  # Set Content-Type Header to : application/octet-stream
  # Set Body to : <image file>


# blob = bucket.blob(f"{save_path}/{idx}.png", chunk_size=262144*10)
#       blob.upload_from_filename(f"{save_path}/{idx}.png")
#       blob.make_public()
#       link = blob.public_url
#       print(link)

 
