import sys
import os
import subprocess
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.history import InMemoryHistory

BUILT_INS = ["echo", "exit", "type", "pwd", "cd", "history"]
HISTFILE = Path(".mshell_history")
commands_this_session: list[str] = []
session = PromptSession(history=InMemoryHistory())
history_append_start_pointer = 0
history_loaded_start_pointer = 0


def load_history() -> list[str]:
    """
    Loads the history from the given HISTFILE.  If no file is 
    defined, returns an empty array instead.
    """
    try:
        with HISTFILE.open("r", encoding = "utf-8") as file:
            return [line.rstrip("\n") for line in file if line.strip()]
    except FileNotFoundError:
        return []

def save_history() -> None:
    """
    Saves all the commands used this session to the designated
    HISTFILE.
    """
    with HISTFILE.open("w", encoding = "utf-8") as file:
        for cmd in commands_this_session:
            file.write(cmd + "\n")

def echoHelper(command: list[str]) -> None:
    """
    Handles the logic for the 'echo' built-in.
    Prints the given string to output.
    """
    to_print = ""
    if len(command) > 1:
        to_print = " ".join(command[1:])
    print(to_print)

def typeHeler(command: list[str]) -> None:
    """
    Handles the logic for the 'type' built-in.
    Prints whether the given command is of type built-in, 
    executable that exists, or if a command that does 
    not exist 

    Returns: None
    """
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
    """
    Handles the logic for running non-built-in files/commands
    if they exist.

    Returns: True if the command was found, false otherwise
       
    """
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
    """Prints current working directory"""
    print(Path.cwd())

def changeDirectoryHelper(command: list[str]) -> None:
    """
    Handles logic for changing the current working directory
    
    Args: 
        command (list[str]): THe full coammnd separated into a list
    Returns: None
    """

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


def unique_history_navigator_helper(history: list[str]) -> list[str]:
    """
    Collects one copy of each used command this session in chonological 
    order.
    
    Args:
        history (list[str]): All the commands used this session

    Returns: 
        list[str]: An array containing only unique commands sorted from oldest
        to newest
    """
    
    seen = set()
    to_return = []

    for cmd in reversed(history):
        if cmd not in seen:
            seen.add(cmd)
            to_return.append(cmd)
    
    return list(reversed(to_return))

# TODO: Look over this function [DONE???, maybe a onceover]
def rebuild_prompt_memory() -> None:
    """
    Replaces the sessions history with a history only containing a single 
    copy of each command used this session in chronological order
    (i.e. oldest to newest)
    """
    global session # May need to comment in later
    navigator_history = unique_history_navigator_helper(commands_this_session)

    new_history = InMemoryHistory()

    for cmd in navigator_history:
        new_history.append_string(cmd)
    
    session.history = new_history

# TODO: LOOK OVER
def add_command_to_history(cmd: str) -> None:
    """
    Adds given command to the command history this session and 
    Rebuilds it as well
    
    """
    cmd = cmd.strip()

    if not cmd:
        return
    
    commands_this_session.append(cmd)
    # save_history() # TEMP CHANGE
    rebuild_prompt_memory()

# NOTE: TESTING OUT
def append_new_history_to_file() -> None:
    """
    Writes the command history from the global starting point 
    (i.e. the history_loaded_start_pointer) 
    to the file address at the global HISTFILE.  
    """
    global history_loaded_start_pointer
    HISTFILE.parent.mkdir(parents=True, exist_ok=True)
    new_commands = commands_this_session[history_loaded_start_pointer:]
    if not new_commands:
        return
    # print(history_loaded_start_pointer)
    # print(new_commands)
    # print()
    # print(commands_this_session)
    # if history_loaded_start_pointer == 0:
    #     print("history_loaded_start_pointer is 0")
    with HISTFILE.open("a", encoding="utf-8") as file:
        file.writelines(cmd + "\n" for cmd in new_commands)
    
    history_loaded_start_pointer = len(commands_this_session)

    # if HISTFILE.parent != Path("."):
    #     HISTFILE.parent.mkdir(parents=True, exist_ok=True)

    # with HISTFILE.open("a", encoding="utf-8") as file:
    #     for i in range(history_loaded_start_pointer, len(commands_this_session)):
    #         file.write(commands_this_session[i] + "\n")
    
    
    
def historyHelper(args: list[str]) -> None:
    """
    Handles the logic for the history built-in and all its sub-commands
    """
    global commands_this_session

    # Case: printing the entire history (i.e. handling just "history") 
    if len(args) == 1:

        for i in range(len(commands_this_session)):
            print(f"    {i + 1} {commands_this_session[i]}")


    else: 

        # Case: reading from a file and adding it's commands to history
        # (i.e. handling "history -r <path-to-file>")
        if args[1] == "-r":
            global session

            if len(args) < 3:
                print("history: missing file path")
                return
            
            path = Path(args[2]).expanduser()
            try:
                with path.open("r", encoding="utf-8") as file:
                    for line in file:
                        cmd = line.rstrip("\n")
                        if cmd.strip():
                            commands_this_session.append(cmd)
                save_history()
                rebuild_prompt_memory()
                file.close()
            except FileNotFoundError:
                print(f"history: {path}: file not found")
            return
        
        # Case: Writing our history to a file
        elif args[1] == "-w":
            path = Path(args[2]).expanduser()
            try:
                with path.open("w", encoding="utf-8") as file:
                    for cmd in commands_this_session:
                        file.write(cmd + "\n")
                file.close()
            except FileNotFoundError:
                print(f"history: {path}: file not found")
                return
        
        # Case: Appending commands from history to a file 
        elif args[1] == "-a":
            global history_append_start_pointer
            path = Path(args[2]).expanduser()
            try:
                with path.open("a", encoding="utf-8") as file:
                    for index in range(history_append_start_pointer, len(commands_this_session)):
                        file.write(commands_this_session[index] + "\n")
                history_append_start_pointer = len(commands_this_session)
                file.close()
            except FileNotFoundError:
                print(f"history: {path}: file not found")
                return

        # Case: Printing out limiting history
        # (i.e. handling "history <number>")            
        else:
            try: 
                from_history = int(args[1])
            except ValueError:
                return
            start = max(len(commands_this_session) - from_history, 0)
            for i in range(start, len(commands_this_session)):
                print(f"   {i + 1} {commands_this_session[i]}")

def main():
    """
    The main loop for the program
    """
    global commands_this_session
    global HISTFILE
    global history_loaded_start_pointer
    if os.environ.get("HISTFILE"):
        # global HISTFILE
        # HISTFILE = Path(os.environ.get("HISTFILE"))
        HISTFILE = Path(os.environ.get("HISTFILE")).expanduser()
        commands_this_session = load_history()
        rebuild_prompt_memory()
        history_loaded_start_pointer = len(commands_this_session)



    while True:
        # sys.stdout.flush()
        # sys.stdout.write("$ ") # Used instead of print because this way does not include a newline
        # command = input("$ ")
        command = session.prompt("$ ") # How the command gets written into the history

        if command.strip():
            add_command_to_history(command)
        
        command = command.split()
        if not command:
            continue

        if command[0] == "exit":
            break
        elif command[0] == "echo":
            echoHelper(command = command)
            
        elif command[0] == "type":
            typeHeler(command = command)
        
        elif command[0] == "pwd":
            pwdHelper()
        
        elif command[0] == "cd":
            changeDirectoryHelper(command = command)
        
        elif command[0] == "history":
            historyHelper(args = command)
        
        else:
            if not externalCommandRunnerHelper(command = command):
                print(f"{command[0]}: command not found")
            else:
                pass
        sys.stdout.flush()
    # save_history() # May not need
    append_new_history_to_file()

if __name__ == "__main__":
    commands_this_session = []
    rebuild_prompt_memory()
    main()
