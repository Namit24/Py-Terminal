import os
import subprocess
import shlex
import getpass
import socket
import datetime
from pathlib import Path

class SimpleTerminal:
    def __init__(self):
        self.cwd = os.getcwd()  # get current dir
        self.user = getpass.getuser()  # get user
        self.host = socket.gethostname()  # get pc name
        self.command_history = []  # just store past cmds
        self.builtins = {  # basic stuff handled by python
            'cd', 'pwd', 'exit', 'help', 'clear', 'cls', 'history',
            'echo', 'dir', 'ls', 'cat', 'type', 'mkdir', 'md', 'rmdir', 'rd'
        }

    def start(self):
        print("Python Terminal Emulator v1.0")
        print("Type 'help' for available commands.\n")
        while True:
            try:
                self.show_prompt()
                command_input = input().strip()
                if not command_input:
                    continue  # empty input, skip
                self.command_history.append(command_input)
                if not self.process_command(command_input):  # exit = False
                    break
            except KeyboardInterrupt:
                print("\n^C")  # ctrl+c
                continue
            except EOFError:
                break  # ctrl+d
        print("Goodbye!")

    def show_prompt(self):
        home = os.path.expanduser("~")
        path_display = self.cwd
        if self.cwd.startswith(home):
            path_display = "~" + self.cwd[len(home):]
        if os.name == 'nt':
            print(f"{self.cwd}>", end=" ")  # windows prompt
        else:
            # linux-ish prompt, colors just for fun
            print(f"\033[32m{self.user}@{self.host}\033[0m:\033[34m{path_display}\033[0m$ ", end="")

    def process_command(self, command_input):
        try:
            args = shlex.split(command_input)  # split like bash
        except ValueError:
            print("Error: Invalid command syntax")
            return True
        if not args:
            return True
        command = args[0].lower()
        # match commands to methods
        if command == 'exit':
            return False
        elif command == 'cd':
            return self.change_directory(args)
        elif command == 'pwd':
            return self.print_working_directory()
        elif command == 'help':
            return self.show_help()
        elif command in ['clear', 'cls']:
            return self.clear_screen()
        elif command == 'history':
            return self.show_history()
        elif command == 'echo':
            return self.echo_text(args)
        elif command in ['dir', 'ls']:
            return self.list_directory(args)
        elif command in ['cat', 'type']:
            return self.show_file_contents(args)
        elif command in ['mkdir', 'md']:
            return self.make_directory(args)
        elif command in ['rmdir', 'rd']:
            return self.remove_directory(args)
        else:
            return self.run_external_command(args)  # anything else

    def change_directory(self, args):
        # cd with or without path
        target = os.path.expanduser("~") if len(args) == 1 else args[1]
        if target.startswith("~"):
            target = os.path.expanduser(target)
        if not os.path.isabs(target):
            target = os.path.join(self.cwd, target)
        try:
            os.chdir(target)
            self.cwd = os.getcwd()
        except FileNotFoundError:
            print(f"cd: {target}: No such file or directory")
        except PermissionError:
            print(f"cd: {target}: Permission denied")
        except Exception as e:
            print(f"cd: {e}")
        return True

    def print_working_directory(self):
        print(self.cwd)
        return True

    def show_help(self):
        # not fancy, just shows stuff
        print("Built-in commands:")
        print("  cd [dir]        - Change directory")
        print("  pwd             - Print working directory")
        print("  echo [text]     - Print text")
        print("  dir/ls [path]   - List directory contents")
        print("  cat/type [file] - Display file contents")
        print("  mkdir/md [dir]  - Create directory")
        print("  rmdir/rd [dir]  - Remove empty directory")
        print("  history         - Show command history")
        print("  clear/cls       - Clear screen")
        print("  help            - Show this help")
        print("  exit            - Exit terminal")
        print("\nOther commands will be executed as external programs.")
        return True

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')  # lazy clear
        return True

    def show_history(self):
        # shows the command list
        for i, cmd in enumerate(self.command_history, 1):
            print(f"{i:4d}  {cmd}")
        return True

    def echo_text(self, args):
        print(" ".join(args[1:]) if len(args) > 1 else "")
        return True

    def list_directory(self, args):
        path = self.cwd if len(args) == 1 else args[1]
        try:
            p = Path(path)
            if not p.exists():
                print(f"Directory not found: {path}")
                return True
            if not p.is_dir():
                print(f"Not a directory: {path}")
                return True
            print(f"\nDirectory of {p.absolute()}\n")
            items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            file_count = 0
            dir_count = 0
            total_size = 0
            if p.parent != p:
                print(f"{'<DIR>':>12}          ..")  # go up
                dir_count += 1
            for item in items:
                try:
                    stats = item.stat()
                    mod_time = datetime.datetime.fromtimestamp(stats.st_mtime)
                    if item.is_dir():
                        print(f"{mod_time.strftime('%m/%d/%Y  %I:%M %p')} {'<DIR>':>12}          {item.name}")
                        dir_count += 1
                    else:
                        size = stats.st_size
                        print(f"{mod_time.strftime('%m/%d/%Y  %I:%M %p')} {size:>12,}          {item.name}")
                        file_count += 1
                        total_size += size
                except (OSError, PermissionError):
                    print(f"{'???':>12}          {item.name} (access denied)")
            print(f"\n{file_count:>16} File(s) {total_size:>15,} bytes")
            print(f"{dir_count:>16} Dir(s)")
        except PermissionError:
            print(f"Access denied: {path}")
        except Exception as e:
            print(f"Error listing directory: {e}")
        return True

    def show_file_contents(self, args):
        if len(args) < 2:
            print("Usage: cat/type <filename>")
            return True
        filename = args[1]
        try:
            with open(filename, 'r', encoding='utf-8', errors='replace') as file:
                print(file.read(), end='')
        except FileNotFoundError:
            print(f"File not found: {filename}")
        except PermissionError:
            print(f"Permission denied: {filename}")
        except Exception as e:
            print(f"Error reading file: {e}")
        return True

    def make_directory(self, args):
        if len(args) < 2:
            print("Usage: mkdir/md <directory>")
            return True
        dirname = args[1]
        try:
            os.makedirs(dirname, exist_ok=True)
            print(f"Directory created: {dirname}")
        except Exception as e:
            print(f"Error creating directory: {e}")
        return True

    def remove_directory(self, args):
        if len(args) < 2:
            print("Usage: rmdir/rd <directory>")
            return True
        dirname = args[1]
        try:
            os.rmdir(dirname)
            print(f"Directory removed: {dirname}")
        except FileNotFoundError:
            print(f"Directory not found: {dirname}")
        except OSError as e:
            if e.errno == 39:
                print(f"Directory not empty: {dirname}")
            else:
                print(f"Error removing directory: {e}")
        except Exception as e:
            print(f"Error removing directory: {e}")
        return True

    def run_external_command(self, args):
        try:
            subprocess.run(args, cwd=self.cwd, capture_output=False, text=True)
        except FileNotFoundError:
            print(f"Command not found: {args[0]}")
        except Exception as e:
            print(f"Error executing command: {e}")
        return True

if __name__ == "__main__":
    shell = SimpleTerminal()
    shell.start()
