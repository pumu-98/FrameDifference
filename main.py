import json
import os
import cv2
import requests
import mysql.connector
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

# Database connection
db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="RavB1998",
  database="frames_db"
)

cursor = db.cursor(buffered=True)

cursor.execute("CREATE DATABASE IF NOT EXISTS frames_db")
cursor.execute("CREATE TABLE IF NOT EXISTS files (id INT NOT NULL AUTO_INCREMENT, name VARCHAR(300) NULL, link VARCHAR(1000), status ENUM('PENDING', 'COMPLETED') NOT NULL DEFAULT 'PENDING', PRIMARY KEY (id))")
cursor.execute("CREATE TABLE IF NOT EXISTS predicted_data (id INT NOT NULL AUTO_INCREMENT, tag_name VARCHAR(255), max_probability DECIMAL(20,10), video_id INT, PRIMARY KEY (id), FOREIGN KEY (video_id) REFERENCES files(id))")

class Link:
  def __init__(self, id, link, name):
    self.id = id
    self.link = link
    self.name = name

@app.get("/")
async def root():
  return {"message": "Hello world"}

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
      query ="INSERT INTO files (name, link) VALUES (%s, %s)"
      data = (link.name, link.link)
      cursor.execute(query, data)
      db.commit()
      print("Video data recorded")
  except Exception as err:
    return {"error": str(err)}

  try:
    query = "SELECT * FROM files WHERE status='PENDING'"
    cursor.execute(query)
    columns = cursor.description
    results = []

    for value in cursor.fetchall():
      temp = {}
      for (index, column) in enumerate(value):
        temp[columns[index][0]] = column
      results.append(temp)
    print(results)

    for link in results:
      video_id= link["id"],
      path = link["link"]
      file_name = link["name"]
      save_dir = "frames"
      video_id = str(video_id).strip("'(,)'")
      save_frame(video_id, path, file_name, save_dir)
      query = "UPDATE files SET status = 'COMPLETED' WHERE id=" + video_id
      cursor.execute(query)
      db.commit()

    return results
  except Exception as err:
    return { "error": str(err) }

def create_dir(path):
  try:
    if not os.path.exists(path):
      os.makedirs(path)
  except OSError:
    print(f"ERROR: creating directory with name {path}")

def save_frame(video_id, path, file_name, dir, gap=50):
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
        
        # print('%s %f' % (tagName, maxProbability))
        print(f"{video_id} - {tagName} {maxProbability}")
        maxProbability = str(maxProbability)
        query = "INSERT INTO predicted_data (tag_name, max_probability, video_id) VALUES(%s, %s, %s)"
        data = (tagName, maxProbability, video_id)
        try:
          cursor.execute(query, data)
          db.commit()
        except Exception as err:
          print(err)
        file.close()
        os.unlink(f"{save_path}/{idx}.png")
    else:
      if idx % gap == 0:
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

          # print('%s %f' % (tagName, maxProbability))
          print(f"{video_id} - {tagName} {maxProbability}")
          maxProbability = str(maxProbability)
          query = "INSERT INTO predicted_data (tag_name, max_probability, video_id) VALUES(%s, %s, %s)"
          data = (tagName, maxProbability, video_id)
          try:
            cursor.execute(query, data)
            db.commit()
          except Exception as err:
            print(err)
          file.close()
          os.unlink(f"{save_path}/{idx}.png")
    idx += 1


@app.get("/pred")
async def getPredictions():
  query = "SELECT tag_name, max_probability, video_id FROM predicted_data"
  
  cursor.execute(query)
  columns = cursor.description
  results = []

  for value in cursor.fetchall():
    temp = {}
    for (index, column) in enumerate(value):
      temp[columns[index][0]] = column
    results.append(temp)

  return results

@app.get("/pred/{id}")
async def getPredictionsForVideo(id: str):
  query = "SELECT tag_name, max_probability FROM predicted_data WHERE video_id=" + id
  
  cursor.execute(query)
  columns = cursor.description
  results = []

  for value in cursor.fetchall():
    temp = {}
    for (index, column) in enumerate(value):
      temp[columns[index][0]] = column
    results.append(temp)

  return results
