import os
from datetime import datetime
from datetime import timedelta
import cv2
import numpy as np

mean_digs = None

def load_averages():
  global mean_digs
  mean_digs = [None for i in range(10)]
  for i in range(10):
    folder = '../classify-digits/data/' + str(i)
    if os.path.isdir(folder):
      dig_images = [cv2.imread(folder + '/' + digimg_name, 0) for digimg_name in os.listdir(folder)]
      if len(dig_images) == 0:
        continue
      mean_digs[i] = np.mean(dig_images, axis=0, dtype='uint32').astype('uint8')

def extrat_number_from_img(img):
  num = 0
  for digit_img in split_num_img_to_digits(img):
    digit = digit_img_to_num(digit_img)
    if digit != None:
      num *= 10
      num += digit
  return num

def split_num_img_to_digits(img):
  img_processed = cv2.threshold(img, 191, 255, cv2.THRESH_BINARY_INV)[1]
  img = cv2.bitwise_not(img)
  images = []
  start_index = 0
  while start_index < img.shape[1]:
    digit_index_range = find_next_digit_index_range(img_processed, start_index)
    if digit_index_range == None:
      break
    start_index = digit_index_range[1] + 1

    digit_image = np.zeros((8, 5), np.uint8)
    width = digit_index_range[1] - digit_index_range[0] + 1

    if width < 3:
      continue

    digit_image[0:8, 5-width:5] = img[0:8, digit_index_range[0]:digit_index_range[1] + 1]
    images.append(digit_image)
  return images

def find_next_digit_index_range(img, start_index):
  result = None
  for i in range(start_index, img.shape[1]):
    if column_contains_pixel(img, i):
      result = (i, i)
      break

  if result == None:
    return None

  for i in range(result[0] + 1, min(result[0] + 5, img.shape[1])):
    if column_contains_pixel(img, i):
      result = (result[0], i)
    else:
      break

  return result

def column_contains_pixel(img, column):
  for i in range(img.shape[0]):
    if img[i, column] > 0:
      return True
  return False

def digit_img_to_num(img):
  for guess_dig in range(10):
    if mean_digs[guess_dig] is None:
      continue
    if cv2.matchTemplate(img, mean_digs[guess_dig], cv2.TM_CCOEFF_NORMED)[0][0] >= 0.95:
      return guess_dig
  raise 'UNKNOWN DIGIT'

load_averages()
img_names = os.listdir('../images')
img_names.sort()
start_date_parts = raw_input("What's the date of the first data point in " + img_names[0] + '? ').split('-')
start_date = datetime(int(start_date_parts[0]), int(start_date_parts[1]), int(start_date_parts[2]))

all_data = {}

for img_name in img_names:
  print img_name
  img_path = '../images/' + img_name
  img = cv2.imread(img_path, 0)

  lower_cost_image = img[337:345, 25:48]
  upper_cost_image = img[7:15, 25:48]
  lower = extrat_number_from_img(lower_cost_image)
  upper = extrat_number_from_img(upper_cost_image)

  processed_image = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]
  kernel = np.ones((4,4), np.uint8)
  processed_image = cv2.erode(processed_image, kernel, iterations=1)

  h, w = processed_image.shape[:2]

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

  if best_day_skip > 1:
    print 'Day skip of ' + str(best_day_skip) + ' found. Delta was ' + str(best_delta)

  start_date += timedelta(days=best_day_skip)

  for index, value in enumerate(values):
    date_string = (start_date + timedelta(days=index)).strftime('%Y-%m-%d')
    if not date_string in all_data:
      all_data[date_string] = []
    all_data[date_string].append(value)

dates = [x for x in all_data]
dates.sort()
output_file = open('output.csv', 'w')
output_file.write("Date,Fuel Cost\n")
for date in dates:
  output_file.write(date)
  output_file.write(',')
  output_file.write(str(round(np.mean(all_data[date]), 2)))
  output_file.write("\n")
output_file.close()
