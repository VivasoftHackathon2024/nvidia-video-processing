import logging
import os
import re
import time
import uuid

import cloudinary
import cloudinary.api
import cloudinary.uploader
from cloudinary import CloudinaryVideo
from django.conf import settings
from moviepy import VideoFileClip
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .agents.chat_agent import create_chat_agent
from .agents.summarize_agent import run_summarize_agent
from .embed import create_embedding
from .models import Video
from .nvidia_analyzer import NvidiaAnalyzer
from .serializers import VideoSerializer
from .specialised_agents.assault_agent import run_assault_agent
from .specialised_agents.crime_agent import run_crime_agent
from .specialised_agents.drug_agent import run_drug_agent
from .specialised_agents.fire_agent import run_fire_agent
from .specialised_agents.theft_agent import run_theft_agent

logger = logging.getLogger(__name__)

agent_executors = {}


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
        # SINGLE API CALL PER VIDEO
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

        # MULTIPLE API CALLS PER VIDEO DIVIDED INTO 30s INTERVALS
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
                        "start_time_seconds": start_sec,
                        "end_time_seconds": end_sec,
                        "analysis": subclip_result,
                    }
                )

                chunk_count += 1

            # -------------------------------------------------------------
            # 5. Save / aggregate / return results (Done for debugging purposes)
            # -------------------------------------------------------------
            # For this example, we'll just store the entire list (JSON-serializable)
            # in the `analysis_result` field.
            # Saving Analysis Results to the Video object
            video.analysis_result = chunk_results
            video.save()

            # -------------------------------------------------------------
            # Writing chunk_results to a file for debugging purposes

            # print("Writing chunk_results to file for debugging purposes...")
            # file_path = os.path.join(settings.BASE_DIR, "chunk_results.txt")

            # try:
            #     # Open the file in write mode and write the chunk_results
            #     with open(file_path, "w", encoding="utf-8") as file:
            #         file.write(str(chunk_results))
            #     print(f"chunk_results successfully written to {file_path}")
            # except Exception as e:
            #     # Handle exceptions, such as permission issues
            #     print(f"Failed to write chunk_results to file: {e}")

            # print("chunk_results: ", chunk_results)

            # DEBUGGING ENDS
            # -------------------------------------------------------------

            # Create embedding after analysis is complete
            print("Creating embedding for video: ", video.id)
            embedding_result = create_embedding(video.id)
            if embedding_result == -1:
                logger.warning(f"Failed to create embedding for video {video.id}")

            print("Embedding for video created: ", video.id)
            return Response(chunk_results)

        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def summarize_agent(self, request, pk=None):
        """
        Runs our specialized LangChain/LLM agent to summarize vectorized info,
        and returns the output from the agent back to the client.
        """
        try:
            video = self.get_object()

            print("Running summarize_agent for video: ", video.id)
            summary_output = run_summarize_agent(video.id)
            video.summary_result = {"summary": summary_output}
            video.save()
            print("Summary completed")

            return Response({"summary": summary_output})
        except Exception as e:
            logger.error(f"Error in summarize_agent: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def initialize_chat_agent(self, request, pk=None):
        """Initialize a chat agent for a specific video"""
        try:
            video = self.get_object()

            # Generate a unique thread ID
            print("Iniitializing Chat Agent")
            thread_id = str(uuid.uuid4())

            # Initialize the agent
            agent_executor = create_chat_agent(video_id=video.id, thread_id=thread_id)

            # Store the agent executor
            agent_executors[thread_id] = agent_executor

            print("Iniitialized Chat Agent")
            return Response({"status": "success", "thread_id": thread_id})

        except Exception as e:
            logger.error(f"Error initializing chat agent: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def chat(self, request, pk=None):
        """Chat with the initialized agent"""
        try:
            thread_id = request.data.get("thread_id")
            message = request.data.get("message")

            if not thread_id or not message:
                return Response(
                    {"error": "thread_id and message are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if thread_id not in agent_executors:
                return Response(
                    {"error": "Thread not found. Please initialize first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            agent_executor = agent_executors[thread_id]
            config = {"configurable": {"thread_id": thread_id}}

            # Collect responses from the agent
            responses = []
            for event in agent_executor.stream(
                {"messages": [{"role": "user", "content": message}]},
                stream_mode="values",
                config=config,
            ):
                msg = event["messages"][-1]
                message_dict = {
                    "role": (
                        msg.type
                        if hasattr(msg, "type")
                        else msg.__class__.__name__.replace("Message", "").lower()
                    ),
                    "content": msg.content,
                    "metadata": (
                        msg.response_metadata
                        if hasattr(msg, "response_metadata")
                        else None
                    ),
                }
                responses.append(message_dict)

            return Response({"response": responses})

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def fire_agent(self, request, pk=None):
        """
        Runs our specialized LangChain/LLM agent to detect the chances and severity of fire from the vectorized info,
        and returns the output from the agent back to the client.
        """
        try:
            video = self.get_object()

            print("Running fire_agent for video: ", video.id)
            fire_output = run_fire_agent(video.id)
            print(fire_output)
            video.fire_evaluation = {"fire_evaluation": fire_output}
            video.save()
            print("Fire Agent Analysis completed")

            return Response({"fire_evaluation": fire_output})
        except Exception as e:
            logger.error(f"Error in fire_agent: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def assault_agent(self, request, pk=None):
        """
        Runs our specialized LangChain/LLM agent to detect incidents of assault from the vectorized info,
        and returns the output from the agent back to the client.
        """
        try:
            video = self.get_object()

            print("Running assault_agent for video: ", video.id)
            assault_output = run_assault_agent(video.id)
            print(assault_output)
            video.assault_evaluation = {"assault_evaluation": assault_output}
            video.save()
            print("Assault Agent Analysis completed")

            return Response({"assault_evaluation": assault_output})
        except Exception as e:
            logger.error(f"Error in assault_agent: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def crime_agent(self, request, pk=None):
        """
        Runs our specialized LangChain/LLM agent to detect crime-related activities from the vectorized info,
        and returns the output from the agent back to the client.
        """
        try:
            video = self.get_object()

            print("Running crime_agent for video: ", video.id)
            crime_output = run_crime_agent(video.id)
            print(crime_output)
            video.crime_evaluation = {"crime_evaluation": crime_output}
            video.save()
            print("Crime Agent Analysis completed")

            return Response({"crime_evaluation": crime_output})
        except Exception as e:
            logger.error(f"Error in crime_agent: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def drug_agent(self, request, pk=None):
        """
        Runs our specialized LangChain/LLM agent to detect drug-related activities from the vectorized info,
        and returns the output from the agent back to the client.
        """
        try:
            video = self.get_object()

            print("Running drug_agent for video: ", video.id)
            drug_output = run_drug_agent(video.id)
            print(drug_output)
            video.drug_evaluation = {"drug_evaluation": drug_output}
            video.save()
            print("Drug Agent Analysis completed")

            return Response({"drug_evaluation": drug_output})
        except Exception as e:
            logger.error(f"Error in drug_agent: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def theft_agent(self, request, pk=None):
        """
        Runs our specialized LangChain/LLM agent to detect theft-related activities from the vectorized info,
        and returns the output from the agent back to the client.
        """
        try:
            video = self.get_object()

            print("Running theft_agent for video: ", video.id)
            theft_output = run_theft_agent(video.id)
            print(theft_output)
            video.theft_evaluation = {"theft_evaluation": theft_output}
            video.save()
            print("Theft Agent Analysis completed")

            return Response({"theft_evaluation": theft_output})
        except Exception as e:
            logger.error(f"Error in theft_agent: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
