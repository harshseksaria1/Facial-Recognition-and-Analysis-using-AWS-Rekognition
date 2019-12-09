# -*- coding: utf-8 -*-

import cv2
import logging as log
import datetime as dt
import numpy as np
import boto3
from boto.s3.connection import S3Connection
import csv

from PIL import Image, ImageDraw, ExifTags, ImageColor
from IPython.display import display
from keras.preprocessing import image

import mysql.connector as sql
import pandas as pd
import os
import io

from datetime import datetime

mydb = sql.connect(
  host="localhost",
  user="root",
  database='customer_data',
  passwd="Harsh@123",
  auth_plugin='mysql_native_password'
)
print(mydb)

maxfaces = 2

umn_red = (25,0,122)
umn_gold = (51,204,255)
green = (0,255,0)
blue = (255,0,0)

# Extract AWS credentials
with open('credentials.csv', 'r') as input:
    next(input)
    reader = csv.reader(input)
    for line in reader:
        access_key_id = line[2]
        secret_access_key = line[3]
        
#Connecting to AWS Rekognition client
client=boto3.client('rekognition',
             aws_access_key_id = access_key_id,
             aws_secret_access_key = secret_access_key,
             region_name='us-east-1')

# Encode target images for comparison
def encode_images():
    df = pd.DataFrame(columns=['fname','lname','bytes'])
    path = 'team/'
    for i in os.listdir(path):
        with open(path+i, 'rb') as source_image:
            source_bytes = source_image.read()
        fname = i.split('_')[0]
        try:
            lname = i.split('_')[1].split('.')[0]
        except:
            lname = ""
        df = df.append({'fname':fname,'lname':lname,'bytes':source_bytes}, ignore_index=True)
    return df

#target_images = encode_images()

# Face Matching
def find_face(img_bytes, aws = False):
    fname = ""
    if aws == False:
        source_bytes = target_images
        for i in range(target_images.shape[0]):
            response = client.compare_faces(SimilarityThreshold=95,
                                      SourceImage={'Bytes':source_bytes['bytes'][i]},
                                      TargetImage={'Bytes': img_bytes})
            if len(response['FaceMatches']) > 0:
                fname = source_bytes['fname'][i]
    return fname


def face_search(img_bytes, collectionId = 'msba', threshold = 90, maxFaces = 1):  
    response=client.search_faces_by_image(CollectionId=collectionId,
                                Image={'Bytes': img_bytes},
                                FaceMatchThreshold=threshold,
                                MaxFaces=maxFaces)
    try:
        img_file = response['FaceMatches'][0]['Face']['ExternalImageId']
        fname = img_file.split('_')[0]
        return fname
    except:
        return ""

video_capture = cv2.VideoCapture(0)

def change_res(width, height):
    video_capture.set(3, width)
    video_capture.set(4, height)

change_res(1920, 1080)

anterior = 0
count = 0

while True:
    if not video_capture.isOpened():
        print('Unable to load camera.')
        sleep(5)
        pass
    
    # Capture frame-by-frame
    ret, frame = video_capture.read()
    
    pil_img = Image.fromarray(frame)
    stream = io.BytesIO()
    pil_img.save(stream, format='JPEG')
    bin_img = stream.getvalue()
    imgWidth = 1280
    imgHeight = 720
    
    #cv2.imwrite("frame%d.jpg" % count, frame)
#    i = image.load_img("frame"+str(count)+".jpg")
#    imgWidth, imgHeight = i.size  
    #draw = ImageDraw.Draw(i) 
   
#    with open("frame"+str(count)+".jpg", 'rb') as source_image:
#        source_bytes = source_image.read()
#    count += 1
    
    response = client.detect_faces(
        Image={
            'Bytes': bin_img,
        },
        Attributes=['ALL']
    )
    
    for faceDetail in response['FaceDetails'][:maxfaces]:
        print('The detected face is a ' + str(faceDetail['Gender']['Value']) + ' between ' + str(faceDetail['AgeRange']['Low']) 
              + ' and ' + str(faceDetail['AgeRange']['High']) + ' years old')
        age_range = "Age: %s - %s" % (faceDetail['AgeRange']['Low'], faceDetail['AgeRange']['High'])
        age_av = int((faceDetail['AgeRange']['High'] + faceDetail['AgeRange']['Low'])/2)
        age_display = "You look %d" % (age_av)
        
        box = faceDetail['BoundingBox']
        left = imgWidth * box['Left']
        top = imgHeight * box['Top']
        width = imgWidth * box['Width']
        height = imgHeight * box['Height']
        print(left,top,width,height)
        
        x = int(left)
        y = int(top)
        w = int(width)
        h = int(height)
        
        cv2.rectangle(frame, (x, y), (x+w, y+h), green, 2)
#        cv2.putText(frame, "Number of faces detected: "+ \
#                    str(len(response['FaceDetails'])), (50,50), \
#                    cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)
        cv2.putText(frame, age_display ,(x+w+30, y+int(h/2)-15), \
                    cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red,1,1)
        
        name = face_search(bin_img)
        
        comment_x = x+w+30
        comment_y = y+int(h/2)+15
                
        if faceDetail['Eyeglasses']['Value'] == True:
            cv2.putText(frame, "Nice pair of glasses " + name + "!", \
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)
        elif faceDetail['Gender']['Value'] == 'Female':
            cv2.putText(frame, "Hey there " + name + "! You look pretty today", \
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)
        elif faceDetail['Mustache']['Value'] == True:
            cv2.putText(frame, "Hello Sire! Great Mustache", \
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)
        elif faceDetail['Beard']['Value'] == True:
            cv2.putText(frame, "Hello Sire! Magnificant Beard", \
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)
        elif faceDetail['Gender']['Value'] == 'Male':
            cv2.putText(frame, "Hey there " + name + "! You look handsome today", 
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)
            
        if faceDetail['Smile']['Value'] == True:
            cv2.putText(frame, "Beautiful Smile!", \
                        (comment_x,comment_y+30), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)

            
        sentiment = ""
        for emotion in faceDetail["Emotions"]:
            if emotion["Confidence"] > 90:
                print("Customer is ",emotion["Type"])
                sentiment = emotion["Type"]
                
    
        now = datetime.now()
        #name
        ageLow = faceDetail['AgeRange']['Low']
        ageHigh = faceDetail['AgeRange']['High']
        gender = faceDetail['Gender']['Value']
        #sentiment
        glassess = faceDetail['Eyeglasses']['Value']
        beard = faceDetail['Beard']['Value']
        #preferences
        numPeople = len(response['FaceDetails'])
        
        mycursor = mydb.cursor()

        sql = "INSERT INTO logs (timest, name, ageLow, ageHigh, gender, emotion, glassess, beard, numPeople)" + \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (now, name, ageLow, ageHigh, gender, sentiment, glassess, beard, numPeople)
        
        mycursor.execute(sql, val)

        mydb.commit()

        print(mycursor.rowcount, "record inserted.")

#        leaderboard_query = "SELECT count(timest) timespent" + \
#                        " FROM logs" + \
#                        " WHERE name = " + str(name)
#                        
#        leaderboard = pd.read_sql(leaderboard_query, mydb)
#    
#    cv2.putText(frame, "Time Spent at Booth", \
#                    (50,200 - 30), \
#                    cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)
#    
#    cv2.putText(frame, str(leaderboard['name'][i]) + " - " + \
#                str(leaderboard['timespent'][i]) + " seconds", \
#                (50,200 + i*30), \
#                cv2.FONT_HERSHEY_SIMPLEX, 1, umn_red, 1)
        

    cv2.imshow('Video', frame)
    key = cv2.waitKey(1) & 0xFF
      
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    # Display the resulting frame
    cv2.imshow('Video', frame)
    
# When everything is done, release the capture
# Define the codec and create VideoWriter object
video_capture.release()
cv2.destroyAllWindows()