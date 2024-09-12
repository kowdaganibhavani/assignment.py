import os
import cv2
from moviepy.editor import VideoFileClip
import requests
from fastapi import FastAPI, Depends, UploadFile, File, Form
from fastapi.security.oauth2 import OAuth2PasswordBearer
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session
from pydantic import BaseModel


from dotenv import load_dotenv
load_dotenv()


database = "sqlite:///./test.db" 
engine = create_engine(database)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    token = Column(String, unique=True, index=True)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify(token):
    try:
        idinfo = id_token.verify(token, google_requests.Request())
        return idinfo
    except ValueError:
        return None


app = FastAPI()

async def processgif(video_file, text):
    video = VideoFileClip(video_file.file)
    

    video = video.fx(vfx.text, text)

    gif_path = f"/tmp/{video_file.filename}.gif"
    video.write_gif(gif_path)
    
    return gif_path


def uploadgiphy(gif_path):
    api_key = os.getenv("GIPHY_API_KEY")
    url = "https://upload.giphy.com/v1/gifs"
    files = {'file': open(gif_path, 'rb')}
    data = {'api_key': api_key}

    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    return result['data']['url'] if 'data' in result else None

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...), text: str = Form(...), db: Session = Depends(get_db)):
    gif_path = await processgif(file, text)

    giphy_url = uploadgiphy(gif_path)

    return {"gif_url": gif_path, "giphy_url": giphy_url}

@app.post("/login/")
async def login(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.token == token).first()
    if not user:
    
        google_data = verify(token)
        if google_data:

            new_user = User(email=google_data["email"], token=token)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        return {"error": "Invalid token"}
    return user


@app.post("/subscribe/")
async def subscribe(user: User = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    return {"message": "Subscription success"}

@app.get("/")
async def root():
    return {"message": "Video-to-GIF app running"}
