import os
import shutil
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import win32com.client
from datetime import datetime, timedelta
import re

# ---------- TIME FILTER ADVANCED ----------
def parse_time_input(input_str):
    input_str = input_str.lower().strip()
    now = datetime.now()

    # Predefined periods
    if input_str == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0), now
    elif input_str == "yesterday":
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)
    elif input_str == "last week":
        return now - timedelta(days=7), now
    elif input_str == "last month":
        return now - timedelta(days=30), now
    elif input_str == "this morning":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=12, minute=0, second=0, microsecond=0)
        return start, end
    elif input_str == "this afternoon":
        start = now.replace(hour=12, minute=0, second=0, microsecond=0)
        end = now.replace(hour=18, minute=0, second=0, microsecond=0)
        return start, end
    elif input_str == "this evening":
        start = now.replace(hour=18, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end
    elif input_str == "recent":
        return now - timedelta(days=3), now
    elif input_str == "old":
        return datetime(2000, 1, 1), now - timedelta(days=30)
    elif input_str == "new":
        return now - timedelta(days=7), now

    # Custom range: from June 2024 to July 2024
    match_range = re.match(r'from (.+?) to (.+)', input_str)
    if match_range:
        try:
            start = datetime.strptime(match_range.group(1).strip(), "%B %Y")
            end = datetime.strptime(match_range.group(2).strip(), "%B %Y") + timedelta(days=31)
            return start, end
        except:
            pass

    # Specific date: files on 8 January 2025
    match_day = re.search(r'(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})', input_str)
    if match_day:
        try:
            start = datetime.strptime(match_day.group(0), "%d %B %Y")
            return start, start + timedelta(days=1)
        except:
            pass

    # Pattern like: all files on 8th 2024
    match_day_any_month = re.match(r'all files on (\d{1,2})(st|nd|rd|th)?\s+(\d{4})', input_str)
    if match_day_any_month:
        day = int(match_day_any_month.group(1))
        year = int(match_day_any_month.group(3))
        date_ranges = []
        for month in range(1, 13):
            try:
                start = datetime(year, month, day)
                end = start + timedelta(days=1)
                date_ranges.append((start, end))
            except:
                continue
        return date_ranges  # multiple ranges

    # Pattern: files created in [month] [year]
    match_month_year = re.match(r'files? (?:created|modified) in ([a-zA-Z]+)\s+(\d{4})', input_str)
    if match_month_year:
        try:
            month_name = match_month_year.group(1)
            year = int(match_month_year.group(2))
            month_num = datetime.strptime(month_name, "%B").month
            start = datetime(year, month_num, 1)
            if month_num == 12:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, month_num + 1, 1)
            return start, end
        except:
            pass

    # Pattern: files from [X] days ago
    match_days_ago = re.match(r'files? from (\d+)\s+days?\s+ago', input_str)
    if match_days_ago:
        try:
            days = int(match_days_ago.group(1))
            start = now - timedelta(days=days)
            return start, now
        except:
            pass

    # Pattern: files modified in the last [X] hours
    match_hours = re.match(r'files? (?:modified|created) in the last (\d+)\s+hours?', input_str)
    if match_hours:
        try:
            hours = int(match_hours.group(1))
            start = now - timedelta(hours=hours)
            return start, now
        except:
            pass

    return None, None

# ---------- GET ALL DRIVES ----------
def get_all_drives():
    drives = []
    if platform.system() == "Windows":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    else:
        drives = ['/']
    return drives

# ---------- WINDOWS SEARCH API ----------
def search_using_windows_index(name, search_type='both', time_start=None, time_end=None):
    matches = []
    connection = win32com.client.Dispatch("ADODB.Connection")
    recordset = win32com.client.Dispatch("ADODB.Recordset")
    connection.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")

    if name.startswith("."):
        restriction = f"System.FileExtension = '{name}'"
    elif search_type == 'file':
        restriction = f"System.FileName LIKE '%{name}%' AND System.ItemType != ''"
    elif search_type == 'folder':
        restriction = f"System.ItemNameDisplay LIKE '%{name}%' AND System.ItemType = ''"
    else:
        restriction = f"System.ItemNameDisplay LIKE '%{name}%'"

    if time_start and isinstance(time_start, datetime):
        iso_start = time_start.strftime("%Y-%m-%dT%H:%M:%S")
        restriction += f" AND System.DateModified >= '{iso_start}'"
    if time_end and isinstance(time_end, datetime):
        iso_end = time_end.strftime("%Y-%m-%dT%H:%M:%S")
        restriction += f" AND System.DateModified < '{iso_end}'"

    query = f"SELECT System.ItemPathDisplay FROM SYSTEMINDEX WHERE {restriction}"

    try:
        recordset.Open(query, connection)
        while not recordset.EOF:
            path = recordset.Fields.Item("System.ItemPathDisplay").Value
            if path:
                matches.append(path)
            recordset.MoveNext()
        recordset.Close()
        connection.Close()
    except Exception as e:
        print(f"\u26a0\ufe0f Windows Search failed. Error: {e}")
    return matches

# ---------- OS WALK SEARCH ----------
EXCLUDED_DIRS = ['Windows', 'Program Files', 'Program Files (x86)', '$Recycle.Bin',
                 'System Volume Information', 'AppData', 'Microsoft']

def search_in_drive(drive, name, search_type, time_start=None, time_end=None):
    matches = []
    for root, dirs, files in os.walk(drive, topdown=True):
        dirs[:] = [d for d in dirs if not any(ex in d for ex in EXCLUDED_DIRS) and not d.startswith('$') and not d.startswith('.')]
        try:
            if search_type in ('folder', 'both'):
                for d in dirs:
                    full_path = os.path.join(root, d)
                    if name.lower() in d.lower():
                        if time_start or time_end:
                            mod_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                            if (time_start and mod_time < time_start) or (time_end and mod_time >= time_end):
                                continue
                        matches.append(full_path)
            if search_type in ('file', 'both'):
                for f in files:
                    full_path = os.path.join(root, f)
                    if name.startswith("."):
                        if not f.lower().endswith(name.lower()):
                            continue
                    elif name.lower() not in f.lower():
                        continue
                    if time_start or time_end:
                        mod_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                        if (time_start and mod_time < time_start) or (time_end and mod_time >= time_end):
                            continue
                    matches.append(full_path)
        except (PermissionError, FileNotFoundError):
            continue
    return matches

def search_with_os_walk(name, search_type='both', time_start=None, time_end=None):
    matches = []
    drives = get_all_drives()
    with ThreadPoolExecutor(max_workers=min(8, len(drives))) as executor:
        futures = [executor.submit(search_in_drive, drive, name, search_type, time_start, time_end) for drive in drives]
        for future in as_completed(futures):
            try:
                matches.extend(future.result())
            except Exception as e:
                print(f"Error searching drive: {e}")
    return matches

# ---------- HYBRID SEARCH ----------
def search_files_and_folders(name, search_type='both', time_start=None, time_end=None, multiple_ranges=None):
    results = []
    if multiple_ranges:
        for start, end in multiple_ranges:
            part = search_files_and_folders(name, search_type, start, end)
            results.extend(part)
        return results

    if platform.system() == "Windows":
        results = search_using_windows_index(name, search_type, time_start, time_end)
        if results:
            return results
        print("\u26a0\ufe0f Falling back to manual search...")
    return search_with_os_walk(name, search_type, time_start, time_end)

# ---------- FILE OPERATIONS ----------
def open_path(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
        print(f"Opened: {path}")
    except Exception as e:
        print(f"Error opening path: {e}")

def copy_item(source, destination):
    try:
        if os.path.isdir(source):
            shutil.copytree(source, os.path.join(destination, os.path.basename(source)))
        else:
            shutil.copy2(source, destination)
        print(f"Copied to: {destination}")
    except Exception as e:
        print(f"Error copying item: {e}")

# ---------- ENHANCED OPERATION EXECUTOR WITH TIMING ----------
def execute_operation_with_timing(operation, filename, timing=None):
    """
    Execute file operations with timing support.
    
    Args:
        operation (str): The operation to perform (open, search, copy)
        filename (str): The filename or search term
        timing (str): Optional timing filter (e.g., "today", "yesterday", "from June 2024 to July 2024")
    
    Returns:
        dict: Result with status, message, and optional matches
    """
    try:
        # Parse timing if provided
        time_start = None
        time_end = None
        multiple_ranges = None
        
        if timing:
            result = parse_time_input(timing)
            if isinstance(result, tuple) and all(isinstance(i, datetime) for i in result):
                time_start, time_end = result
                multiple_ranges = None
            elif isinstance(result, list):
                time_start = time_end = None
                multiple_ranges = result
            else:
                # Invalid timing format
                return {
                    "status": "error",
                    "message": f"Invalid timing format: '{timing}'. Supported formats: today, yesterday, last week, last month, specific dates, or date ranges."
                }
        
        # Determine search type based on filename
        search_type = 'both'
        if filename.startswith('.'):
            search_type = 'file'
        elif '/' in filename or '\\' in filename:
            # If it looks like a path, search for exact match first
            if os.path.exists(filename):
                if operation == 'open':
                    open_path(filename)
                    return {
                        "status": "success",
                        "message": f"✅ Opened: {filename}",
                        "path": filename
                    }
                elif operation == 'search':
                    return {
                        "status": "success",
                        "message": f"✅ Found: {filename}",
                        "path": filename
                    }
        
        # Search for files/folders
        matches = search_files_and_folders(filename, search_type, time_start, time_end, multiple_ranges)
        
        if not matches:
            timing_info = f" with timing '{timing}'" if timing else ""
            return {
                "status": "not_found",
                "message": f"❌ No files found matching '{filename}'{timing_info}"
            }
        
        elif len(matches) == 1:
            match = matches[0]
            timing_info = f" with timing '{timing}'" if timing else ""
            
            if operation == 'open':
                open_path(match)
                return {
                    "status": "success",
                    "message": f"✅ Opened: {match}{timing_info}",
                    "path": match
                }
            
            elif operation == 'search':
                return {
                    "status": "success",
                    "message": f"✅ Found: {match}{timing_info}",
                    "path": match
                }
            
            elif operation == 'copy':
                # For copy operations, we need a destination
                # This is a simplified version - in practice, you might want to ask for destination
                return {
                    "status": "success",
                    "message": f"✅ Found file to copy: {match}{timing_info}",
                    "path": match
                }
        
        else:
            # Multiple matches
            timing_info = f" with timing '{timing}'" if timing else ""
            match_list = []
            for idx, match in enumerate(matches, 1):
                match_list.append({
                    "index": idx,
                    "path": match,
                    "name": os.path.basename(match)
                })
            
            return {
                "status": "ambiguous",
                "message": f"🔍 Found {len(matches)} files matching '{filename}'{timing_info}",
                "matches": matches,
                "match_details": match_list
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Error executing {operation} on {filename}: {str(e)}"
        }

# ---------- MAIN ----------
def main():
    print("\U0001f527 Welcome to the System Assistant (Open / Search / Copy)\n")
    while True:
        print("\nChoose an operation: open / search / copy (or type 'exit' to quit)")
        operation = input("Operation: ").strip().lower()

        if operation == 'exit':
            print("Goodbye!")
            break

        if operation not in ['open', 'search', 'copy']:
            print("\u274c Invalid operation. Please choose from open, search, copy.")
            continue

        name = input("Enter file or folder name (partial, full, or extension like .py): ").strip()
        if not name:
            print("\u274c Name cannot be empty.")
            continue

        time_input = input("Filter by time? (e.g., today / yesterday / last week / last month / 'files on 8 January 2025' / 'from June 2024 to July 2024' / 'all files on 8th 2024' / none): ").strip().lower()
        if time_input == 'none':
            time_start = time_end = multiple_ranges = None
        else:
            result = parse_time_input(time_input)
            if isinstance(result, tuple) and all(isinstance(i, datetime) for i in result):
                time_start, time_end = result
                multiple_ranges = None
            elif isinstance(result, list):
                time_start = time_end = None
                multiple_ranges = result
            else:
                print("\u274c Invalid time input.")
                continue

        search_type = 'both'
        matches = search_files_and_folders(name, search_type, time_start, time_end, multiple_ranges)

        if not matches:
            print("\U0001f50d No matches found.")
            continue
        elif len(matches) == 1:
            match = matches[0]
            print(f"\u2705 One match found: {match}")
            if operation == 'open':
                open_path(match)
            elif operation == 'search':
                print(f"Found: {match}")
            elif operation == 'copy':
                destination = input("Enter destination folder path: ").strip()
                if os.path.isdir(destination):
                    copy_item(match, destination)
                else:
                    print("\u274c Invalid destination folder.")
        else:
            print(f"\U0001f50d Multiple matches found ({len(matches)}):")
            for idx, match in enumerate(matches, 1):
                print(f"{idx}. {match}")
            if operation in ['open', 'copy']:
                try:
                    choice = int(input("Select the number of the path to proceed: "))
                    if 1 <= choice <= len(matches):
                        selected = matches[choice - 1]
                        if operation == 'open':
                            open_path(selected)
                        elif operation == 'copy':
                            destination = input("Enter destination folder path: ").strip()
                            if os.path.isdir(destination):
                                copy_item(selected, destination)
                            else:
                                print("\u274c Invalid destination folder.")
                    else:
                        print("\u274c Invalid choice.")
                except ValueError:
                    print("\u274c Invalid input. Enter a number.")

if __name__ == "__main__":
    main()