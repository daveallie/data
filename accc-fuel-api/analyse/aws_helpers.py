from datetime import datetime, timedelta
import boto3
import cv2
import numpy as np
from helpers import datetime_from_string, s3_key_from_region_type_date

def get_processing_date(region_type):
  dynamo_response = boto3.client('dynamodb', region_name='ap-southeast-2').get_item(
    TableName='accc-fuel-data-latest-solved',
    Key={'RegionFuel': {'S': region_type}},
    AttributesToGet=['Date'],
  )

  latest_proccessed_date = datetime_from_string(dynamo_response['Item']['Date']['S'])
  return latest_proccessed_date + timedelta(days=1)

def check_if_run_needed(region_type, processing_date):
  s3_key = s3_key_from_region_type_date(region_type, processing_date)
  return len(list(boto3.resource('s3').Bucket('accc-fuel-images-2').objects.filter(Prefix=s3_key))) > 0

def get_start_date(key):
  dynamo_response = boto3.client('dynamodb', region_name='ap-southeast-2').get_item(
    TableName='accc-fuel-image-dates',
    Key={'ImageKey': {'S': key}},
    AttributesToGet=['Date'],
  )

  return datetime_from_string(dynamo_response['Item']['Date']['S'])

def get_image(key):
  obj = boto3.resource('s3').Object('accc-fuel-images-2', key).get()
  image = np.asarray(bytearray(obj['Body'].read()), dtype="uint8")
  return cv2.imdecode(image, 0)

def get_last_10_images(region_type, processing_date):
  s3_keys = [s3_key_from_region_type_date(region_type, processing_date - timedelta(days=(9-i))) for i in range(10)]

  return [
    {
      'img': get_image(s3_key),
      'key': s3_key,
    } for s3_key in s3_keys
  ]

def batch_write_items(table, items):
  boto3.client('dynamodb', region_name='ap-southeast-2').batch_write_item(RequestItems={table: items})
