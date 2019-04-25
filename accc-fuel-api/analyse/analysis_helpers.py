from datetime import datetime, timedelta
import cv2
import numpy as np

mean_digs = [
  np.array([[ 15, 183, 209, 185,  17], [147, 111,   0, 113, 145], [221,  25,   0,  23, 221], [245,   0,   0,   0, 245], [245,   0,   0,   0, 245], [219,  23,   0,  23, 221], [147, 111,   0, 111, 147], [ 19, 189, 211, 185,  17]], dtype=np.uint8),
  np.array([[  0,   0,   0,  23, 225], [  0,   0,  55, 211, 251], [  0,   0, 163,  53, 247], [  0,   0,   0,   0, 247], [  0,   0,   0,   0, 247], [  0,   0,   0,   0, 247], [  0,   0,   0,   0, 247], [  0,   0,   0,   0, 247]], dtype=np.uint8),
  np.array([[ 41, 199, 213, 207,  51], [193,  79,   0,  61, 213], [ 93,   5,   0,  15, 241], [  0,   0,   0, 143, 161], [  0,   0, 131, 207,  15], [  3, 159, 195,  17,   0], [141, 183,   9,   0,   0], [249, 219, 207, 207, 207]], dtype=np.uint8),
  np.array([[  3, 161, 215, 207,  69], [ 95, 159,   0,  35, 227], [  0,   3,   0,  65, 211], [  0,   0, 165, 253,  77], [  0,   0,   0,  79, 209], [ 51,  33,   0,   5, 245], [113, 157,   0,  79, 193], [  7, 173, 215, 199,  37]], dtype=np.uint8),
  np.array([[  0,   0,   0,  49, 245], [  0,   0,  11, 199, 249], [  0,   0, 157,  85, 247], [  0,  85, 157,   0, 247], [ 29, 203,  11,   0, 247], [111, 219, 207, 207, 253], [  0,   0,   0,   0, 247], [  0,   0,   0,   0, 247]], dtype=np.uint8),
  np.array([[ 65, 235, 207, 207, 133], [117, 109,   0,   0,   0], [169, 189, 207, 175,  19], [153,  65,   0, 125, 169], [  0,   0,   0,  13, 241], [121,   0,   0,  13, 235], [211,  75,   0, 115, 157], [ 49, 207, 213, 179,  15]], dtype=np.uint8),
  np.array([[  9, 167, 215, 205,  33], [129, 153,   0,  93, 169], [209,  37,   0,   5,  37], [241, 111, 207, 193,  39], [247,  95,   0,  95, 199], [223,   5,   0,   5, 243], [153,  85,   0,  79, 193], [ 17, 179, 211, 203,  41]], dtype=np.uint8),
  np.array([[207, 207, 207, 223, 243], [  0,   0,   0, 189,  85], [  0,   0,  95, 175,   0], [  0,   0, 219,  43,   0], [  0,  71, 183,   0,   0], [  0, 151,  93,   0,   0], [  0, 207,  31,   0,   0], [  0, 241,   3,   0,   0]], dtype=np.uint8),
  None, # No average for 8
  None, # No average for 9
]

def column_contains_pixel(img, column):
  for i in range(img.shape[0]):
    if img[i, column] > 0:
      return True
  return False

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

def digit_img_to_num(img):
  for guess_dig in range(10):
    if mean_digs[guess_dig] is None:
      continue
    if cv2.matchTemplate(img, mean_digs[guess_dig], cv2.TM_CCOEFF_NORMED)[0][0] >= 0.95:
      return guess_dig
  raise 'UNKNOWN DIGIT'

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

def extract_number_from_img(img):
  num = 0
  for digit_img in split_num_img_to_digits(img):
    digit = digit_img_to_num(digit_img)
    if digit != None:
      num *= 10
      num += digit
  return num
