import subprocess
import os
import shlex

def get_env(local_port:int, chat_model:str=None, chat_host:str=None, chat_port:str=None):
    new_env = os.environ.copy()
    new_env["LOCAL_PORT"] = str(local_port)
    if chat_model is not None:
        new_env["CHAT_MODEL"]=chat_model 
    if chat_host is not None:
        new_env["CHAT_HOST"]=chat_host
    if chat_port is not None: 
        new_env["CHAT_PORT"]=str(chat_port)
    return new_env

def run_command(command:str, new_env:dict):
    args=shlex.split(command)
    try:
        subprocess.run(args, env=new_env, check=True) 
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

def start_chat():
    """
    Start the text chat server on port 8010
    """
    my_env = get_env(local_port=8010, chat_model="nlip-test-model")
    command = f"poetry run python nlip_web/text_chat.py"
    run_command(command, my_env)

def start_image():
    """
    Start the image chat server on port 8020
    """
    my_env = get_env(local_port=8020, chat_model="nlip-test-model")
    command = f"poetry run python nlip_web/image_chat.py"
    run_command(command, my_env)