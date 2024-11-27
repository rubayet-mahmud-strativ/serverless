from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import boto3
import uuid
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv


load_dotenv()

# AWS Configuration
S3_UPLOAD_BUCKET = os.getenv("S3_UPLOAD_BUCKET")
S3_OUTPUT_BUCKET = os.getenv("S3_OUTPUT_BUCKET")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
AWS_REGION = os.getenv("AWS_REGION")

# Set up S3 client
s3_client = boto3.client("s3", region_name=AWS_REGION)

# Set up DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
dynamo_table = dynamodb.Table(DYNAMODB_TABLE)


# FastAPI configurations

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload/")
async def upload_file(file: UploadFile):
    if file.content_type not in ["image/jpeg", "image/png"]:
        return {"error": "Invalid file type. Only JPEG and PNG are allowed."}
    try:
        # Upload image to S3
        tz = pytz.timezone('UTC')  # You can replace 'UTC' with your desired timezone
        timestamp = datetime.now(tz).strftime("%Y%m%dT%H%M%S%z")
        file_key = f"{uuid.uuid4()}/{timestamp}/{file.filename}"
        s3_client.upload_fileobj(file.file, S3_UPLOAD_BUCKET, file_key)
        success_message = "Image uploaded successfully!"

        # Save metadata to DynamoDB
        dynamo_table.put_item(
            Item={
                "id": file_key,
                "filename": file.filename,
                "status": "uploaded",
            }
        )
        # response = {"message": "Image uploaded successfully!", "file_key": file_key}
        response = RedirectResponse(url="/gallery/", status_code=303)
        return RedirectResponse(url=f"/gallery/?message={success_message}", status_code=303)
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
            images = [obj["Key"] for obj in response["Contents"]]
            images = [f"https://{S3_UPLOAD_BUCKET}.s3.amazonaws.com/{obj['Key']}" for obj in response["Contents"]]
    except Exception as e:
        print(f"------- Unable to retrieve gallery")
        print(f"------- ERROR: {e}")

    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})


@app.get("/processed/", response_class=HTMLResponse)
def processed_images(request: Request):
    processed = []
    try:
        # Fetch processed images from DynamoDB
        response = dynamo_table.scan()
        processed = [
            item for item in response.get("Items", []) if item.get("status") == "processed"
        ]
    except Exception as e:
        print(f"------- Unable to retrieve processed images")
        print(f"------- ERROR: {e}")

    return templates.TemplateResponse("processed.html", {"request": request, "processed": processed})
