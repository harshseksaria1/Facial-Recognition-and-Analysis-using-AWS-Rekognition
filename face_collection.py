# -*- coding: utf-8 -*-
import boto3
from boto.s3.connection import S3Connection
import csv

def create_collection(collection_id):

    client=boto3.client('rekognition',
                     aws_access_key_id = access_key_id,
                     aws_secret_access_key = secret_access_key,
                     region_name='us-east-1')

    #Create a collection
    print('Creating collection:' + collection_id)
    response=client.create_collection(CollectionId=collection_id)
    print('Collection ARN: ' + response['CollectionArn'])
    print('Status code: ' + str(response['StatusCode']))
    print('Done...')

def list_collections():

    max_results=2
    
    client=boto3.client('rekognition',
                     aws_access_key_id = access_key_id,
                     aws_secret_access_key = secret_access_key,
                     region_name='us-east-1')

    #Display all the collections
    print('Displaying collections...')
    response=client.list_collections(MaxResults=max_results)
    collection_count=0
    done=False
    
    while done==False:
        collections=response['CollectionIds']

        for collection in collections:
            print (collection)
            collection_count+=1
        if 'NextToken' in response:
            nextToken=response['NextToken']
            response=client.list_collections(NextToken=nextToken,MaxResults=max_results)
            
        else:
            done=True

    return collection_count   

def add_faces_to_collection(bucket,photo,collection_id):

    client=boto3.client('rekognition',
                     aws_access_key_id = access_key_id,
                     aws_secret_access_key = secret_access_key,
                     region_name='us-east-1')

    response=client.index_faces(CollectionId=collection_id,
                                Image={'S3Object':{'Bucket':bucket,'Name':photo}},
                                ExternalImageId=photo,
                                MaxFaces=1,
                                QualityFilter="AUTO",
                                DetectionAttributes=['ALL'])

    print ('Results for ' + photo) 	
    print('Faces indexed:')						
    for faceRecord in response['FaceRecords']:
         print('  Face ID: ' + faceRecord['Face']['FaceId'])
         print('  Location: {}'.format(faceRecord['Face']['BoundingBox']))

    print('Faces not indexed:')
    for unindexedFace in response['UnindexedFaces']:
        print(' Location: {}'.format(unindexedFace['FaceDetail']['BoundingBox']))
        print(' Reasons:')
        for reason in unindexedFace['Reasons']:
            print('   ' + reason)
    return len(response['FaceRecords'])

def list_faces_in_collection(collection_id):


    maxResults=2
    faces_count=0
    tokens=True

    client=boto3.client('rekognition')
    response=client.list_faces(CollectionId=collection_id,
                               MaxResults=maxResults)

    print('Faces in collection ' + collection_id)

 
    while tokens:

        faces=response['Faces']

        for face in faces:
            print (face)
            faces_count+=1
        if 'NextToken' in response:
            nextToken=response['NextToken']
            response=client.list_faces(CollectionId=collection_id,
                                       NextToken=nextToken,MaxResults=maxResults)
        else:
            tokens=False
    return faces_count   

def index_faces(bucket, photo, collection_id):
    conn = S3Connection(access_key_id,secret_access_key)
    bucket_conn = conn.get_bucket('trendsnew')
    for key in bucket_conn.list():
        photo=key.name
        indexed_faces_count=add_faces_to_collection(bucket, photo, collection_id)
        print("Faces indexed count: " + str(indexed_faces_count))

def face_search(collectionId, img_bytes, threshold = 90, maxFaces = 2):
    client=boto3.client('rekognition',
                     aws_access_key_id = access_key_id,
                     aws_secret_access_key = secret_access_key,
                     region_name='us-east-1')

  
    response=client.search_faces_by_image(CollectionId=collectionId,
                                Image={'Bytes': img_bytes},
                                FaceMatchThreshold=threshold,
                                MaxFaces=maxFaces)

    return response

with open('credentials.csv', 'r') as input:
    next(input)
    reader = csv.reader(input)
    for line in reader:
        access_key_id = line[2]
        secret_access_key = line[3]

collection_id='msba'
#create_collection(collection_id)
collection_count=list_collections()
print("collections: " + str(collection_count))

bucket='trendsnew'
# index_faces(bucket, photo, collection_id)

faces_count=list_faces_in_collection(collection_id)
print("faces count: " + str(faces_count))




