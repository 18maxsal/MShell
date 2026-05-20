import sys
import os
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
            # print(path_list)
            for i in range(len(path_list)):
                # print(f"{i}: {path_list[i]}")
                if os.path.isfile(path_list[i]) and os.access(path_list[i], os.X_OK):
                    print(f"{command[1]} is {path_list[i]}")
                    return

            # path = Path.cwd()
            # path = Path('/')
            # for subdir in path.iterdir():
            #     if subdir.is_dir():
            #         print(subdir)
            # print(f"current path: {path}")

            print(f"{command[1]}: not found")


        else: # Case: there is no command[1] (i.e. we just have "type " for input)
            print("not found")

def main():
    while True:
        sys.stdout.write("$ ") # Used instead of print because this way does not include a newline
        command = input().split(" ")
        if command[0] == "exit":
            break
        elif command[0] == "echo":
            echoHelper(command = command)
            
            # to_print = ""
            # if len(command) > 1:
            #     to_print = " ".join(command[1:])
            # print(to_print)

        elif command[0] == "type":
            typeHeler(command = command)
            # if command[1] and command[1] in BUILT_INS:
            #     print(f"{command[1]} is a shell builtin")
            # else: # Command is not Built-in
            #     if command[1]:

            #         print(f"{command[1]}: not found")


            #     else: # Case: there is no command[1] (i.e. we just have "type " for input)
            #         print("not found")
        
        else:
            print(f"{command[0]}: command not found")
    


if __name__ == "__main__":
    main()
