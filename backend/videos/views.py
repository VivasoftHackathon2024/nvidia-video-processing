import logging
import os
import re
import time

import cloudinary
import cloudinary.api
import cloudinary.uploader
from cloudinary import CloudinaryVideo
from django.conf import settings
from moviepy import VideoFileClip
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Video
from .nvidia_analyzer import NvidiaAnalyzer
from .serializers import VideoSerializer

logger = logging.getLogger(__name__)


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def create(self, request):
        video_file = request.FILES.get("video")
        title = request.data.get("title")
        description = request.data.get("description")

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            video_file, resource_type="video", folder="video_analyzer"
        )

        # Create Video object
        video = Video.objects.create(
            title=title, description=description, video_url=upload_result["secure_url"]
        )

        return Response(VideoSerializer(video).data)

    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        # try:
        #     video = self.get_object()
        #     analyzer = NvidiaAnalyzer()

        #     # Download video from Cloudinary URL and analyze
        #     logger.info(f"Analyzing video: {video.video_url}")
        #     result = analyzer.analyze_video(video.video_url)

        #     # Update video object with analysis results
        #     video.analysis_result = result
        #     video.save()

        #     return Response(result)

        # except Exception as e:
        #     logger.error(f"Error analyzing video: {str(e)}")
        #     return Response(
        #         {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )

        """
        Splits the Cloudinary video into 30s intervals (on-the-fly) and
        analyzes each segment in a loop by calling NvidiaAnalyzer.analyze_video().
        """
        try:
            video = self.get_object()
            analyzer = NvidiaAnalyzer()

            secure_url = video.video_url
            if not secure_url:
                return Response(
                    {"error": "No video URL found in the database."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            match = re.search(r"/video/upload/(?:v\d+/)?(.+)\.\w+$", secure_url)
            if not match:
                error_msg = (
                    f"Could not parse public_id from URL: {secure_url}. "
                    "Make sure it's a valid Cloudinary video URL."
                )
                logger.error(error_msg)
                return Response(
                    {"error": error_msg}, status=status.HTTP_400_BAD_REQUEST
                )

            public_id = match.group(1)  # e.g. "folder_name/abcd1234"
            print("public_id: ", public_id)

            try:
                duration = VideoFileClip(secure_url).duration
                duration = max(int(duration), 0)
                print(f"Video duration: {duration} seconds")
                if duration == 0:
                    error_msg = "Could not retrieve video duration from Cloudinary."
                    logger.error(error_msg)
                    return Response(
                        {"error": error_msg}, status=status.HTTP_400_BAD_REQUEST
                    )
            except cloudinary.exceptions.NotFound as e:
                error_msg = f"Cloudinary resource not found for public_id: {public_id}"
                logger.error(error_msg)
                return Response({"error": error_msg}, status=status.HTTP_404_NOT_FOUND)

            MAX_CHUNK_DURATION = 30
            start_time = 0
            intervals = []

            while start_time < duration:
                end_time = min(start_time + MAX_CHUNK_DURATION, duration)
                intervals.append((start_time, end_time))
                start_time = end_time

            def build_chunk_url(original_url, start_sec, end_sec):
                """
                E.g. original_url:
                  https://res.cloudinary.com/.../upload/v1736265995/video_analyzer/ulbcownftehnh9f0ge48.mp4
                Insert "so_{start_sec},eo_{end_sec}/" after "/upload/", e.g.:
                  https://res.cloudinary.com/.../upload/so_31,eo_60/v1736265995/...
                """
                # Insert transformation right after /upload/
                return original_url.replace(
                    "/upload/", f"/upload/so_{int(start_sec)},eo_{int(end_sec)}/"
                )

            # -------------------------------------------------------------
            # 4. Loop through each interval, build a subclip URL, and analyze
            # -------------------------------------------------------------
            chunk_results = []
            chunk_count = 1
            for start_sec, end_sec in intervals:
                chunk_url = build_chunk_url(secure_url, start_sec, end_sec)
                logger.info(
                    f"Analyzing subclip: {start_sec}-{end_sec}s (URL: {chunk_url})"
                )

                print(
                    "Analyzing subclip number: ",
                    chunk_count,
                    " : ",
                    start_sec,
                    "-",
                    end_sec,
                    "s",
                )
                subclip_result = analyzer.analyze_video(chunk_url)
                chunk_results.append(
                    {
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "analysis": subclip_result,
                    }
                )

                chunk_count += 1

            # -------------------------------------------------------------
            # 5. Save / aggregate / return results
            # -------------------------------------------------------------
            # For this example, we'll just store the entire list (JSON-serializable)
            # in the `analysis_result` field.
            # Adjust as needed (flatten, combine, etc.).
            video.analysis_result = chunk_results
            video.save()

            file_path = os.path.join(settings.BASE_DIR, "chunk_results.txt")

            try:
                # Open the file in write mode and write the chunk_results
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(str(chunk_results))
                print(f"chunk_results successfully written to {file_path}")
            except Exception as e:
                # Handle exceptions, such as permission issues
                print(f"Failed to write chunk_results to file: {e}")

            print("chunk_results: ", chunk_results)

            return Response(chunk_results)

        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
