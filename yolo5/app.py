import time
from pathlib import Path
from flask import Flask, request
from detect import run
import uuid
import yaml
import boto3
from loguru import logger
import os
import requests
from pymongo import MongoClient


images_bucket = os.environ['BUCKET_NAME']

## Initialize S3 and mongoDB clients
s3 = boto3.client('s3')
client = MongoClient("mongodb://localhost:27017/")
db = client["predictions"]
collection = db["prediction_summary"]


with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    # Generates a UUID for this current prediction HTTP request. This id can be used as a reference in logs to identify and track individual prediction requests.
    prediction_id = str(uuid.uuid4())

    logger.info(f'prediction: {prediction_id}. start processing')

    # Receives a URL parameter representing the image to download from S3
    img_name = request.args.get('imgName')

    # TODO download img_name from S3, store the local image path in the original_img_path variable.
    #  The bucket name is provided as an env var BUCKET_NAME.

    s3 = boto3.client('s3')
    original_img_path = Path(f'static/data/{prediction_id}/{img_name}')
    s3.download_file(images_bucket, img_name, str(original_img_path))



    logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')

    # Predicts the objects in the image
    run(
        weights='yolov5s.pt',
        data='data/coco128.yaml',
        source=original_img_path,
        project='static/data',
        name=prediction_id,
        save_txt=True
    )

    logger.info(f'prediction: {prediction_id}/{original_img_path}. done')

    # This is the path for the predicted image with labels
    # The predicted image typically includes bounding boxes drawn around the detected objects, along with class labels and possibly confidence scores.
    predicted_img_path = Path(f'static/data/{prediction_id}/{original_img_path}')

    # TODO Uploads the predicted image (predicted_img_path) to S3 (be careful not to override the original image).
    s3.upload_file(str(predicted_img_path), images_bucket, f'predicted_{img_name}')
    logger.info(f'prediction: {prediction_id}/{original_img_path}. Upload predicted img completed')



    # Parse prediction labels and create a summary
    pred_summary_path = Path(f'static/data/{prediction_id}/labels/{original_img_path.split(".")[0]}.txt')
    if pred_summary_path.exists():
        with open(pred_summary_path) as f:
            labels = f.read().splitlines()
            labels = [line.split(' ') for line in labels]
            labels = [{
                'class': names[int(l[0])],
                'cx': float(l[1]),
                'cy': float(l[2]),
                'width': float(l[3]),
                'height': float(l[4]),
            } for l in labels]

        logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')

        prediction_summary = {
            'prediction_id': prediction_id,
            'original_img_path': original_img_path,
            'predicted_img_path': predicted_img_path,
            'labels': labels,
            'time': time.time()
        }

        # TODO store the prediction_summary in MongoDB
        # i run mongodb in docker container
        # docker run -d -p 27017:27017 --name mongodb mongo

        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["predictions"]
        collection = db["prediction_summary"]
        collection.insert_one(prediction_summary)
        logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary saved to MongoDB')

        return prediction_summary
    else:
        return f'prediction: {prediction_id}/{original_img_path}. prediction result not found', 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
