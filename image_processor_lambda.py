import json
import boto3
from PIL import Image
from io import BytesIO
from datetime import datetime

# Initialize AWS services
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# DynamoDB table name
dynamo_table_name = "rmm-sls-image-metadata"
table = dynamodb.Table(dynamo_table_name)

# S3 bucket names
source_bucket = "rmm-sls-image-upload"
destination_bucket = "rmm-sls-image-output"


def lambda_handler(event, context):
    # Log the event for debugging
    print("-------------Received event: " + json.dumps(event, indent=2))

    # Extract S3 bucket name and object key
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    # Retrieve the image from S3
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        image_data = response['Body'].read()
    except Exception as e:
        print(f"-------------Error retrieving image from S3: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error retrieving image from S3.')
        }

    # Open image with Pillow
    try:
        image = Image.open(BytesIO(image_data))

        # Extract image metadata
        image_metadata = {
            "Format": image.format,
            "Mode": image.mode,
            "Size": image.size,
            "ImageWidth": image.width,
            "ImageHeight": image.height,
            "UploadTimestamp": datetime.utcnow().isoformat()
        }

        # Save image metadata to DynamoDB
        try:
            table.put_item(Item={
                'id': 1,
                'image_id': object_key,
                'metadata': image_metadata
            })
            print(f"------------- Metadata for Image {object_key} extracted and saved to {dynamo_table_name}.")

        except Exception as e:
            print(f"-------------Error saving metadata to DynamoDB: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps('Error saving metadata to DynamoDB.')
            }

        # Convert the image to grayscale and save as PNG
        grayscale_image = image.convert('L')  # Convert to grayscale
        png_image = BytesIO()
        grayscale_image.save(png_image, format='PNG')
        png_image.seek(0)  # Reset pointer to start of file

        # Upload the converted image to the destination S3 bucket
        destination_key = f"grayscale/{object_key.split('/')[-1].split('.')[0]}.png"
        try:
            s3_client.put_object(Body=png_image, Bucket=destination_bucket, Key=destination_key)
        except Exception as e:
            print(f"------------- Error uploading image to S3: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps('Error uploading image to S3.')
            }

        print(f"------------- Image {object_key} processed and saved to {destination_key}.")
        return {
            'statusCode': 200,
            'body': json.dumps('Image processed successfully!')
        }

    except Exception as e:
        print(f"-------------Error processing image: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing image.')
        }
