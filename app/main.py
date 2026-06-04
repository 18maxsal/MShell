import sys
import os
import subprocess
from pathlib import Path

BUILT_INS = ["echo", "exit", "type", "pwd", "cd", "history"]
history = []

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
        # print(f"full_path: {full_path}")
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

def changeDirectoryHelper(command: list[str]) -> None:

    # Handles going to the home directory 
    if command[1] == "~":
        path = Path.home()
        os.chdir(path)
        return
    
    # Handles absolute and relative paths (i.e. /. and /..)
    path = os.path.realpath(command[1])
    if os.path.exists(path):
        os.chdir(path)
    
    # Handles invalid input
    else:
        print(f"cd: {path}: No such file or directory")

    
def historyHelper(command: list[str]) -> None:
    
    if not command[1]:
        for i in range(len(history)):
            print(f"{i + 1} {history[i]}")
    
    else: 
        #TODO: Fix this block of code
        from_history = int(command[1])
        for i in range(len(history) - from_history, len(history)):
            # print(f"   {from_history} {history[i]}")
            print(f"   {i} {history[i]}")
            # from_history += 1
        # n = len(history)
        # i = n - 1
        # iterations = int(command[1])
        # while iterations:
        #     print(f"    {i} {history[i - 1]}")
        #     iterations -= 1
        #     i -= 1
        #     n -= 1


def main():
    while True:
        sys.stdout.write("$ ") # Used instead of print because this way does not include a newline
        command = input()
        to_add_history_command = command
        command = command.split(" ")
        if command[0] == "exit":
            break
        elif command[0] == "echo":
            echoHelper(command = command)
            history.append(to_add_history_command)
            
        elif command[0] == "type":
            typeHeler(command = command)
            history.append(to_add_history_command)
        
        elif command[0] == "pwd":
            pwdHelper()
            history.append(to_add_history_command)
        
        elif command[0] == "cd":
            changeDirectoryHelper(command = command)
            history.append(to_add_history_command)
        
        elif command[0] == "history":
            history.append(to_add_history_command)
            historyHelper(command = command)
        
        else:
            # command.insert(0, "type") # TEMP
            # typeHeler(command = command) # TEMP
            if not externalCommandRunnerHelper(command = command):
                print(f"{command[0]}: command not found")
            else:
                history.append(to_add_history_command)

if __name__ == "__main__":
    main()
