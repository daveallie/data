import os
import numpy as np
import cv2
import uuid

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

def ask_image(dig_image):
  cv2.imshow('image', dig_image)
  key = cv2.waitKey(0)
  cv2.destroyAllWindows()
  if key - 48 > 9 or key - 48 < 0:
    return 10
  else:
    return key - 48

if not os.path.isdir('./data'):
  os.mkdir('./data')

mean_digs = [None for i in range(10)]

if not os.path.isdir('./data/skipped'):
  os.mkdir('./data/skipped')

for i in range(10):
  folder = './data/' + str(i)
  if not os.path.isdir(folder):
    os.mkdir(folder)
  dig_images = [cv2.imread(folder + '/' + digimg_name, 0) for digimg_name in os.listdir(folder)]

  if len(dig_images) == 0:
    continue
  mean_digs[i] = np.mean(dig_images, axis=0, dtype='uint32').astype('uint8')

done_file_path = './data/done.txt'
threshold = 0.95
open(done_file_path, 'a').close()

image_names = os.listdir('../images')
image_names.sort()

for image_name in image_names:
  print image_name
  done_file = open(done_file_path, 'r')
  if image_name in done_file.read().split("\n"):
    done_file.close()
    continue
  done_file.close()

  img_path = '../images/' + image_name
  img = cv2.imread(img_path, 0)
  img_digs = [[] for i in range(11)]

  for i in range(7):
    for dig_image in np.flip(split_num_img_to_digits(img[7 + i*55:15 + i*55, 25:48]), 0):
      dig = None

      try:
        for guess_dig in range(10):
          if cv2.matchTemplate(dig_image, mean_digs[guess_dig], cv2.TM_CCOEFF_NORMED)[0][0] >= threshold:
            print 'GUESSED' + str(guess_dig)
            dig = guess_dig
            break
      except cv2.error:
        print 'failed'

      if dig == None:
        dig = ask_image(dig_image)

      img_digs[dig].append(dig_image)

  for i in range(10):
    for dig_image in img_digs[i]:
      cv2.imwrite('./data/' + str(i) + '/' + image_name.split('.')[0] + '-' + str(uuid.uuid4()) + '.png', dig_image)

  for dig_image in img_digs[10]:
    cv2.imwrite('./data/skipped/' + image_name.split('.')[0] + '-' + str(uuid.uuid4()) + '.png', dig_image)

  done_file = open(done_file_path, 'a')
  done_file.write(image_name + "\n")
  done_file.close()
