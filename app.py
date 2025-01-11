import json
import re


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


# Example usage:
if __name__ == "__main__":
    input_text = """
    Based on the retrieved data regarding fire incidents, here is the structured JSON format of findings:
    
    ```json
    {
      "fire_incidents": [
        {
          "severity": "high",
          "description": "Large fire consuming a building",
          "time_interval": {
            "start_time": "30 seconds",
            "end_time": "60 seconds"
          }
        },
        {
          "severity": "medium",
          "description": "Fire with flames and smoke visible, structure outlines obscured",
          "time_interval": {
            "start_time": "60 seconds",
            "end_time": "90 seconds"
          }
        },
        {
          "severity": "low",
          "description": "Individual using a tool in a dimly lit environment, possibly related to fire response",
          "time_interval": {
            "start_time": "90 seconds",
            "end_time": "end of video"
          }
        }
      ]
    }
    ```
    
    ### Summary of Findings:
    - The first incident is categorized as high severity, indicating a significant fire affecting a building.
    - The second incident shows visible flames and smoke, with medium severity due to the ongoing danger.
    - The third incident is of low severity, depicting post-fire activity involving fire response efforts.
    """

    try:
        extracted_json = extract_json(input_text)
        # Ensure extracted_json is a dictionary and has the key 'fire_incidents'
        if isinstance(extracted_json, dict) and "fire_incidents" in extracted_json:
            # Append the new entry to the 'fire_incidents' list
            extracted_json["fire_incidents"].append({"severity": "none"})
        print(json.dumps(extracted_json, indent=2))
    except ValueError as ve:
        print(f"Error: {ve}")
