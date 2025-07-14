import os
import shutil
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_all_drives():
    """Detect all accessible drives (Windows) or root (Linux/macOS)."""
    drives = []
    if platform.system() == "Windows":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    else:
        drives = ['/']  # Linux/macOS root
    return drives

EXCLUDED_DIRS = [
    'Windows', 'Program Files', 'Program Files (x86)', '$Recycle.Bin',
    'System Volume Information', 'AppData', 'Microsoft', 'MSOCache', 'Recovery'
]

def search_in_drive(drive, name, search_type):
    """Search files/folders in a single drive."""
    matches = []
    for root, dirs, files in os.walk(drive, topdown=True):
        # Skip unwanted system folders for speed & permission safety
        dirs[:] = [d for d in dirs if not any(ex in d for ex in EXCLUDED_DIRS) and not d.startswith('$') and not d.startswith('.')]
        try:
            if search_type in ('folder', 'both'):
                for d in dirs:
                    if name.lower() in d.lower():
                        matches.append(os.path.join(root, d))
            if search_type in ('file', 'both'):
                for f in files:
                    if name.lower() in f.lower():
                        matches.append(os.path.join(root, f))
        except (PermissionError, FileNotFoundError):
            continue
    return matches

def search_files_and_folders(name, search_type='both'):
    """Search for files/folders by name across all drives (multi-threaded)."""
    matches = []
    drives = get_all_drives()

    with ThreadPoolExecutor(max_workers=min(8, len(drives))) as executor:
        futures = [executor.submit(search_in_drive, drive, name, search_type) for drive in drives]
        for future in as_completed(futures):
            try:
                matches.extend(future.result())
            except Exception as e:
                print(f"Error searching drive: {e}")
    return matches

def open_path(path):
    """Open file or folder using system's default program."""
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
    """Copy file or folder to destination."""
    try:
        if os.path.isdir(source):
            shutil.copytree(source, os.path.join(destination, os.path.basename(source)))
        else:
            shutil.copy2(source, destination)
        print(f"Copied to: {destination}")
    except Exception as e:
        print(f"Error copying item: {e}")

def main():
    print("🔧 Welcome to the System Assistant (Open / Search / Copy)\n")

    while True:
        print("\nChoose an operation: open / search / copy (or type 'exit' to quit)")
        operation = input("Operation: ").strip().lower()

        if operation == 'exit':
            print("Goodbye!")
            break

        if operation not in ['open', 'search', 'copy']:
            print("❌ Invalid operation. Please choose from open, search, copy.")
            continue

        name = input("Enter file or folder name (partial or full): ").strip()
        if not name:
            print("❌ Name cannot be empty.")
            continue

        search_type = 'both'
        matches = search_files_and_folders(name, search_type)

        if not matches:
            print("🔍 No matches found.")
            continue

        elif len(matches) == 1:
            match = matches[0]
            print(f"✅ One match found: {match}")

            if operation == 'open':
                open_path(match)

            elif operation == 'search':
                print(f"Found: {match}")

            elif operation == 'copy':
                destination = input("Enter destination folder path: ").strip()
                if os.path.isdir(destination):
                    copy_item(match, destination)
                else:
                    print("❌ Invalid destination folder.")

        else:
            print(f"🔍 Multiple matches found ({len(matches)}):")
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
                                print("❌ Invalid destination folder.")
                    else:
                        print("❌ Invalid choice.")
                except ValueError:
                    print("❌ Invalid input. Enter a number.")
            elif operation == 'search':
                pass

if __name__ == "__main__":
    main()
