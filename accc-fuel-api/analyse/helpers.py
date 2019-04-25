from datetime import datetime, timedelta

def datetime_from_string(date_string):
  date_parts = date_string.split('-')
  return datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))

def s3_key_from_region_type_date(region_type, date):
  return region_type + '/' + str(date.year) + '/' + date.strftime('%Y-%m-%d') + '.png'
