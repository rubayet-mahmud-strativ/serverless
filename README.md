# Introduction to serverless

This app takes an image and upload directly to a S3 bucket, which triggers a lambda to output the image as a grayscales png to another s3 bucket, and stores metadata in a DynamoDB table. 

 
```
serverless/
├── app.py                        # image processor app
├── image_processor.py            # image processor function
├── image_processor_lambda.py     # image processor lambda
├── templates/
│   ├── upload.html               # Page to upload images
│   ├── gallery.html              # Page to show uploaded images
│   ├── processed.html            # Page to show processed images & metadata
├── static/
│   └── styles.css                # Optional CSS for styling
└── requirements.txt              # Dependencies

```

## To run the project:
Create a .env file from the example:
```commandline
cp .env.example .env
```
Fill the environment variables with your own value.

### Then run with:
```commandline
uvicorn app:app --reload
```
