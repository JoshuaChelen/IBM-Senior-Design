from program_files.debug import debug
from pathlib import Path

# Use to toggle on and off DEBUG_MODE 
DEBUG_MODE = True 

def main():
    if DEBUG_MODE == True: 
        debug()

    else: 
        # If debug mode is not on, we call the chat_cli.py file
        print("Debug mode off")

if __name__ == '__main__':
    main()