import os
import json
from PIL import Image
import exifread


def process_image(image_path, image_output_dir, metadata_output_dir):
    """
    Converts an image to grayscale PNG, extracts essential metadata and general file info, and saves outputs.

    Args:
        image_path (str): Path to the input image file.
        image_output_dir (str): Directory to save the processed image.
        metadata_output_dir (str): Directory to save the metadata JSON.

    Returns:
        dict: Extracted metadata and general file info from the image.
    """
    # Ensure output directories exist
    os.makedirs(image_output_dir, exist_ok=True)
    os.makedirs(metadata_output_dir, exist_ok=True)

    # Extract file name without extension
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    # Paths for output files
    processed_image_path = os.path.join(image_output_dir, f"{base_name}_processed.png")
    metadata_path = os.path.join(metadata_output_dir, f"{base_name}_metadata.json")

    # General file information
    general_info = {}

    try:
        with Image.open(image_path) as img:
            # Get image dimensions
            general_info["ImageWidth"] = img.width
            general_info["ImageHeight"] = img.height

            # Get file size
            general_info["FileSize"] = os.path.getsize(image_path)

            # Get file format
            general_info["Format"] = img.format

            # Save grayscale image
            grayscale_image = img.convert("L")  # Convert to grayscale
            grayscale_image.save(processed_image_path, format="PNG")
            print(f"Grayscale image saved to: {processed_image_path}")
    except Exception as e:
        print(f"Error processing image: {e}")
        return

    # Essential metadata
    essential_metadata = {}
    try:
        with open(image_path, 'rb') as img_file:
            tags = exifread.process_file(img_file)
            essential_metadata = {
                "ImageDescription": tags.get("Image ImageDescription", "N/A"),
                "Make": tags.get("Image Make", "N/A"),
                "Model": tags.get("Image Model", "N/A"),
                "Orientation": tags.get("Image Orientation", "N/A"),
                "XResolution": tags.get("Image XResolution", "N/A"),
                "YResolution": tags.get("Image YResolution", "N/A"),
                "ResolutionUnit": tags.get("Image ResolutionUnit", "N/A"),
                "DateTime": tags.get("Image DateTime", "N/A"),
                "ExposureTime": tags.get("EXIF ExposureTime", "N/A"),
                "FNumber": tags.get("EXIF FNumber", "N/A"),
                "ISOSpeedRatings": tags.get("EXIF ISOSpeedRatings", "N/A"),
                "FocalLength": tags.get("EXIF FocalLength", "N/A"),
                "ColorSpace": tags.get("EXIF ColorSpace", "N/A"),
                "ExifImageWidth": tags.get("EXIF ExifImageWidth", "N/A"),
                "ExifImageLength": tags.get("EXIF ExifImageLength", "N/A"),
            }

        # Convert metadata values to string
        essential_metadata = {key: str(value) for key, value in essential_metadata.items()}
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return

    # Merge general info and essential metadata
    combined_metadata = {**general_info, **essential_metadata}

    # Save metadata to JSON
    try:
        with open(metadata_path, "w") as json_file:
            json.dump(combined_metadata, json_file, indent=4)
            print(f"Metadata JSON saved to: {metadata_path}")
    except Exception as e:
        print(f"Error saving metadata JSON: {e}")
        return

    return combined_metadata


# Example Usage
if __name__ == "__main__":
    # Input image path
    image_path = r"C:\Users\Rubayet Mahmud\Downloads\Images\rmm_2016.jpg"

    # Output directories
    image_output_dir = r"C:\Users\Rubayet Mahmud\Downloads\Images\processed\images\\"
    metadata_output_dir = r"C:\Users\Rubayet Mahmud\Downloads\Images\processed\metadata\\"

    # Process the image
    metadata = process_image(image_path, image_output_dir, metadata_output_dir)
    print("Extracted Metadata:", metadata)
