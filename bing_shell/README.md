# bing_shell - A Unix Shell in C

A feature-rich Unix shell implemented in C, supporting pipes, redirects, job control, and more.

## Features

- **Command Execution**: Execute external commands and built-in commands
- **Pipes**: Support for multiple pipes (`cmd1 | cmd2 | cmd3`)
- **I/O Redirection**: Input (`<`), output (`>`), and append (`>>`) redirection
- **Background Jobs**: Run commands in background with `&`
- **Job Control**: `jobs`, `fg`, `bg` commands and `Ctrl+Z` support
- **Variable Expansion**: Environment variables (`$VAR`) and exit status (`$?`)
- **Wildcards**: Glob patterns (`*`, `?`, `[...]`)
- **Tilde Expansion**: `~` expands to home directory
- **Command History**: Arrow keys navigation and `history` command
- **Tab Completion**: Auto-complete for built-in commands
- **Aliases**: Pre-defined aliases (`ll`, `la`, `l`)

## Building

### Prerequisites

- GCC compiler
- Readline library (`libreadline-dev`)

### Install Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install libreadline-dev

# Fedora/RHEL
sudo dnf install readline-devel

# macOS (with Homebrew)
brew install readline
```

### Compile

```bash
cd bing_shell
make
```

### Run

```bash
./bing_shell
```

## Built-in Commands

| Command | Description |
|---------|-------------|
| `cd [dir]` | Change directory (supports `~`) |
| `help` | Show help information |
| `exit` | Exit the shell |
| `history` | Show command history |
| `jobs` | List background jobs |
| `fg [%job]` | Bring job to foreground |
| `bg [%job]` | Continue job in background |
| `export VAR=val` | Set environment variable |
| `unset VAR` | Remove environment variable |

## Usage Examples

### Basic Commands
```bash
ls -la
echo "Hello World"
cat file.txt
```

### Pipes
```bash
ls -la | grep ".c"
cat file.txt | sort | uniq
ps aux | grep bash | wc -l
```

### Redirections
```bash
# Output to file
echo "Hello" > output.txt

# Append to file
echo "World" >> output.txt

# Input from file
sort < input.txt

# Combined
cat < input.txt | sort > output.txt
```

### Background Jobs
```bash
# Run in background
sleep 10 &

# List jobs
jobs

# Bring to foreground
fg %1

# Send to background
bg %1
```

### Variables
```bash
# Set variable
export MY_VAR=hello

# Use variable
echo $MY_VAR

# Exit status
echo $?
```

### Wildcards
```bash
ls *.c
cat file?.txt
ls [a-z]*.txt
```

### Job Control
```bash
# Start a long-running process
sleep 100

# Press Ctrl+Z to stop it
^Z
[1]  Stopped                 sleep 100

# Continue in background
bg %1

# Or bring to foreground
fg %1
```

## Configuration

The shell reads configuration from `~/.bingshellrc` on startup. You can set aliases and environment variables there.

## History

Command history is saved to `~/.bing_shell_history`.

## Project Structure

```
bing_shell/
├── main.c      # Main program entry and shell loop
├── shell.h     # Header file with declarations
├── readline.c  # Input reading with readline
├── parse.c     # Command parsing and variable expansion
├── execute.c   # Command execution and pipes
├── builtin.c   # Built-in commands implementation
├── prompt.c    # Prompt display
├── signal.c    # Signal handling (Ctrl+C, Ctrl+Z)
├── jobs.c      # Job control management
├── envvar.c    # Environment variable handling
├── config.c    # Configuration file loading
└── Makefile    # Build configuration
```

## License

This project is for educational purposes.

## Author

bing_shell - A learning project for understanding Unix shell internals.

