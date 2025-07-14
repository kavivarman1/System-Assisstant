import google.generativeai as genai
import json
import os
import operation_executor_window  # Updated to use the enhanced version

# ✅ Configure Gemini API
genai.configure(api_key="AIzaSyDeABwz4vTnFLH3ZRN6cl1jw_X-6Sm2180")  # Replace with your actual key

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


def handle_input(user_input):
    global operations_list, file_context

    full_history.append(f"User: {user_input}")
    response = chat.send_message(user_input)
    bot_reply = response.text.strip()
    full_history.append(f"Gemini: {bot_reply}")

    print(f"\n🤖 Gemini says:\n{bot_reply}")

    # ✅ Try extracting JSON array (preferred format)
    try:
        json_start = bot_reply.find("[")
        json_end = bot_reply.rfind("]") + 1
        if json_start != -1 and json_end != -1:
            json_text = bot_reply[json_start:json_end]
            data = json.loads(json_text)

            if isinstance(data, list) and all("operation" in d and "filename" in d for d in data):
                print("\n✅ Extracted Operations (in order):")
                for item in data:
                    print(json.dumps(item, indent=2))

                operations_list.extend(data)

                for item in data:
                    process_operation(item)

                print("\n📂 Full Operations List:")
                for item in operations_list:
                    print(item)
                return
    except json.JSONDecodeError:
        pass

    # ✅ Fallback to single operation dictionary
    try:
        json_start = bot_reply.find("{")
        json_end = bot_reply.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            json_text = bot_reply[json_start:json_end]
            data = json.loads(json_text)

            if isinstance(data, dict) and "operation" in data and "filename" in data:
                print("\n✅ Extracted Single Operation:")
                print(json.dumps(data, indent=2))

                operations_list.append(data)
                process_operation(data)

                print("\n📂 Full Operations List:")
                for item in operations_list:
                    print(item)
                return
    except json.JSONDecodeError:
        pass

    print("\n❌ No valid operation extracted.")


def process_operation(operation_data):
    """Process a single operation and communicate results with Gemini"""
    operation = operation_data["operation"]
    filename = operation_data["filename"]
    timing = operation_data.get("timing")

    # Update with context if available
    if "/" not in filename and filename in file_context:
        filename = file_context[filename]
        operation_data["filename"] = filename

    try:
        result = operation_executor_window.execute_operation_with_timing(operation, filename, timing)
        system_message = ""

        if isinstance(result, dict):
            status = result.get("status")
            msg = result.get("message", "")

            if status == "ambiguous" and result.get("matches"):
                matches = result["matches"]
                for match_path in matches:
                    base_name = os.path.basename(match_path)
                    file_context[base_name] = match_path

                match_list = [
                    {"index": idx + 1, "path": match, "name": os.path.basename(match)}
                    for idx, match in enumerate(matches)
                ]

                system_message = {
                    "status": "multiple_matches",
                    "operation": operation,
                    "query": filename,
                    "timing": timing,
                    "matches": match_list,
                    "message": f"Found {len(matches)} possible matches for '{filename}'"
                }

                print(f"\n🔍 Multiple matches for '{filename}'" + (f" with timing '{timing}'" if timing else "") + ":")
                for idx, match in enumerate(matches, 1):
                    print(f"{idx}. {match}")

            elif status == "not_found":
                system_message = {
                    "status": "not_found",
                    "operation": operation,
                    "query": filename,
                    "timing": timing,
                    "message": msg
                }
                print(f"\n❌ {msg}")

            elif status == "success":
                system_message = {
                    "status": "success",
                    "operation": operation,
                    "query": filename,
                    "timing": timing,
                    "message": msg
                }
                print(f"\n✅ {msg}")

                if result.get("path"):
                    path = result["path"]
                    base_name = os.path.basename(path)
                    file_context[base_name] = path
                    system_message["path"] = path
                    system_message["filename"] = base_name

            else:
                system_message = {
                    "status": status,
                    "operation": operation,
                    "query": filename,
                    "timing": timing,
                    "message": msg
                }
                print(f"\n{msg}")

        else:
            system_message = {
                "status": "success" if "✅" in result else "error",
                "operation": operation,
                "query": filename,
                "timing": timing,
                "message": result
            }
            print(f"\n{result}")

            if "✅" in result and ":" in result:
                try:
                    path_part = result.split(":", 1)[1].strip().strip("'")
                    if os.path.exists(path_part):
                        base_name = os.path.basename(path_part)
                        file_context[base_name] = path_part
                        system_message["path"] = path_part
                        system_message["filename"] = base_name
                except:
                    pass

        full_history.append(f"System: {json.dumps(system_message)}")
        chat.send_message(f"SYSTEM_RESULT: {json.dumps(system_message)}")

    except Exception as e:
        error_msg = f"Error executing {operation} on {filename}"
        if timing:
            error_msg += f" with timing '{timing}'"
        error_msg += f": {str(e)}"

        system_message = {
            "status": "error",
            "operation": operation,
            "query": filename,
            "timing": timing,
            "message": error_msg
        }

        full_history.append(f"System: {json.dumps(system_message)}")
        chat.send_message(f"SYSTEM_RESULT: {json.dumps(system_message)}")


# ✅ MAIN LOOP
if __name__ == "__main__":
    print("💬 Gemini Chat Assistant Ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\n📝 Full chat history before exit:")
            for line in full_history:
                print(line)
            print("\nGoodbye! 👋")
            break
        handle_input(user_input)
