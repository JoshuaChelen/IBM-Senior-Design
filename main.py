from program_files import chat_cli, debug
from pathlib import Path

# Use to toggle on and off DEBUG_MODE 
DEBUG_MODE = False 

def main():
    if DEBUG_MODE: 
        debug.debug()

    else: 
        # If debug mode is not on, we call the chat_cli.py file
        # print("Debug mode off")
        chat_cli.chat_cli()

if __name__ == '__main__':
    main()