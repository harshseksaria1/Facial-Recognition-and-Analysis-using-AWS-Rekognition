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

db_connection = sql.connect(
  host="localhost",
  user="root",
  passwd="Harsh@123",
  auth_plugin='mysql_native_password'
)
print(db_connection)

umn_red = (25,0,122)
umn_gold = (51,204,255)

with open('credentials.csv', 'r') as input:
    next(input)
    reader = csv.reader(input)
    for line in reader:
        access_key_id = line[2]
        secret_access_key = line[3]
        
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

target_images = encode_images()
            
def find_face(img_bytes, aws = False):

    client=boto3.client('rekognition',
                     aws_access_key_id = access_key_id,
                     aws_secret_access_key = secret_access_key,
                     region_name='us-east-1')
    fname = ""
    if aws == False:
        source_bytes = target_images
        for i in range(target_images.shape[0]):
            response = client.compare_faces(SimilarityThreshold=95,
                                      SourceImage={'Bytes':source_bytes['bytes'][i]},
                                      TargetImage={'Bytes': img_bytes})
            if len(response['FaceMatches']) > 0:
                fname = source_bytes['fname'][i]
#            for faceMatch in response['FaceMatches']:
#                position = faceMatch['Face']['BoundingBox']
#                similarity = str(faceMatch['Similarity'])
#                print('The face at ' +
#                   str(position['Left']) + ' ' +
#                   str(position['Top']) +
#                   ' matches with ' + similarity + '% confidence')
#                if faceMatch['Similarity'] >= 90:
#                    fname = source_bytes['fname'][i]
    return fname

            
    
#    conn = S3Connection(access_key_id,secret_access_key)
#    bucket = conn.get_bucket('trendsnew')
#    
#    for key in bucket.list():
#        response=client.compare_faces(SimilarityThreshold=50,
#                                      SourceImage={'S3Object':{'Bucket':'trendsnew','Name':key.name}},
#                                      TargetImage={'Bytes': img_bytes})
#    
#        for faceMatch in response['FaceMatches']:
#            position = faceMatch['Face']['BoundingBox']
#            similarity = str(faceMatch['Similarity'])
#            print('The face at ' +
#                   str(position['Left']) + ' ' +
#                   str(position['Top']) +
#                   ' matches with ' + similarity + '% confidence')
#    
#    print(key.name)
#
#    return key.name

        

client = boto3.client('rekognition',
                     aws_access_key_id = access_key_id,
                     aws_secret_access_key = secret_access_key,
                     region_name='us-east-1')

video_capture = cv2.VideoCapture(0)
anterior = 0
count = 0

while True:
    if not video_capture.isOpened():
        print('Unable to load camera.')
        sleep(5)
        pass
    
    # Capture frame-by-frame
    ret, frame = video_capture.read()
    cv2.imwrite("frame%d.jpg" % count, frame)
    
    i = image.load_img("frame"+str(count)+".jpg")
    imgWidth, imgHeight = i.size  
    draw = ImageDraw.Draw(i) 
    
    with open("frame"+str(count)+".jpg", 'rb') as source_image:
        source_bytes = source_image.read()
    count += 1
    
    response = client.detect_faces(
        Image={
            'Bytes': source_bytes,
        },
        Attributes=['ALL']
    )
    
    
    for faceDetail in response['FaceDetails']:
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
        
        cv2.rectangle(frame, (x, y), (x+w, y+h), umn_red, 2)
        cv2.putText(frame, "Number of faces detected: "+ str(len(response['FaceDetails'])), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, umn_gold, 1)
        cv2.putText(frame, age_display ,(x-20,y-1), cv2.FONT_HERSHEY_SIMPLEX, 1,umn_red,1,1)
        
        name = find_face(source_bytes)
        
        comment_x = 30
        comment_y = 450
        
        if faceDetail['Eyeglasses']['Value'] == True:
            cv2.putText(frame, "Nice pair of glasses " + name + "!", \
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_gold, 1)
        elif faceDetail['Gender']['Value'] == 'Female':
            cv2.putText(frame, "Hey there " + name + "! You look beautiful today", \
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_gold, 1)
        elif faceDetail['Beard']['Value'] == True:
            cv2.putText(frame, "Hello Sire! Magnificant Beard", \
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_gold, 1)
        elif faceDetail['Gender']['Value'] == 'Male':
            cv2.putText(frame, "Hey there " + name + "! You look handsome today", 
                        (comment_x,comment_y), \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, umn_gold, 1)
        

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