import logging
import os
import tempfile
import urllib.request
import uuid

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class NvidiaAnalyzer:
    def __init__(self):
        self.invoke_url = "https://ai.api.nvidia.com/v1/vlm/nvidia/cosmos-nemotron-34b"
        self.api_key = os.getenv("TEST_NVCF_API_KEY")
        if not self.api_key:
            raise ValueError("NVIDIA API key not found in environment variables")
        self.nvcf_asset_url = "https://api.nvcf.nvidia.com/v2/nvcf/assets"
        self.supported_formats = {
            "mp4": ["video/mp4", "video"],
            "png": ["image/png", "img"],
            "jpg": ["image/jpg", "img"],
            "jpeg": ["image/jpeg", "img"],
        }

    def download_video(self, url):
        """Download video from Cloudinary URL to temporary file"""
        try:
            temp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            logger.info(f"Downloading video from {url} to {temp.name}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }

            # Download the file
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                with open(temp.name, "wb") as out_file:
                    out_file.write(response.read())

            logger.info("Video downloaded successfully")
            return temp.name

        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            if os.path.exists(temp.name):
                os.unlink(temp.name)
            raise Exception(f"Failed to download video: {str(e)}")

    def _upload_asset(self, media_file, description):
        """Upload asset to NVIDIA's storage"""
        try:
            logger.info(f"Uploading file {media_file} to NVIDIA storage")

            with open(media_file, "rb") as data_input:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "accept": "application/json",
                }

                # Request upload URL
                authorize = requests.post(
                    self.nvcf_asset_url,
                    headers=headers,
                    json={"contentType": "video/mp4", "description": description},
                    timeout=30,
                )
                authorize.raise_for_status()
                authorize_res = authorize.json()

                # Upload to provided URL
                with open(media_file, "rb") as data_input:
                    response = requests.put(
                        authorize_res["uploadUrl"],
                        data=data_input,
                        headers={
                            "x-amz-meta-nvcf-asset-description": description,
                            "content-type": "video/mp4",
                        },
                        timeout=300,
                    )
                response.raise_for_status()

                logger.info("File uploaded successfully to NVIDIA storage")
                return uuid.UUID(authorize_res["assetId"])

        except Exception as e:
            logger.error(f"Error uploading to NVIDIA storage: {str(e)}")
            raise

    def _delete_asset(self, asset_id):
        """Delete asset from NVIDIA's storage"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        assert_url = f"{self.nvcf_asset_url}/{asset_id}"
        response = requests.delete(assert_url, headers=headers, timeout=30)
        response.raise_for_status()

    def analyze_video(self, video_url, query="Describe the scene"):
        """Main method to analyze video using NVIDIA API"""
        try:
            # Download video from Cloudinary
            temp_file = self.download_video(video_url)

            # Upload to NVIDIA
            asset_id = self._upload_asset(temp_file, "Video analysis")

            # Prepare API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "NVCF-INPUT-ASSET-REFERENCES": str(asset_id),
                "NVCF-FUNCTION-ASSET-IDS": str(asset_id),
                "Accept": "application/json",
            }

            messages = [
                {
                    "role": "user",
                    "content": f'{query} <video src="data:video/mp4;asset_id,{asset_id}" />',
                }
            ]

            payload = {
                "max_tokens": 2048,
                "temperature": 0.2,
                "top_p": 0.7,
                "seed": 50,
                "num_frames_per_inference": 8,
                "messages": messages,
                "stream": False,
                "model": "nvidia/vila",
            }

            # Make API call
            response = requests.post(self.invoke_url, headers=headers, json=payload)

            # Clean up
            self._delete_asset(asset_id)
            os.unlink(temp_file)  # Delete temporary file

            return response.json()

        except Exception as e:
            raise Exception(f"Error analyzing video: {str(e)}")


# Usage in views.py:
# analyzer = NvidiaAnalyzer()
# result = analyzer.analyze_video(video_url)
