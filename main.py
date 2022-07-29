import json
import os
import cv2
from typing import List
from fastapi import FastAPI, File, UploadFile
from config.firebase import firebase
from firebase_admin import firestore, credentials, initialize_app

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

@app.post("/upload")
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

  return {"message": links}    

@app.get("/get-files")
async def get_links():
  try:
    file_links = []
    docs = db.collection(u"file_links").stream()
    
    for doc in docs:
      data = { "id": doc.id, "file": doc.to_dict() }
      file_links.append(data)

    return file_links
  except Exception as err:
    return { "error": str(err) }

@app.post("/frame")
async def make_frame():
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

def save_frame(path, file_name, dir, gap=10):
  save_path = os.path.join(dir, file_name)
  create_dir(save_path)

  cap = cv2.VideoCapture(path)
  idx = 0
  
  while True:
    ret, frame = cap.read()

    if ret == False:
      cap.release()
      break

    if idx == 0:
      cv2.imwrite(f"{save_path}/{idx}.png", frame)
    else:
      if idx % gap == 0:
        cv2.imwrite(f"{save_path}/{idx}.png", frame)

    idx += 1