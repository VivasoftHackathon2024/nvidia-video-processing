import json
import os
import re

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, create_react_agent
from pydantic import BaseModel

load_dotenv()


api_key = os.environ.get("OPENAI_API_KEY")

# Global variables
collection_name = None
drug_vector_store = None


def extract_json(input_string):
    """
    Extracts the first JSON code block from the input string and returns it as a Python dictionary.

    Args:
        input_string (str): The input string containing a JSON code block.

    Returns:
        dict: The parsed JSON object.

    Raises:
        ValueError: If no JSON code block is found or if the JSON is invalid.
    """
    # Regular expression to match a JSON code block
    # It looks for ```json (case-insensitive), captures everything until the next ```
    pattern = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)

    match = pattern.search(input_string)

    if not match:
        raise ValueError("No JSON code block found in the input string.")

    json_str = match.group(1)

    try:
        # Parse the JSON string into a Python dictionary
        json_data = json.loads(json_str)
        return json_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


system_message_drug_agent = """
You are an intelligent assistant specialized in detecting and analyzing drug-related incidents within video content. Your tasks are as follows:

1. **Retrieve Relevant Information**: Use the 'retrieve' tool to access all pertinent data from the vector store related to the input query.

2. **Detect Drug-Related Mentions**: Analyze the retrieved content to identify any mentions or indications of drug-related activities, such as possession, use, distribution, or manufacturing of controlled substances.

3. **Assess Severity**:
    - Determine the severity of each detected drug-related incident based on factors such as the type and quantity of substances involved, the nature of the activity (e.g., personal use vs. distribution), and potential legal classifications.
    - Categorize the severity into one of the following levels:
        - **none**: No drug-related activity detected.
        - **low**: Minor offenses, such as possession of small quantities for personal use, with minimal legal consequences. 
        - **medium**: Significant offenses, such as possession of larger quantities or involvement in distribution, leading to moderate legal consequences. 
        - **high**: Severe offenses, such as large-scale trafficking or manufacturing of controlled substances, associated with substantial legal penalties. 

4. **Extract Time Intervals**: For each detected drug-related incident, extract the corresponding `start_time_seconds` and `end_time_seconds`.

5. **Structured Output**: Present the results in a clear, structured JSON format containing:
    - **severity**: The overall severity level of the detected drug-related incidents.
    - **drug_events**: A list of objects, each with `start_time_seconds` and `end_time_seconds` indicating when the drug-related activity was detected.

**Important Guidelines**:
- Always begin by using the 'retrieve' tool to obtain the relevant vectorized data.
- Focus exclusively on content related to drug-related incidents; disregard unrelated information.
- Ensure that the output strictly adheres to the specified JSON structure without additional explanations or narrative.
- If no drug-related activity is detected, set the severity to "none" and provide an empty list for `drug_events`.

**Example Output**:
```json
{
    "severity": "none",
    "drug_events": []
}
```
```json
{
    "severity": "low",
    "drug_events": [
        {
            "start_time_seconds": 120,
            "end_time_seconds": 150
        }
    ]
}
```
```json
{
    "severity": "medium",
    "drug_events": [
        {
            "start_time_seconds": 120,
            "end_time_seconds": 150
        },
        {
            "start_time_seconds": 300,
            "end_time_seconds": 330
        }
    ]
}
```
```json
{
    "severity": "high",
    "drug_events": [
        {
            "start_time_seconds": 120,
            "end_time_seconds": 150
        },
        {
            "start_time_seconds": 300,
            "end_time_seconds": 330
        }
    ]
}
```
"""


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_message_drug_agent),
        ("human", "{input}"),
    ]
)


embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
llm = ChatOpenAI(model="gpt-4o-mini")


def evaluate_severity(input_string: str) -> str:
    """
    Determines the severity of a fire situation using LangChain's ChatOpenAI.

    Args:
        system_prompt (str): The system prompt to set the context for the AI model.
        input_string (str): The input string containing information about the fire situation.

    Returns:
        str: A single word indicating the severity: 'neutral', 'low', 'medium', or 'high'.

    Raises:
        ValueError: If the AI model returns an unexpected severity level.
    """

    evaluator_prompt = "You are an assistant that analyzes drug incident reports and determines their severity."

    # Initialize the ChatOpenAI model with desired parameters
    chat = ChatOpenAI(
        model_name="gpt-4o-mini",  # You can choose other models like "gpt-3.5-turbo" if preferred
        temperature=0,  # Setting temperature to 0 for deterministic output
        openai_api_key=api_key,
    )

    # Define the messages to send to the model
    messages = [
        SystemMessage(content=evaluator_prompt),
        HumanMessage(
            content=f"{input_string}\n\nPlease provide the severity of the drug situation as a single word: neutral, low, medium, or high."
        ),
    ]

    # Get the response from the model
    response = chat(messages)

    # Extract and clean the content from the response
    severity = response.content.strip().lower()

    # Define the valid severity levels
    valid_severities = {"neutral", "low", "medium", "high"}

    # Validate the response
    if severity in valid_severities:
        return severity
    else:
        # Handle unexpected responses gracefully
        raise ValueError(
            f"Unexpected severity level returned: '{severity}'. Expected one of {valid_severities}."
        )


@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    global drug_vector_store
    retrieved_docs = drug_vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


# memory = MemorySaver()

# agent_executor = create_react_agent(llm, [retrieve], checkpointer=memory)


def run_drug_agent(video_id: int):
    """
    Runs the crime detection agent with a predefined prompt, collects the final
    structured JSON output, and returns it.
    """
    global collection_name, drug_vector_store
    collection_name = f"video_id_{video_id}"

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    drug_vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=os.environ.get("POSTGRES_CONNECTION"),
    )

    llm = ChatOpenAI(model="gpt-4o-mini")
    memory = MemorySaver()
    agent_executor = create_react_agent(llm, [retrieve], checkpointer=memory)

    input_message = "Please analyze the following vectorized data retrieved from the pgvector database to detect any mentions of drug or drugs. Your analysis should focus exclusively on identifying drug-related incidents, assessing their severity, and extracting the corresponding time intervals. Present your findings in the structured JSON format as specified in the system prompt."

    final_output = ""
    for event in agent_executor.stream(
        {"messages": [{"role": "user", "content": input_message}]},
        stream_mode="values",
        config={"configurable": {"thread_id": "def234"}},
    ):
        messages = event.get("messages", [])
        if messages:
            final_output = messages[-1].content

    try:
        extracted_json = extract_json(final_output)
        if isinstance(extracted_json, dict) and "drug_incidents" in extracted_json:
            severity = evaluate_severity(final_output)
            extracted_json["drug_incidents"].append({"severity": severity})
        final_output = json.dumps(extracted_json, indent=2)
        return final_output
    except ValueError as ve:
        print(f"Error: {ve}")
