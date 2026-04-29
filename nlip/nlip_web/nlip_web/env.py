'''
This file contains some handy utilities for reading environment variables
In python, all environment variables are passed as strings. 
However, this causes an issue when we want to read an integer or floating point
This provides checks for reading those types of environment variable. 

'''
import os
import re

'''
The basic string variable reading. This may be superflous but
keeps the same calling convention for functions. 

'''

def read_string(var_name:str, def_value:str) -> str:
    return os.environ.get(var_name, def_value).strip()

'''
A routine to read digits only from environment variable. 
This will read the digital value such as port or positive unsigned int. 

'''

def read_digits(var_name:str, def_value:int) -> int:
    env_value = os.environ.get(var_name,None)
    if env_value is None:
        return def_value
    if env_value.strip().isdigit():
        return int(env_value.strip())
    return def_value

'''
A routine to read signed/unsigned int from environment variable. 
This will read values with +, - or nothing in front, followed by digits.

'''

def read_int(var_name:str, def_value:int) -> int:
    env_value = os.environ.get(var_name,None)
    if env_value is None:
        return def_value
    env_value = env_value.strip()
    if env_value[0] == '+' or env_value[i]=='-':
        if env_value[1:].isdigit():
            return int(env_value)
    if env_value.isdigit():
        return int(env_value)
    return def_value

'''
A routine to read a floating number from environment variable. 

'''
def read_float(var_name:str, def_value:float) -> float:
    env_value = os.environ.get(var_name,None)
    if env_value is None:
        return def_value
    pattern = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
    env_value=env_value.strip()
    if bool(pattern.match(env_value)):
        return float(env_value)
    return def_value