import logging

import cloudinary.uploader
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
        try:
            video = self.get_object()
            analyzer = NvidiaAnalyzer()

            # Download video from Cloudinary URL and analyze
            logger.info(f"Analyzing video: {video.video_url}")
            result = analyzer.analyze_video(video.video_url)

            # Update video object with analysis results
            video.analysis_result = result
            video.save()

            return Response(result)

        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
