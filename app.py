from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import boto3
import uuid
import os
from dotenv import load_dotenv

from botocore.exceptions import NoCredentialsError


load_dotenv()

# AWS Configuration
S3_UPLOAD_BUCKET = os.getenv("S3_UPLOAD_BUCKET")
S3_OUTPUT_BUCKET = os.getenv("S3_OUTPUT_BUCKET")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

AWS_REGION = os.getenv("AWS_REGION")

# Set up S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Set up DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
dynamo_table = dynamodb.Table(DYNAMODB_TABLE)


# FastAPI configurations

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """
    Generate a pre-signed URL for an S3 object.

    :param bucket_name: Name of the S3 bucket.
    :param object_key: Key of the object in the S3 bucket.
    :param expiration: Time in seconds for the pre-signed URL to remain valid.
    :return: Pre-signed URL as a string. If error, returns None.
    """
    try:
        # Generate the pre-signed URL
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration
        )
        return presigned_url
    except NoCredentialsError:
        print("AWS credentials not found.")
        return None
    except Exception as e:
        print(f"Error generating pre-signed URL: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload/")
async def upload_file(file: UploadFile):
    if file.content_type not in ["image/jpeg", "image/png"]:
        return {"error": "Invalid file type. Only JPEG and PNG are allowed."}
    try:
        # Upload image to S3
        file_key = f"{uuid.uuid4()}-{file.filename}"
        s3_client.upload_fileobj(file.file, S3_UPLOAD_BUCKET, file_key)
        success_message = "Image uploaded successfully!"

        # Save metadata to DynamoDB
        dynamo_table.put_item(
            Item={
                "image_id": file_key,
                "filename": file.filename,
                "status": "uploaded",
            }
        )

        response = RedirectResponse(url=f"/gallery/?message={success_message}", status_code=303)
    except Exception as e:
        print(f"------- Unable to upload images")
        print(f"------- ERROR: {e}")
        response = {"message": "Image uploaded failed!"}

    return response


@app.get("/gallery/", response_class=HTMLResponse)
def gallery(request: Request):
    images = []
    try:
        # List uploaded images from S3
        response = s3_client.list_objects_v2(Bucket=S3_UPLOAD_BUCKET)
        if "Contents" in response:
            images = [
                generate_presigned_url(S3_UPLOAD_BUCKET, obj["Key"])
                for obj in response["Contents"]
            ]
    except Exception as e:
        print(f"------- Unable to retrieve gallery")
        print(f"------- ERROR: {e}")

    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})


@app.get("/processed/", response_class=HTMLResponse)
def processed_images(request: Request):
    processed = []
    try:
        # List uploaded images from S3
        response = s3_client.list_objects_v2(Bucket=S3_OUTPUT_BUCKET)
        if "Contents" in response:
            processed = [
                generate_presigned_url(S3_OUTPUT_BUCKET, obj["Key"])
                for obj in response["Contents"]
            ]
    except Exception as e:
        print(f"------- Unable to retrieve processed images")
        print(f"------- ERROR: {e}")

    return templates.TemplateResponse("processed.html", {"request": request, "processed": processed})
