import google.generativeai as genai
import json
import os
import operation_executor_window  # Updated to use the enhanced version
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# ✅ Configure Gemini API
genai.configure(api_key="AIzaSyDLHRVTQwFqUyazT187GPQHaME7VVZu71o")  # Replace with your actual key

# ✅ Load Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# ✅ Enhanced System prompt with multi-operation and timing extraction
intro_prompt = """
You are an AI assistant that:
1. Chats like a smart assistant.
2. Detects file operations (like open, delete, move, copy, paste) and filenames (like report.pdf, notes.txt).
3. Extracts timing information from user requests for file filtering.

Instructions:
- Your goal is to extract one or more valid file operations, associated filenames, and optional timing information.
- File **operation** and **filename** are required.
- Additionally, extract **timing fields** if present:
  - `time_type`: one of "modified", "created", or "accessed"
  - `date`, `month`, `year`, `range`: if explicitly mentioned
  - `timestamp`: natural phrase like "yesterday", "last month", "8 January 2025", etc.
  
Each operation must be output as a JSON object inside an array, including all available fields. Here's the format:
[
  {
    "operation": "search",
    "filename": "report.pdf",
    "timestamp": "last month",
    "time_type": "modified",
    "date": "8",
    "month": "January",
    "year": "2025"
  }
]

If `date`, `month`, or `year` are not available, omit them. If `time_type` is missing, infer from the phrasing (e.g., "created", "modified"). `timestamp` must always be present if any time-related detail is found.

TIMING EXTRACTION:
Extract timing information from phrases like:
- "files from today", "documents created yesterday"
- "files modified last week", "files from last month"
- "files on 8 January 2025", "files from June 2024 to July 2024"
- "all files on 8th 2024", "files created this morning"
- "recent files", "old files", "new files"

TIMING FORMATS TO RECOGNIZE:
- "today", "yesterday", "last week", "last month"
- "from [month] [year] to [month] [year]"
- "[day] [month] [year]" (e.g., "8 January 2025")
- "all files on [day][suffix] [year]" (e.g., "8th 2024")
- "this morning", "this afternoon", "this evening"
- "recent", "old", "new" (relative terms)

If the user says "open a file", but doesn't give a filename, ask naturally for the filename.
If optional info like file extension or folder is missing, ask nicely. But if the user says "I don't know", just move on.
Use full contextual paths when appropriate. For example, if a file is copied to or pasted into a folder, use "folder/file.txt" as the filename in subsequent operations like "open", "move", etc.
Pay close attention to details users provide about file locations, such as "open 500 days of summer located in movies folder" - include this context in your operations.
Remember file paths from previous operations to provide better context for new operations.

You may receive a single sentence with multiple file operations. Extract **each operation separately in the order they appear**. For example:
Input: "Search for report.pdf and open summary.txt from yesterday"
Output:
[
  {"operation": "search", "filename": "report.pdf"},
  {"operation": "open", "filename": "summary.txt", "timing": "yesterday"}
]

Your response must always be a single valid JSON array (no explanation or text), in the correct order of execution.

SYSTEM RESPONSES:
You will receive system responses after executing operations with the format:
SYSTEM_RESULT: {"status": "...", "operation": "...", "query": "...", "timing": "...", ...}

Different status types:
1. "success" - Operation was successful
2. "not_found" - File was not found
3. "multiple_matches" - Multiple files found matching the query
4. "error" - An error occurred

For multiple matches, you'll receive a "matches" field with paths. Reply to the user about these matches, 
letting them specify which one they meant. For example:
"I found several files matching 'report.pdf' from today. Which one did you want to open?
1. /path/to/report.pdf
2. /path/to/other/report.pdf"

For success, tell the user the operation was completed successfully.
For not_found, tell the user you couldn't find the file and ask for more details.
For error, tell the user there was a problem and explain what happened.

IMPORTANT: Never show the raw JSON to the user. Always respond conversationally based on the system response.
"""

# ✅ Start chat
chat = model.start_chat(history=[])
chat.send_message(intro_prompt)

# ✅ Track history
full_history = []
operations_list = []
file_context = {}  # Store file paths for context

# --- Refactor handle_input to return a string response ---
def handle_input(user_input):
    global operations_list, file_context

    full_history.append(f"User: {user_input}")
    response = chat.send_message(user_input)
    bot_reply = response.text.strip()
    full_history.append(f"Gemini: {bot_reply}")

    # Try extracting JSON array (preferred format)
    try:
        json_start = bot_reply.find("[")
        json_end = bot_reply.rfind("]") + 1
        if json_start != -1 and json_end != -1:
            json_text = bot_reply[json_start:json_end]
            data = json.loads(json_text)

            if isinstance(data, list) and all("operation" in d and "filename" in d for d in data):
                operations_list.extend(data)
                responses = []
                for item in data:
                    op_result = process_operation(item)
                    # Send SYSTEM_RESULT to Gemini and get user-facing reply
                    system_message = f"SYSTEM_RESULT: {json.dumps(op_result)}"
                    gemini_response = chat.send_message(system_message)
                    responses.append(gemini_response.text.strip())
                return "\n".join(responses)
    except json.JSONDecodeError:
        pass

    # Fallback to single operation dictionary
    try:
        json_start = bot_reply.find("{")
        json_end = bot_reply.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            json_text = bot_reply[json_start:json_end]
            data = json.loads(json_text)

            if isinstance(data, dict) and "operation" in data and "filename" in data:
                operations_list.append(data)
                op_result = process_operation(data)
                system_message = f"SYSTEM_RESULT: {json.dumps(op_result)}"
                gemini_response = chat.send_message(system_message)
                return gemini_response.text.strip()
    except json.JSONDecodeError:
        pass

    # If no valid operation extracted, let Gemini generate the user-facing message
    system_result = {
        "status": "invalid_request",
        "message": "Could not extract a valid operation or filename from the user input.",
        "user_input": user_input
    }
    system_message = f"SYSTEM_RESULT: {json.dumps(system_result)}"
    gemini_response = chat.send_message(system_message)
    return gemini_response.text.strip()

# --- Refactor process_operation to return only structured data ---
def process_operation(operation_data):
    operation = operation_data["operation"]
    filename = operation_data["filename"]
    timing = operation_data.get("timing")

    # Update with context if available
    if "/" not in filename and filename in file_context:
        filename = file_context[filename]
        operation_data["filename"] = filename

    try:
        result = operation_executor_window.execute_operation_with_timing(operation, filename, timing)
        status = result.get("status") if isinstance(result, dict) else None
        msg = result.get("message", "") if isinstance(result, dict) else str(result)
        if status == "ambiguous" and result.get("matches"):
            matches = result["matches"]
            for match_path in matches:
                base_name = os.path.basename(match_path)
                file_context[base_name] = match_path
            return {
                "status": "ambiguous",
                "operation": operation,
                "query": filename,
                "timing": timing,
                "matches": matches,
                "message": msg
            }
        elif status == "not_found":
            return {
                "status": "not_found",
                "operation": operation,
                "query": filename,
                "timing": timing,
                "message": msg
            }
        elif status == "success":
            if result.get("path"):
                path = result["path"]
                base_name = os.path.basename(path)
                file_context[base_name] = path
            return {
                "status": "success",
                "operation": operation,
                "query": filename,
                "timing": timing,
                "message": msg,
                "path": result.get("path")
            }
        else:
            return {
                "status": status or "unknown",
                "operation": operation,
                "query": filename,
                "timing": timing,
                "message": msg
            }
    except Exception as e:
        error_msg = f"Error executing {operation} on {filename}"
        if timing:
            error_msg += f" with timing '{timing}'"
        error_msg += f": {str(e)}"
        return {
            "status": "error",
            "operation": operation,
            "query": filename,
            "timing": timing,
            "message": error_msg
        }

# --- FastAPI server ---
app = FastAPI()

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    if not user_message:
        return JSONResponse({"response": "No message provided."}, status_code=400)
    response = handle_input(user_message)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run("smart_chatbot:app", host="127.0.0.1", port=5005, reload=False)

