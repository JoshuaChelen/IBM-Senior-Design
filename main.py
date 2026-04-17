from program_files.debug import debug
from program_files import chat_cli
from pathlib import Path

# Use to toggle on and off DEBUG_MODE 
DEBUG_MODE = False

def main():
    if DEBUG_MODE == True: 
        debug()

    else: 
        # If debug mode is not on, we call the chat_cli.py file
        print("Debug mode off")
        chat_cli.conversation()

if __name__ == '__main__':
    main()