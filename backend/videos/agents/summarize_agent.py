import os

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, create_react_agent

load_dotenv()


api_key = os.environ.get("OPENAI_API_KEY")

# Global variables
collection_name = None
summary_vector_store = None

system_message = """
You are an intelligent assistant specialized in analyzing video content. Your task is to:
1. First use the 'retrieve' tool to get all relevant information from the vector store
2. Analyze the retrieved content thoroughly
3. Create a comprehensive summary of the video content
4. Focus on key events, actions, and important details
5. Present the information in a clear, structured format

Always start by using the retrieve tool to get the video content before creating your summary.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_message),
        ("human", "{input}"),
    ]
)


embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
llm = ChatOpenAI(model="gpt-4o-mini")


@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    global summary_vector_store
    # 'vector_store' is assumed to be globally accessible or imported.
    retrieved_docs = summary_vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


# memory = MemorySaver()

# agent_executor = create_react_agent(llm, [retrieve], checkpointer=memory)


def run_summarize_agent(video_id: int):
    """
    Runs the agent with a default prompt, collects the final
    message in a variable, and returns it.
    """
    global collection_name, summary_vector_store
    collection_name = f"video_id_{video_id}"

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    summary_vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=os.environ.get("POSTGRES_CONNECTION"),
    )

    llm = ChatOpenAI(model="gpt-4o-mini")
    memory = MemorySaver()
    agent_executor = create_react_agent(llm, [retrieve], checkpointer=memory)

    input_message = "Please analyze the following vectorized data retrieved from a pgvector database and provide a detailed summary focusing exclusively on content related to crime scenes, criminal activities, or any information linked to crimes. Disregard unrelated information in your summary."

    final_output = ""
    for event in agent_executor.stream(
        {"messages": [{"role": "user", "content": input_message}]},
        stream_mode="values",
        config={"configurable": {"thread_id": "def234"}},
    ):
        messages = event.get("messages", [])
        if messages:
            final_output = messages[-1].content

    return final_output
