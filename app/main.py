import sys
import os
import subprocess
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.history import InMemoryHistory

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
# HISTORY_FILE = ".mshell_history"
HISTORY_FILE = Path(".mshell_history")
commands_this_session: list[str] = []
# current_history_file = HISTORY_FILE
# session = PromptSession(history=FileHistory(current_history_file))
session = PromptSession(history=InMemoryHistory())

def load_history() -> list[str]:
    try:
        with HISTORY_FILE.open("r", encoding = "utf-8") as file:
            return [line.rstrip("\n") for line in file if line.strip()]
    except FileNotFoundError:
        return []

def save_history() -> None:
    with HISTORY_FILE.open("w", encoding = "utf-8") as file:
        for cmd in commands_this_session:
            file.write(cmd + "\n")


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


def copySessionCommandsToHistory(history_backend: FileHistory) -> None:
    for cmd in commands_this_session:
        if cmd.strip():
            history_backend.append_string(cmd)


def appendHistoryFileToDefaultHistory(source_history_file: str) -> None:
    source_history = FileHistory(source_history_file)
    for cmd in source_history.get_strings():
        if cmd.strip():
            session.history.append_string(cmd)

# TESTING OUT
def unique_history_navigator_helper(history: list[str]) -> list[str]:
    seen = set()
    to_return = []

    for cmd in reversed(history):
        if cmd not in seen:
            seen.add(cmd)
            to_return.append(cmd)
    
    return list(reversed(to_return))

# TESTING OUT
def rebuild_prompt_memory() -> None:
    navigator_history = unique_history_navigator_helper(commands_this_session)

    new_history = InMemoryHistory()

    for cmd in navigator_history:
        new_history.append_string(cmd)
    
    session.history = new_history

def add_command_to_history(cmd: str) -> None:
    cmd = cmd.strip()

    if not cmd:
        return
    
    commands_this_session.append(cmd)
    save_history()
    rebuild_prompt_memory()


    
def historyHelper(args: list[str]) -> None:
    global commands_this_session


    if len(args) == 1:

        for i in range(len(commands_this_session)):
            print(f"    {i + 1} {commands_this_session[i]}")


        # entries = getHistoryEntries()
        # # print("Entries: ", entries)
        # for i in range(len(entries)):
        #     print(f"    {i + 1} {entries[i]}")
        #     # print("2")
    
    else: 

        # READING FROM A FILE [NOTE: NOT DONE TODO]
        if args[1] == "-r":
            global session
            global current_history_file

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
            except FileNotFoundError:
                print(f"history: {path}: file not found")
            return
            
            ###### BLOCKING OUT FOR TESTING ######
            # with open(args[2], "r", encoding="utf-8") as file:
            #     # commands_from_other_file = file.readlines()
            #     commands_from_other_file = []
            #     for line in file:
            #         commands_from_other_file.append(line.strip())
            #     # print(commands_from_other_file)
            #     for command in commands_from_other_file:
            #         commands_this_session.append(command)
            # file.close()

            # path_to_history_file = os.path.expanduser(args[2])
            # history_parent = os.path.dirname(path_to_history_file)
            # if history_parent:
            #     os.makedirs(history_parent, exist_ok = True)
            # current_history_file = path_to_history_file

            # # session = PromptSession(history=FileHistory(current_history_file))
            # new_history = FileHistory(current_history_file)
            # session = PromptSession(history=new_history)


            # session = PromptSession(history=FileHistory(current_history_file))


            # # global session 
            # # path_to_history_file = command[2]
            # # session = PromptSession(history=FileHistory(path_to_history_file))
            ###### ENDING TEST BLOCK ######

        else:
            try: 
                from_history = int(args[1])
            except ValueError:
                return
            # if from_history == 2:
            #     print(session.history.get_strings())
            # entries = getHistoryEntries()
            # print(from_history)
            # if from_history == 2:
                # print(commands_this_session)
                # print(entries)
            # start = max(len(entries) - from_history, 0)
            unique_history = unique_history_navigator_helper(history = commands_this_session)
            if from_history == 2:
                print(unique_history)
            # start = max(len(commands_this_session) - from_history, 0)
            start = max(len(unique_history) - from_history, 0)
            for i in range(start, len(unique_history)):
                print(f"   {i + 1} {unique_history[i]}")
            # for i in range(start, len(commands_this_session)):
            #     print(f"   {i + 1} {commands_this_session[i]}")
            # for i in range(start, len(entries)):
            #     print(f"   {i + 1} {entries[i]}")



            # from_history = int(command[1])
            # for i in range(len(history) - from_history, len(history)):
            #     print(f"   {i} {history[i]}")

def main():
    while True:
        global commands_this_session
        # sys.stdout.flush()
        # sys.stdout.write("$ ") # Used instead of print because this way does not include a newline
        # command = input("$ ")
        command = session.prompt("$ ") # How the command gets written into the history

        # TESTING OUT
        if command.strip():
            add_command_to_history(command)
            # commands_this_session.append(command)
            # rebuild_prompt_memory(session, commands_this_session)
        

        # command_to_add_history = command
        # commands_this_session.append(command)
        # print("commands this session: ", commands_this_session)
        # command = command.split(" ")
        command = command.split()
        # print(len(command))
        # print(command)
        
        if len(command) == 1 and command[0] == '':
            continue

        if command[0] == "exit":
            break
        elif command[0] == "echo":
            echoHelper(command = command)
            # history.append(to_add_history_command)
            # commands_this_session.append(command_to_add_history)
            
        elif command[0] == "type":
            typeHeler(command = command)
            # history.append(to_add_history_command)
            # commands_this_session.append(command_to_add_history)
        
        elif command[0] == "pwd":
            pwdHelper()
            # history.append(to_add_history_command)
            # commands_this_session.append(command_to_add_history)
        
        elif command[0] == "cd":
            changeDirectoryHelper(command = command)
            # history.append(to_add_history_command)
            # commands_this_session.append(command_to_add_history)
        
        elif command[0] == "history":
            # history.append(to_add_history_command)
            historyHelper(args = command)
            # commands_this_session.append(command_to_add_history)
        
        else:
            # command.insert(0, "type") # TEMP
            # typeHeler(command = command) # TEMP
            if not externalCommandRunnerHelper(command = command):
                print(f"{command[0]}: command not found")
            else:
                pass
                # history.append(to_add_history_command)
            # commands_this_session.append(command_to_add_history)
        sys.stdout.flush()

if __name__ == "__main__":
    commands_this_session = load_history()
    rebuild_prompt_memory()
    main()
