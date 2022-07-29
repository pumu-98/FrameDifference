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

@app.get("/")
async def root():
  return {"message": "Hello world 2"}

@app.post("/upload")
async def uploadVideo(files: List[UploadFile] = File(...)):
  links = []
  for file in files:
    try:
      contents = await file.read()
      with open(file.filename, "wb") as f:
        f.write(contents)
        bucket = storage.bucket
        blob = bucket.blob(file.filename, chunk_size=262144*10)
        blob.upload_from_filename(file.filename)
        blob.make_public()
        link = blob.public_url
        links.append(link)
        f.close()
        os.unlink(file.filename)
    except Exception as err:
      return {"message": str(err)}
    finally:
      await file.close()
  
  try:
    data = { "links": links }
    file_ref.document().set(data)
  except Exception as err:
    return {"message": str(err)}

  return {"message": links}    

@app.get("/get-files")
async def get_links():
  try:
    file_links = []
    docs = db.collection(u"file_links").stream()
    
    for doc in docs:
      data = { "id": doc.id, "file_links": doc.to_dict() }
      file_links.append(data)

    return { "data": file_links }
  except Exception as err:
    return { "error": str(err) }

@app.post("/frame")
async def make_frame():
  try:
    file_links = []
    docs = db.collection(u"file_links").stream()
    
    for doc in docs:
      print(doc["links"])


    return { "data": file_links }
  except Exception as err:
    return { "error": str(err) }