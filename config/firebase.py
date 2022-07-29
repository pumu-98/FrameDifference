from pyrebase import pyrebase

firebaseConfig = {
  "projectId": "temp-fastapi",
  "apiKey": "AIzaSyAwLxbgLHrxD5H8ngdOdeDW7gwozUNBn-Y",
  "authDomain": "temp-fastapi.firebaseapp.com",
  "databaseURL": "https://temp-fastapi.firebaseio.com",
  "storageBucket": "temp-fastapi.appspot.com",
  "messagingSenderId": "276121432901",
  "appId": "1:276121432901:web:a8712f97f6a735679e442c",
  "measurementId": "G-ZH2D51TR7P",
  "serviceAccount": "serviceAccountCredentials.json"
}

firebase = pyrebase.initialize_app(firebaseConfig)