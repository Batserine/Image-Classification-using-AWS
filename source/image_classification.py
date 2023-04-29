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
