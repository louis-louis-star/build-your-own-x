/**
 * bing_shell - A simple Unix shell written in C
 *
 * 模块化头文件，包含所有公共声明和宏定义
 */

#ifndef SHELL_H
#define SHELL_H

#include <sys/wait.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <pwd.h>
#include <linux/limits.h>
#include <fcntl.h>
#include <stdbool.h>
#include <signal.h>
#include <glob.h>

/* 缓冲区大小定义 */
#define SHELL_TOK_BUFSIZE 64
#define SHELL_TOK_DELIM " \t\r\n\a"
#define HISTORY_FILE ".bing_shell_history"
#define CONFIG_FILE ".bingshellrc"
#define MAX_HISTORY 1000
#define MAX_PIPES 10
#define MAX_JOBS 100

/* ANSI 颜色代码 */
#define COLOR_RED     "\033[1;31m"
#define COLOR_GREEN   "\033[1;32m"
#define COLOR_YELLOW  "\033[1;33m"
#define COLOR_BLUE    "\033[1;34m"
#define COLOR_MAGENTA "\033[1;35m"
#define COLOR_CYAN    "\033[1;36m"
#define COLOR_WHITE   "\033[1;37m"
#define COLOR_RESET   "\033[0m"

/* 命令结构体 */
typedef struct {
    char **args;
    int argc;
    char *input_file;
    char *output_file;
    bool append_output;
    bool background;
} Command;

/* 命令行结构体 */
typedef struct {
    Command *commands;
    int cmd_count;
    bool has_pipe;
} CommandLine;

/* 任务状态 */
typedef enum { JOB_RUNNING, JOB_STOPPED, JOB_DONE } JobState;

/* 任务结构 */
typedef struct {
    pid_t pid;
    int job_id;
    char command[256];
    JobState state;
    int active;
} Job;

/* 全局变量 */
extern int last_exit_status;
extern Job jobs[MAX_JOBS];
extern int job_count;
extern pid_t current_foreground_pid;

/* 函数声明 */
void shell_get_prompt(char *buf, int size);
void shell_init_signals(void);
void shell_set_foreground(pid_t pid);
void shell_readline_init(void);
void shell_readline_cleanup(void);
char *shell_read_line(void);
char **shell_split_line(char *line);
char *shell_expand_tilde(const char *path);
CommandLine *shell_parse_command_line(char *line);
void free_command_line(CommandLine *cmdline);
char *shell_expand_variables(const char *str);
char **shell_expand_wildcards(char **args, int *argc);
int shell_launch(char **args);
int shell_execute_single(char **args);
int shell_execute(char **args);
int shell_execute_line(char *line);
int shell_num_builtins(void);
char *shell_expand_alias(const char *cmd);
int shell_cd(char **args);
int shell_help(char **args);
int shell_exit(char **args);
int shell_history(char **args);
int shell_jobs(char **args);
int shell_fg(char **args);
int shell_bg(char **args);
int shell_export(char **args);
int shell_unset(char **args);
int shell_add_job(pid_t pid, const char *cmd);
void shell_remove_job(pid_t pid);
void shell_update_jobs(void);
int shell_find_job_by_id(int job_id);
void shell_stop_job(pid_t pid);
void shell_continue_job(pid_t pid, int foreground);
void shell_init_env(void);
char *shell_getenv(const char *name);
int shell_setenv(const char *name, const char *value);
int shell_unsetenv(const char *name);
void shell_load_config(void);

#endif /* SHELL_H */

