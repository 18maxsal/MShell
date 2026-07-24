import sys
import os
import subprocess
from pathlib import Path
import shutil
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion import Completer, Completion

from prompt_toolkit.output import Output
from prompt_toolkit.output import create_output
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.data_structures import Size
from prompt_toolkit.shortcuts import CompleteStyle

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import run_in_terminal


BUILT_INS = ["echo", "exit", "type", "pwd", "cd", "history"]
kb = KeyBindings()
last_tab_text = None
last_tab_matches = []

@kb.add("tab")
def _(event):
    """
    TODO: Fill in method description here

    TODO: Learn more about what this does
    """
    global last_tab_text, last_tab_matches
    buffer = event.current_buffer
    text = buffer.document.text_before_cursor

    if " " in text:
        event.app.output.bell()
        last_tab_text = None
        last_tab_matches = []
        return
    
    # matches = [cmd for cmd in BUILT_INS if cmd.startswith(text)]
    matches = get_command_matches(text)

    if len(matches) == 0:
        event.app.output.bell()
        last_tab_text = None
        last_tab_matches = []
        return
    
    if len(matches) == 1:
        # match = matches[0]

        buffer.delete_before_cursor(count=len(text))
        # buffer.insert_text(match + " ")
        buffer.insert_text(matches[0] + " ")
        last_tab_text = None
        last_tab_matches = []
        return
    
    # Multiple Matches
    if text == last_tab_text and matches == last_tab_matches:
        # print_matches(matches)
        print_matches(matches, text)
        last_tab_text = None
        last_tab_matches = []
        return

    common_prefix = os.path.commonprefix(matches)

    if len(common_prefix) > len(text):
        buffer.delete_before_cursor(count = len(text))
        buffer.insert_text(common_prefix)

        last_tab_text = common_prefix
        last_tab_matches = get_command_matches(common_prefix)
        return

    event.app.output.bell()
    last_tab_text = text
    last_tab_matches = matches
    

    # buffer.start_completion(select_first=False)

# def print_matches(matches: list[str]) -> None:
def print_matches(matches: list[str], current_text: str) -> None:
    """
    TODO: Fill in method description here
    """
    def printer():
        """
        TODO: Fill in method description here
        """

        print(f"$ {current_text}")
        print(" ".join(sorted(matches)))
    run_in_terminal(printer)


def get_executables_from_path() -> set[str]:
    """
    TODO: Fill in method description here
    """
    executables = set()

    path_env= os.environ.get("PATH", "")

    for directory in path_env.split(os.pathsep):
        if not directory:
            continue

        try:
            for name in os.listdir(directory):
                full_path = os.path.join(directory, name)

                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    executables.add(name)
        
        except FileNotFoundError:
            continue
        except NotADirectoryError:
            continue
        except PermissionError:
            continue
    
    return executables


def get_command_matches(prefix: str) -> list[str]:
    """
    TODO: Fill in method description here
    """
    commands = set(BUILT_INS)
    commands.update(get_executables_from_path())

    return sorted(cmd for cmd in commands if cmd.startswith(prefix))


class BuiltInCompleter(Completer):
    """
    TODO: fill in class definition here
    """

    def get_completions(self, document, complete_event):
        """
        TODO: fill in method definition here
        """
        text=  document.text_before_cursor

        if " " in text:
            return
        
        matches = [cmd for cmd in BUILT_INS if cmd.startswith(text)]
        # matches = self.get_command_matches(text)

        if len(matches) == 1: 
            match = matches[0]
            yield Completion(
                match + " ", 
                # matches[0] + " ",
                start_position =- len(text)
            )

def get_terminal_size():
    """
    TODO: fill in method definition here
    """
    size = shutil.get_terminal_size((80, 24))
    return Size(rows= size.lines, columns= size.columns)

if os.name == "nt":
    output = create_output()

else:
    output = Vt100_Output (
        stdout=sys.stdout,
        get_size=get_terminal_size,
        term=os.environ.get("TERM"),
        enable_cpr=False,
    )

# BUILT_INS = ["echo", "exit", "type", "pwd", "cd", "history"]
BUILT_INS_COMPLETER = WordCompleter(BUILT_INS)
HISTFILE = Path(".mshell_history")
commands_this_session: list[str] = []

# session = PromptSession(history=InMemoryHistory())

# NOTE: use this version of session variable for a more modern terminal experience
# session = PromptSession(history=InMemoryHistory(), completer=BUILT_INS_COMPLETER)

# NOTE: use this version of session variable for a more traditional terminal experience
# session = PromptSession(
#     history=InMemoryHistory(), 
#     completer=BuiltInCompleter(),
#     complete_while_typing=False, 
#     complete_style=CompleteStyle.READLINE_LIKE,
#     reserve_space_for_menu=0, 
#     output=output
# )
session = PromptSession(
    history=InMemoryHistory(), 
    completer=BuiltInCompleter(),
    complete_while_typing=False, 
    complete_style=CompleteStyle.READLINE_LIKE,
    reserve_space_for_menu=0, 
    output=output, 
    key_bindings=kb
)


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

# def echoHelper(command: list[str], is_redirected: bool, is_redirected_error: bool, 
#                is_redirected_append: bool, is_redirected_append_error: bool) -> None:
def echoHelper(command: list[str], is_redirected: bool, is_redirected_error: bool, 
               is_redirected_append: bool, is_redirected_append_error: bool, 
               is_pipeline: bool = False) -> str | None:
    """
    Handles the logic for the 'echo' built-in.
    Prints the given string to output.
    """
    to_print = ""
    # if is_redirected:
    if is_redirected or is_redirected_error or is_redirected_append or is_redirected_append_error:
        command, file_name = get_command_and_file_from_redirect(command)
    if len(command) > 1:
        to_print = " ".join(command[1:])
    
    if is_redirected:
        with open(file_name, "w", encoding="utf-8") as file:
            file.writelines(to_print)
            file.write("\n")
    elif is_redirected_error:
        print(to_print)
        with open(file_name, "w", encoding="utf-8") as file:
            pass
    elif is_redirected_append:
        with open(file_name, "a", encoding="utf-8") as file:
            file.writelines(to_print)
            file.write("\n") # may or may not need
    elif is_redirected_append_error:
        print(to_print)
        with open(file_name, "a", encoding="utf-8") as file:
            pass
    elif is_pipeline:
        return to_print
    else:
        print(to_print)

def typeHelper(command: list[str], is_pipeline: bool = False) -> str | None:
    """
    Handles the logic for the 'type' built-in.
    Prints whether the given command is of type built-in, 
    executable that exists, or if a command that does 
    not exist 

    Returns: None
    """
    if command[1] and command[1] in BUILT_INS:
        if is_pipeline:
            return f"{command[1]} is a shell builtin"
        else: 
            print(f"{command[1]} is a shell builtin")
    else: # Command is not Built-in
        if command[1]:
            to_find = shutil.which(command[1])
            if to_find:
                if is_pipeline:
                    return f"{command[1]} is {to_find}"
                else:
                    print(f"{command[1]} is {to_find}")
            else:
                if is_pipeline:
                    return f"{command[1]}: not found"
                else:
                    print(f"{command[1]}: not found")

        else: # Case: there is no command[1] (i.e. we just have "type " for input)
            if is_pipeline:
                return "not found"
            else:
                print("not found")

# def externalCommandRunnerHelper(command: list[str], is_redirected: bool, 
#                                 is_redirected_error: bool, 
#                                 is_redirected_append: bool, 
#                                 is_redirected_append_error: bool) -> bool:
def externalCommandRunnerHelper(command: list[str], is_redirected: bool, 
                                is_redirected_error: bool, 
                                is_redirected_append: bool, 
                                is_redirected_append_error: bool) -> bool:
    """
    Handles the logic for running non-built-in files/commands
    if they exist.

    Returns: True if the command was found, false otherwise
       
    """
    if is_redirected or is_redirected_error or is_redirected_append or is_redirected_append_error:
        command, file_name = get_command_and_file_from_redirect(command)
    executable = shutil.which(command[0])

    if executable is None:
        # return False
        return ""
    
    if is_redirected:
        with open(file_name, "w", encoding="utf-8") as file:
            subprocess.run(command, stdout=file)
    elif is_redirected_error:
        # result = subprocess.run(command, capture_output=True, text=True)
        with open(file_name, "w", encoding="utf-8") as file:
            subprocess.run(command, stderr=file)
    elif is_redirected_append:
        with open(file_name, "a", encoding="utf-8") as file:
            subprocess.run(command, stdout=file)
    elif is_redirected_append_error:
        with open(file_name, "a", encoding="utf-8") as file:
            subprocess.run(command, stderr=file)
    
    # Not redirecting anywhere
    else:
        subprocess.run(command)
        # return subprocess.run(command)
    # subprocess.run([executable] + command[1:])
    # subprocess.run(command)
    return True
    # return "Valid Output"

# def pwdHelper() -> None:
def pwdHelper() -> str:
    """Prints current working directory"""
    print(Path.cwd())
    # return str(Path.cwd())
    return Path.cwd()

def changeDirectoryHelper(command: list[str]) -> str | None:
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
    global session 
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
    with HISTFILE.open("a", encoding="utf-8") as file:
        file.writelines(cmd + "\n" for cmd in new_commands)
    
    history_loaded_start_pointer = len(commands_this_session)
    
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

def string_parser(command: str) -> list[str]:
    """
    Parses the given command into an array and supports 
    single and double quotes with escape characters (often
    denoted by a backslash) as well.
    """

    args = []
    curr = []
    in_single_quote = False
    in_double_quote = False
    building_arg = False

    index = 0

    while index < len(command):
        character = command[index]

        # Case: Single quotes (i.e. ').  Treat everything as a literal
        # Characters until the next single quote
        if in_single_quote:
            if character == '\'':
                in_single_quote = False
            else:
                curr.append(character)
            index += 1
            continue

        # Case: Double quotes.  Handle everything as a literal until the 
        # Next double quote
        if in_double_quote:
            if character == "\"":
                in_double_quote = False
            
            # Handles when we encounter a backslash within a double quoted statement
            elif character == "\\":
                if (index + 1) < len(command) and command[index + 1] in ["\"", "\\", "$", "`"]:
                    index += 1
                    character = command[index]
                #     curr.append(character)
                # else:
                #     curr.append(character)
                curr.append(character)
            else:
                curr.append(character)
            index += 1
            continue


        # if character.isspace():
        # Handles when we encounter a space
        if character == " ":
            if building_arg:
                args.append("".join(curr))
                curr = []
                building_arg = False
            index += 1
            continue

        # Handling the first single quote
        if character == '\'':
            in_single_quote = True
            building_arg = True
            index += 1
            continue

        # Handling the first double quote
        if character == "\"":
            in_double_quote = True
            building_arg = True
            index += 1
            continue

        # Handles backslash (i.e. "\") characters
        # We treat the character after the backslash
        # As a literal
        if character == "\\":
            index += 1
            character = command[index]
            curr.append(character)
            index += 1
            building_arg = True 
            continue
        curr.append(character)
        building_arg = True
        index += 1
    

    if building_arg:
        args.append("".join(curr))
        
    return args

def pipeline_parser(command: list[str]) -> list[list[str]]:
    """
    TODO: Fill in function defintion here
    """

    commands = []
    current_command = []

    for token in command:
        if token == "|":
            if not current_command:
                return []
            commands.append(current_command)
            current_command = []
        else:
            current_command.append(token)
    
    if not current_command:
        return []
    commands.append(current_command)
    return commands


    # to_return = []
    # try: 
    #     pipeline_index = command.index("|")
    #     # to_return.append([])
    #     to_return = [command[:pipeline_index], command[pipeline_index + 1:]]
    #     return to_return

    # except ValueError:
    #     return to_return

def run_pipeline(commands: list[list[str]]) -> None:
    """
    Handles command execution for when piping is used.
    """
    # TODO: Finish implementation for built-in exection for pipelines
    if commands[0][0] == "echo":
        process1 = echoHelper(command=commands[0], is_pipeline=True)
        process2 = subprocess.Popen(commands[1] ,stdin=process1)
    # accepted_pipeline_built_ins = ["echo", "type"]
    # if commands[0][0] in accepted_pipeline_built_ins:
    #     process1 = subprocess.Popen(commands[0], )
    elif commands[0][0] == "type":
        process1 = typeHelper(command=commands[0])
        process2 = subprocess.Popen(commands[1] ,stdin=process1)

    else:
        process1 = subprocess.Popen(commands[0], stdout=subprocess.PIPE)
        process2 = subprocess.Popen(commands[1] ,stdin=process1.stdout)
    process1.stdout.close()
    process2.communicate()




def get_command_and_file_from_redirect(command: list[str]) -> tuple[list[str], str]:
    """
    Extracts the destination file name when we wish to have our output
    redirected and written to a file.
    """
    command_to_return = command[:-2]
    file = command[-1] 
    return (command_to_return, file)

def main_loop_handler(command: list[str], is_redirected: bool, is_redirected_error: bool, 
                      is_redirected_append: bool, is_redirected_append_error: bool) -> str:
    if command[0] == "echo":
        # echoHelper(command = command)
        # echoHelper(command = command, is_redirected= is_redirected)
        # echoHelper(command = command, is_redirected= is_redirected, 
        #            is_redirected_error= is_redirected_error)
        # echoHelper(command = command, is_redirected= is_redirected, 
        #            is_redirected_error= is_redirected_error, 
        #            is_redirected_append= is_redirected_append)
        # echoHelper(command = command, is_redirected= is_redirected, 
        #             is_redirected_error= is_redirected_error, 
        #             is_redirected_append= is_redirected_append, 
        #             is_redirected_append_error= is_redirected_append_error)
        to_return = echoHelper(command = command, is_redirected= is_redirected, 
                    is_redirected_error= is_redirected_error, 
                    is_redirected_append= is_redirected_append, 
                    is_redirected_append_error= is_redirected_append_error)
        return to_return
        
    elif command[0] == "type":
        typeHelper(command = command)
    
    elif command[0] == "pwd":
        # pwdHelper()
        return pwdHelper()
    
    elif command[0] == "cd":
        changeDirectoryHelper(command = command)
    
    elif command[0] == "history":
        historyHelper(args = command)
    
    else:
        # if not externalCommandRunnerHelper(command = command):
        # if not externalCommandRunnerHelper(command = command, is_redirected= is_redirected):
        # if not externalCommandRunnerHelper(command = command, is_redirected= is_redirected, 
        #                                    is_redirected_error=is_redirected_error):
        # if not externalCommandRunnerHelper(command = command, is_redirected= is_redirected, 
        #                                    is_redirected_error=is_redirected_error, 
        #                                    is_redirected_append=is_redirected_append):
        is_external_command_found = externalCommandRunnerHelper(command = command, is_redirected= is_redirected, 
                                            is_redirected_error=is_redirected_error, 
                                            is_redirected_append=is_redirected_append, 
                                            is_redirected_append_error=is_redirected_append_error)
        if not is_external_command_found:
        # if not externalCommandRunnerHelper(command = command, is_redirected= is_redirected, 
        #                                     is_redirected_error=is_redirected_error, 
        #                                     is_redirected_append=is_redirected_append, 
        #                                     is_redirected_append_error=is_redirected_append_error):
            print(f"{command[0]}: command not found")
        # else:
        #     # print(output_from_external_command)
        #     return is_external_command_found
        else:
            return is_external_command_found
    sys.stdout.flush()


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


        # TESTING
        # command = string_parser(command)
        # add_command_to_history(command)
        
        if command.strip():
            add_command_to_history(command)
        
        # command = command.split()
        command = string_parser(command)
        # if [">", "1>"] in command:
        #     is_redirected = True

        # #TESTING
        # print(command)
        # print(get_command_and_file_from_redirect(command))
        # break
        
        # print(command)
        if not command:
            continue

        is_redirected = False
        is_redirected_error = False
        is_redirected_append = False
        is_redirected_append_error = False
        # if [">", "1>"] in command:
        if ">" in command or "1>" in command:
            is_redirected = True
        elif "2>" in command:
            is_redirected_error = True
        elif ">>" in command or "1>>" in command:
            is_redirected_append = True
        elif "2>>" in command:
            is_redirected_append_error = True

        # is_pipe = False
        # if "|" in command:
        #     is_pipe = True
        #     commands = pipeline_parser(command)
        #     # print(commands)
        #     if not commands:
        #         print("Error with input")
        #         continue

        if command[0] == "exit":
            break

        # Using a pipeline
        if "|" in command:
            commands = pipeline_parser(command)
            if not commands:
                print("Error with input.")
                continue
            run_pipeline(commands)
            continue
            # prev_command_output = run_pipeline_command(command1=commands[0], command2=commands[1])


            # print(commands)
            # break
            # prev_command_output = None
            # for cmd in commands:
            #     prev_command_output = run_pipeline_command(cmd, prev_command_output)
            #     if prev_command_output is None:
            #         break
            # if prev_command_output is not None:


            # if prev_command_output:
            #     print(prev_command_output, end="")
            # continue


            #     if not prev_command_output:
            #         result = main_loop_handler(command=cmd, 
            #                       is_redirected=is_redirected, 
            #                       is_redirected_error=is_redirected_error, 
            #                       is_redirected_append=is_redirected_append, 
            #                       is_redirected_append_error=is_redirected_append_error)
            #         # prev_command_output = result
            #         cmd.append(prev_command_output)
            #         prev_command_output = result
            #     else:
            #         result = main_loop_handler(command=cmd, 
            #                         is_redirected=is_redirected, 
            #                         is_redirected_error=is_redirected_error, 
            #                         is_redirected_append=is_redirected_append, 
            #                         is_redirected_append_error=is_redirected_append_error)
            #         prev_command_output = result
            # print(prev_command_output)

        else:
            main_loop_handler(command=command, 
                              is_redirected=is_redirected,
                              is_redirected_error=is_redirected_error, 
                              is_redirected_append=is_redirected_append, 
                              is_redirected_append_error=is_redirected_append_error)
            # result = main_loop_handler(command=command, 
            #                   is_redirected=is_redirected,
            #                   is_redirected_error=is_redirected_error, 
            #                   is_redirected_append=is_redirected_append, 
            #                   is_redirected_append_error=is_redirected_append_error)
            # print(result)
            
        # if command[0] == "exit":
        #     break
        # elif command[0] == "echo":
        #     # echoHelper(command = command)
        #     # echoHelper(command = command, is_redirected= is_redirected)
        #     # echoHelper(command = command, is_redirected= is_redirected, 
        #     #            is_redirected_error= is_redirected_error)
        #     # echoHelper(command = command, is_redirected= is_redirected, 
        #     #            is_redirected_error= is_redirected_error, 
        #     #            is_redirected_append= is_redirected_append)
        #     echoHelper(command = command, is_redirected= is_redirected, 
        #                is_redirected_error= is_redirected_error, 
        #                is_redirected_append= is_redirected_append, 
        #                is_redirected_append_error= is_redirected_append_error)
            
        # elif command[0] == "type":
        #     typeHelper(command = command)
        
        # elif command[0] == "pwd":
        #     pwdHelper()
        
        # elif command[0] == "cd":
        #     changeDirectoryHelper(command = command)
        
        # elif command[0] == "history":
        #     historyHelper(args = command)
        
        # else:
        #     # if not externalCommandRunnerHelper(command = command):
        #     # if not externalCommandRunnerHelper(command = command, is_redirected= is_redirected):
        #     # if not externalCommandRunnerHelper(command = command, is_redirected= is_redirected, 
        #     #                                    is_redirected_error=is_redirected_error):
        #     # if not externalCommandRunnerHelper(command = command, is_redirected= is_redirected, 
        #     #                                    is_redirected_error=is_redirected_error, 
        #     #                                    is_redirected_append=is_redirected_append):
        #     if not externalCommandRunnerHelper(command = command, is_redirected= is_redirected, 
        #                                        is_redirected_error=is_redirected_error, 
        #                                        is_redirected_append=is_redirected_append, 
        #                                        is_redirected_append_error=is_redirected_append_error):
        #         print(f"{command[0]}: command not found")
        #     else:
        #         pass
        # sys.stdout.flush()

    # save_history() # May not need
    append_new_history_to_file()

if __name__ == "__main__":
    commands_this_session = []
    rebuild_prompt_memory()
    main()
