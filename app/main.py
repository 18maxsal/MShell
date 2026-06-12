import sys
import os
import subprocess
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

# Ensuring program works regardless of OS that user is running
# if sys.platform != "win32":
#     import readline
# else:
#     from prompt_toolkit import PromptSession
#     from prompt_toolkit.history import FileHistory

# print(sys.platform)
# try: 
#     import readline
# except ImportError:
#     import pyreadline3 as readline

BUILT_INS = ["echo", "exit", "type", "pwd", "cd", "history"]
# PROJECT_ROOT = Path(__file__).resolve().parent.parent
# history_file =  os.path.expanduser("~/.mshell_history")
# history_file = str(PROJECT_ROOT) + "/.mshell_history" 
# history_file = str(PROJECT_ROOT) + "/.mshell_history"
HISTORY_FILE = ".mshell_history"
current_history_file = HISTORY_FILE
session = PromptSession(history=FileHistory(current_history_file))

# try:
#     readline.read_history_file(HISTORY_FILE)
# except FileNotFoundError:
#     pass

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


def getHistoryEntries() -> list[str]:
    return list(session.history.get_strings())

    
def historyHelper(command: list[str]) -> None:


    if len(command) == 1:
        entries = getHistoryEntries()
        print("Entries: ", entries)
        for i in range(len(entries)):
            print(f"    {i + 1} {entries[i]}")
    
    else: 

        if command[1] == "-r":
            global session
            global current_history_file
            path_to_history_file = os.path.expanduser(command[2])
            history_parent = os.path.dirname(path_to_history_file)
            if history_parent:
                os.makedirs(history_parent, exist_ok = True)
            current_history_file = path_to_history_file
            session = PromptSession(history=FileHistory(current_history_file))


            # global session 
            # path_to_history_file = command[2]
            # session = PromptSession(history=FileHistory(path_to_history_file))


        else:
            try: 
                from_history = int(command[1])
            except ValueError as VE:
                return
            entries = getHistoryEntries()
            start = max(len(entries) - from_history, 0)
            for i in range(start, len(entries)):
                print(f"   {i + 1} {entries[i]}")



            # from_history = int(command[1])
            # for i in range(len(history) - from_history, len(history)):
            #     print(f"   {i} {history[i]}")

def main():
    while True:
        # sys.stdout.flush()
        # sys.stdout.write("$ ") # Used instead of print because this way does not include a newline
        # command = input("$ ")
        command = session.prompt("$ ")
        command = command.split(" ")
        # print(len(command))
        # print(command)
        
        if len(command) == 1 and command[0] == '':
            continue

        if command[0] == "exit":
            break
        elif command[0] == "echo":
            echoHelper(command = command)
            # history.append(to_add_history_command)
            
        elif command[0] == "type":
            typeHeler(command = command)
            # history.append(to_add_history_command)
        
        elif command[0] == "pwd":
            pwdHelper()
            # history.append(to_add_history_command)
        
        elif command[0] == "cd":
            changeDirectoryHelper(command = command)
            # history.append(to_add_history_command)
        
        elif command[0] == "history":
            # history.append(to_add_history_command)
            historyHelper(command = command)
        
        else:
            # command.insert(0, "type") # TEMP
            # typeHeler(command = command) # TEMP
            if not externalCommandRunnerHelper(command = command):
                print(f"{command[0]}: command not found")
            else:
                pass
                # history.append(to_add_history_command)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
