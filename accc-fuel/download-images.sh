#!/bin/bash

AWS_PROFILE=fuel-downloader aws s3 cp --recursive s3://accc-fuel-images/brisbane/ images/
