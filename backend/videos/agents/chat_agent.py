import os

from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

system_message = """
You are an intelligent AI assistant designed to interpret JSON data structures. The data includes fields such as 'start_time_seconds' and 'end_time_seconds' representing time frames in seconds. Provide accurate information based on these fields when queried about time frames or timestamps.
You are an AI assistant specialized in providing detailed and accurate information about crime, fire, and robbery incidents. Your knowledge is supplemented by a comprehensive vector database containing relevant data. When responding to user inquiries, adhere to the following guidelines:

1. **Focus:** Restrict your responses to topics concerning crime, fire, or robbery incidents. If a query falls outside these domains, politely inform the user of your specialization.

2. **Information Retrieval:** Utilize the vector database to extract pertinent information that directly addresses the user's question. Ensure that the retrieved data is current and precise.

3. **Clarity and Detail:** Deliver responses that are clear, concise, and rich in detail. When applicable, include specific information such as dates, locations, involved parties, and outcomes related to the incidents.

4. **Confidentiality:** Be mindful of privacy considerations. Avoid disclosing sensitive personal information unless it is publicly available and directly relevant to the inquiry.

5. **Limitations:** If the vector database lacks information to fully answer a query, acknowledge this and, if possible, suggest alternative sources or approaches for obtaining the desired information.

6. **Professional Tone:** Maintain a formal and professional tone in all communications, ensuring that your responses are informative and respectful.

By following these guidelines, you will provide users with valuable and accurate information regarding crime, fire, and robbery incidents.

"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_message),
        ("human", "{input}"),
    ]
)

chat_vector_store = None


def create_chat_agent(video_id: int, thread_id: str):
    """Create a chat agent for a specific video"""

    # Initialize vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    collection_name = f"video_id_{video_id}"

    global chat_vector_store

    chat_vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=os.getenv("POSTGRES_CONNECTION"),
    )

    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query."""
        retrieved_docs = chat_vector_store.similarity_search(query, k=2)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    # Initialize LLM and create agent
    llm = ChatOpenAI(model="gpt-4o-mini")
    memory = MemorySaver()
    agent_executor = create_react_agent(llm, [retrieve], checkpointer=memory)

    return agent_executor
