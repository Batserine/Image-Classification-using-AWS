import tensorflow.keras as keras
import numpy as np
from PIL import Image
import json
import sys
import numpy as np
import os


# Load pre-trained model
model = keras.applications.resnet50.ResNet50(weights='imagenet')

path = str(sys.argv[1])
# Load image and preprocess it
img = Image.open(path)
img = img.resize((224, 224))
img = np.array(img)
img = np.expand_dims(img, axis=0)
img = keras.applications.resnet50.preprocess_input(img)

# Make prediction
preds = model.predict(img)
decoded_preds = keras.applications.resnet50.decode_predictions(preds, top=1)[0]

# Print the top prediction
print(decoded_preds[0][1])
f = open("/home/ubuntu/classifier/output.txt","a")
print(path+" "+decoded_preds[0][1],file=f)
os.remove(path)

# Observations:

# For 20 images uploaded - 230.15 seconds response time, 30 images - 215.67 seconds.
# Unable to upload, 60 images, faced memory error. Also, unable to upload 40 images, faced looping after 26th image so need to check the maximum number of images that can be uploaded.
# Average boot time for 1 instance (not considering a delay of 30 seconds) - 71.36 seconds, 71.17 seconds, 101.26 seconds, -- 106.14 seconds, 76.10 seconds, 76.20 seconds, 60.90 seconds, 76.01 seconds, 75.92 seconds, 76.27 seconds, 76.06 seconds, 61.76 seconds, 60.86 seconds