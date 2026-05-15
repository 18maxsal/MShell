import sys


def main():
    while True:
        sys.stdout.write("$ ") # Used instead of print because this way does not include a newline
        command = input().split(" ")
        if command[0] == "exit":
            break
        elif command[0] == "echo":
            # to_print = command.split(" ")
            to_print = ""
            if len(command) > 1:
                to_print = " ".join(command[1:])
            print(to_print)
        else:
            print(f"{command[0]}: command not found")
    


if __name__ == "__main__":
    main()
