import boto3
from botocore.client import Config
from upload_file import upload_file,download_file,get_file_output_from_s3,send_message
from werkzeug.utils import secure_filename
import os
import time
import subprocess

BUCKET_NAME='aws-input-cap'
UPLOAD_FOLDER = './upload_dir/'
OUTPUT_BUCKET_NAME = 'aws-output-cap'

from flask import Flask, render_template, request
app = Flask(__name__)
app.debug=True
from werkzeug.utils import secure_filename


@app.route('/')
def home():
    return render_template("app.html")
@app.route('/upload',methods=['post'])


def upload():
    # Clear previous output results
    # output_dict.clear()
    if request.method == 'POST':
        start_time = time.time()
        msg="Upload Not Done ! "
        files = request.files.getlist('file')
        output_dict = {}
        for file in files:
            if file:
                try:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    upload_file(filename)
                    send_message(filename)

                    msg = "Upload Done ! "
                except Exception as e:
                    print(e)

        download_file()
        for file in files:
            if file:
                try:
                    filename= secure_filename(file.filename)
                    # print(filename)
                    k = get_file_output_from_s3(bucket=OUTPUT_BUCKET_NAME,filename = filename)
                    print("op filename:",k)
                    while k=="":
                        k = get_file_output_from_s3(bucket=OUTPUT_BUCKET_NAME,filename=filename)
                        # print("k",k) debugging
                    output_dict[filename] = k
                except Exception as e:
                    print(e)
        end_time = time.time()
        response_time = end_time - start_time
        print("Response time: {:.2f} seconds".format(response_time))
        return render_template("app.html",msg =msg,output = output_dict)


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0",port=5000)

