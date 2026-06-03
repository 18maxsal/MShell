import sys
import os
import subprocess
from pathlib import Path

BUILT_INS = ["echo", "exit", "type", "pwd"]

def echoHelper(command: list[str]) -> None:
    to_print = ""
    if len(command) > 1:
        to_print = " ".join(command[1:])
    print(to_print)

def typeHeler(command: list[str]) -> None:
    if command[1] and command[1] in BUILT_INS:
        print(f"{command[1]} is a shell builtin")
    else: # Command is not Built-in
        if command[1]:
            path = os.environ.get('PATH')
            path_list = path.split(os.pathsep)
            for i in range(len(path_list)):
                full_path = os.path.join(path_list[i], command[1])
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    print(f"{command[1]} is {full_path}")
                    return
            print(f"{command[1]}: not found")

        else: # Case: there is no command[1] (i.e. we just have "type " for input)
            print("not found")

def externalCommandRunnerHelper(command: list[str]) -> bool:
    path = os.environ.get('PATH')
    path_list = path.split(os.pathsep)
    for i in range(len(path_list)):
        full_path = os.path.join(path_list[i], command[0])
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            if full_path.endswith(command[0]):
                full_path = full_path.split("/")
                custom_command = [full_path[-1]]
                ptr = 1
                while ptr < len(command):
                    custom_command.append(command[ptr])
                    ptr += 1
                subprocess.run(custom_command)
                return True

    return False

def pwdHelper() -> None:
    print(Path.cwd())

def main():
    while True:
        sys.stdout.write("$ ") # Used instead of print because this way does not include a newline
        command = input().split(" ")
        if command[0] == "exit":
            break
        elif command[0] == "echo":
            echoHelper(command = command)
            
        elif command[0] == "type":
            typeHeler(command = command)
        
        elif command[0] == "pwd":
            pwdHelper()
        
        else:
            # command.insert(0, "type") # TEMP
            # typeHeler(command = command) # TEMP
            if not externalCommandRunnerHelper(command = command):
                print(f"{command[0]}: command not found")

if __name__ == "__main__":
    main()
