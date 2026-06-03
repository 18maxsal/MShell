import sys
import os
import subprocess
from pathlib import Path

BUILT_INS = ["echo", "exit", "type"]

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
    # counter = 10
    # print(command) # format: external_command arg1 arg2 ...
    path = os.environ.get('PATH')
    path_list = path.split(os.pathsep)
    for i in range(len(path_list)):
        full_path = os.path.join(path_list[i], command[0])
        # print(f"full path: {full_path}, path_list[{i}]: {path_list[i]}")
        
        # full_path = os.path.join(path_list[i], command[1]) # TEMP
        # print(full_path)

        # print(path_list[i])
        # counter -= 1

        # if counter == 0:
        #     break
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            # print("aaaa")
            # break
            if full_path.endswith(command[0]):
                full_path = full_path.split("/")
                custom_command = [full_path[-1]]
                ptr = 1
                # print(f"custom_command before: {custom_command}")
                while ptr < len(command):
                    # print("ptr: ", ptr)
                    custom_command.append(command[i])
                    ptr += 1
                # process_to_run = full_path
                # subprocess.run([full_path, ])
                # print(f"custom_command AFTER: {custom_command}")
                # print(f"custom command to run: {custom_command}") # TEMP
                subprocess.run(custom_command)
                return True

    return False

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
        
        else:
            # command.insert(0, "type") # TEMP
            # typeHeler(command = command) # TEMP
            if not externalCommandRunnerHelper(command = command):
                print(f"{command[0]}: command not found")

if __name__ == "__main__":
    main()
