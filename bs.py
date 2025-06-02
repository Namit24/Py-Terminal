import os
import sys
import subprocess
import shlex
import getpass
import socket
import datetime
from pathlib import Path


class Terminal:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.username = getpass.getuser()
        self.hostname = socket.gethostname()
        self.history = []
        self.builtin_commands = {
            'cd', 'pwd', 'exit', 'help', 'clear', 'cls', 'history',
            'echo', 'dir', 'ls', 'cat', 'type', 'mkdir', 'md', 'rmdir', 'rd'
        }

    def run(self):
        print("Python Terminal Emulator v1.0")
        print("Type 'help' for available commands.\n")

        while True:
            try:
                self.print_prompt()
                user_input = input().strip()

                if not user_input:
                    continue

                # Add to history
                self.history.append(user_input)

                # Execute command
                if not self.execute_command(user_input):
                    break

            except KeyboardInterrupt:
                print("\n^C")
                continue
            except EOFError:
                break

        print("Goodbye!")

    def print_prompt(self):
        # Show current directory with ~ for home
        home_dir = os.path.expanduser("~")
        display_dir = self.current_dir

        if self.current_dir.startswith(home_dir):
            display_dir = "~" + self.current_dir[len(home_dir):]

        if os.name == 'nt':  # Windows
            print(f"{self.current_dir}>", end=" ")
        else:  # Unix/Linux
            print(f"\033[32m{self.username}@{self.hostname}\033[0m:\033[34m{display_dir}\033[0m$ ", end="")

    def execute_command(self, user_input):
        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Error: Invalid command syntax")
            return True

        if not args:
            return True

        command = args[0].lower()

        # Handle built-in commands
        if command == 'exit':
            return False
        elif command == 'cd':
            return self.handle_cd(args)
        elif command == 'pwd':
            return self.handle_pwd()
        elif command == 'help':
            return self.handle_help()
        elif command in ['clear', 'cls']:
            return self.handle_clear()
        elif command == 'history':
            return self.handle_history()
        elif command == 'echo':
            return self.handle_echo(args)
        elif command in ['dir', 'ls']:
            return self.handle_dir(args)
        elif command in ['cat', 'type']:
            return self.handle_cat(args)
        elif command in ['mkdir', 'md']:
            return self.handle_mkdir(args)
        elif command in ['rmdir', 'rd']:
            return self.handle_rmdir(args)
        else:
            # Execute external command
            return self.execute_external_command(args)

    def handle_cd(self, args):
        if len(args) == 1:
            # No arguments - go to home directory
            target_dir = os.path.expanduser("~")
        else:
            target_dir = args[1]

            # Handle ~ expansion
            if target_dir.startswith("~"):
                target_dir = os.path.expanduser(target_dir)

            # Handle relative paths
            if not os.path.isabs(target_dir):
                target_dir = os.path.join(self.current_dir, target_dir)

        try:
            os.chdir(target_dir)
            self.current_dir = os.getcwd()
        except FileNotFoundError:
            print(f"cd: {target_dir}: No such file or directory")
        except PermissionError:
            print(f"cd: {target_dir}: Permission denied")
        except Exception as e:
            print(f"cd: {e}")

        return True

    def handle_pwd(self):
        print(self.current_dir)
        return True

    def handle_help(self):
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

    def handle_clear(self):
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux
            os.system('clear')
        return True

    def handle_history(self):
        for i, cmd in enumerate(self.history, 1):
            print(f"{i:4d}  {cmd}")
        return True

    def handle_echo(self, args):
        if len(args) > 1:
            print(" ".join(args[1:]))
        else:
            print()
        return True

    def handle_dir(self, args):
        target_dir = self.current_dir if len(args) == 1 else args[1]

        try:
            path = Path(target_dir)
            if not path.exists():
                print(f"Directory not found: {target_dir}")
                return True

            if not path.is_dir():
                print(f"Not a directory: {target_dir}")
                return True

            print(f"\nDirectory of {path.absolute()}\n")

            items = list(path.iterdir())
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

            file_count = 0
            dir_count = 0
            total_size = 0

            # Show parent directory if not root
            if path.parent != path:
                print(f"{'<DIR>':>12}          ..")
                dir_count += 1

            for item in items:
                try:
                    stat = item.stat()
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)

                    if item.is_dir():
                        print(f"{mtime.strftime('%m/%d/%Y  %I:%M %p')} {'<DIR>':>12}          {item.name}")
                        dir_count += 1
                    else:
                        size = stat.st_size
                        print(f"{mtime.strftime('%m/%d/%Y  %I:%M %p')} {size:>12,}          {item.name}")
                        file_count += 1
                        total_size += size

                except (OSError, PermissionError):
                    print(f"{'???':>12}          {item.name} (access denied)")

            print(f"\n{file_count:>16} File(s) {total_size:>15,} bytes")
            print(f"{dir_count:>16} Dir(s)")

        except PermissionError:
            print(f"Access denied: {target_dir}")
        except Exception as e:
            print(f"Error listing directory: {e}")

        return True

    def handle_cat(self, args):
        if len(args) < 2:
            print("Usage: cat/type <filename>")
            return True

        filename = args[1]
        try:
            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                print(f.read(), end='')
        except FileNotFoundError:
            print(f"File not found: {filename}")
        except PermissionError:
            print(f"Permission denied: {filename}")
        except Exception as e:
            print(f"Error reading file: {e}")

        return True

    def handle_mkdir(self, args):
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

    def handle_rmdir(self, args):
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
            if e.errno == 39:  # Directory not empty
                print(f"Directory not empty: {dirname}")
            else:
                print(f"Error removing directory: {e}")
        except Exception as e:
            print(f"Error removing directory: {e}")

        return True

    def execute_external_command(self, args):
        try:
            result = subprocess.run(args, cwd=self.current_dir,
                                    capture_output=False, text=True)
            return True
        except FileNotFoundError:
            print(f"Command not found: {args[0]}")
        except Exception as e:
            print(f"Error executing command: {e}")

        return True


if __name__ == "__main__":
    terminal = Terminal()
    terminal.run()