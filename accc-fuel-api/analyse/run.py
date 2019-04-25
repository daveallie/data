from datetime import timedelta
import numpy as np
import cv2
from aws_helpers import check_if_run_needed, get_processing_date, get_last_10_images, batch_write_items, get_start_date
from analysis_helpers import extract_number_from_img

region_types = ['adelaide/ulp', 'brisbane/ulp', 'melbourne/ulp', 'perth/ulp', 'sydney/e10']

def run(region_type, processing_date):
  images = get_last_10_images(region_type, processing_date)
  images = [im for im in images if im['img'] is not None]
  start_date = get_start_date(images[0]['key'])

  all_data = {}
  img_start_dates = {}

  for img_data in images:
    img = img_data['img']
    img_key = img_data['key']
    lower_cost_image = img[337:345, 25:48]
    upper_cost_image = img[7:15, 25:48]
    lower = extract_number_from_img(lower_cost_image)
    upper = extract_number_from_img(upper_cost_image)

    processed_image = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]
    kernel = np.ones((4, 4), np.uint8)
    processed_image = cv2.erode(processed_image, kernel, iterations=1)
    contours0 = cv2.findContours(processed_image.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)[0]
    moments  = [cv2.moments(cnt) for cnt in contours0]
    centroids = [(m['m10'] / m['m00'], m['m01'] / m['m00']) for m in moments]
    centroids.sort(key=lambda tup: tup[0])

    # 10 is the whitespace above the graph and 330 is the size of the graph
    values = [(1 - (c[1] - 10.0)/330.0) * (upper - lower) + lower for c in centroids]

    best_delta = 1000000000
    best_day_skip = 0
    for day_skip in range(10):
      day_skip_delta = 0
      for index, value in enumerate(values):
        date_string = (start_date + timedelta(days=index + day_skip)).strftime('%Y-%m-%d')
        if date_string in all_data:
          day_skip_delta += abs(value - np.mean(all_data[date_string]))

      if day_skip_delta < best_delta:
        best_delta = day_skip_delta
        best_day_skip = day_skip

    start_date += timedelta(days=best_day_skip)
    img_start_dates[img_key] = start_date.strftime('%Y-%m-%d')

    for index, value in enumerate(values):
      date_string = (start_date + timedelta(days=index)).strftime('%Y-%m-%d')
      if not date_string in all_data:
        all_data[date_string] = []
      all_data[date_string].append(value)

  all_dates = [x for x in all_data]
  all_dates.sort()
  last_10_days = all_dates[-10:]

  dynamo_items = [{
    'PutRequest': {
        'Item': {
            'RegionFuelDate': {'S': region_type + '/' + date},
            'Cost': {'N': str(round(np.mean(all_data[date]), 2))}
        }
    }
  } for date in last_10_days]
  batch_write_items('accc-fuel-data', dynamo_items)

  dynamo_items = [{
    'PutRequest': {
        'Item': {
            'ImageKey': {'S': img_key},
            'Date': {'S': img_start_dates[img_key]}
        }
    }
  } for img_key in img_start_dates]
  batch_write_items('accc-fuel-image-dates', dynamo_items)

  dynamo_items = [{'PutRequest': {'Item': { 'RegionFuel': {'S': region_type}, 'Date': {'S': processing_date.strftime('%Y-%m-%d')}}}}]
  batch_write_items('accc-fuel-data-latest-solved', dynamo_items)


def handler(event, context):
  for region_type in region_types:
    processing_date = get_processing_date(region_type)
    if check_if_run_needed(region_type, processing_date):
      run(region_type, processing_date)

handler(None, None)
