import sys

BUILT_INS = ["echo", "exit", "type"]

def main():
    while True:
        sys.stdout.write("$ ") # Used instead of print because this way does not include a newline
        command = input().split(" ")
        if command[0] == "exit":
            break
        elif command[0] == "echo":
            to_print = ""
            if len(command) > 1:
                to_print = " ".join(command[1:])
            print(to_print)
        elif command[0] == "type":
            if command[1] and command[1] in BUILT_INS:
                print(f"{command[1]} is a shell builtin")
            else: # Case: there is no command[1] (i.e. we just have "type " for input)
                #TODO: Finish
                if command[1]:
                    print(f"{command[1]}: not found")
                else:
                    print("not found")
        else:
            print(f"{command[0]}: command not found")
    


if __name__ == "__main__":
    main()
