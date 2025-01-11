import json
import os
from typing import List

import psycopg2
from django.db import connection
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


def create_embedding(video_id: int) -> int:
    """
    Create embeddings for a specific video's analysis results.

    Args:
        video_id (int): The ID of the video to create embeddings for

    Returns:
        int: 1 if successful, -1 if failed
    """
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

        # Connect to database
        # db_connection = psycopg2.connect(os.getenv("POSTGRES_CONNECTION"))
        # cursor = db_connection.cursor()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT analysis_result FROM videos_video WHERE id = %s", (video_id,)
            )
            row = cursor.fetchone()

        # Fetch specific video data
        # cursor.execute(
        #     "SELECT analysis_result FROM videos_video WHERE id = %s", (video_id,)
        # )
        # row = cursor.fetchone()

        if not row or not row[0]:
            return -1

        # Convert JSONB data to Document
        analysis_data = row[0]
        content = (
            json.dumps(analysis_data)
            if isinstance(analysis_data, dict)
            else str(analysis_data)
        )
        documents = [Document(page_content=content)]

        # Initialize vector store
        collection_name = f"video_id_{video_id}"

        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=os.getenv("POSTGRES_CONNECTION"),
        )

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        all_splits = text_splitter.split_documents(documents)

        # Index chunks
        vector_store.add_documents(documents=all_splits)

        cursor.close()

        return 1

    except Exception as e:
        print(f"Error creating embedding: {str(e)}")
        return -1
