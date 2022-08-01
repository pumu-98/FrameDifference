from pyrebase import pyrebase

firebaseConfig = {
  "projectId": "temp-fastapi-7b328",
  "apiKey": "AIzaSyDaPoiao4FyQaS1GktPCZ-mtkoiSdhSuoY",
  "authDomain": "temp-fastapi-7b328.firebaseapp.com",
  "databaseURL": "https://temp-fastapi.firebaseio.com",
  "storageBucket": "temp-fastapi-7b328.appspot.com",
  "messagingSenderId": "1061926035437",
  "appId": "1:1061926035437:web:7b90ceebe36eec9f7011e4",
  "measurementId": "G-N7SNCFGBHE",
  "serviceAccount": "serviceAccountCredentials.json"
}

firebase = pyrebase.initialize_app(firebaseConfig)
