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

/* 缓冲区大小定义 */
#define SHELL_TOK_BUFSIZE 64
#define SHELL_TOK_DELIM " \t\r\n\a"
#define HISTORY_FILE ".bing_shell_history"
#define MAX_HISTORY 1000
#define MAX_PIPES 10

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
    char **args;        /* 参数数组 */
    int argc;           /* 参数数量 */
    char *input_file;   /* 输入重定向文件 */
    char *output_file;  /* 输出重定向文件 */
    bool append_output; /* 是否追加输出 */
    bool background;    /* 是否后台运行 */
} Command;

/* 命令行结构体 */
typedef struct {
    Command *commands;  /* 命令数组 */
    int cmd_count;      /* 命令数量 */
    bool has_pipe;      /* 是否有管道 */
} CommandLine;

/* ===== prompt.c ===== */
/**
 * 生成提示符字符串
 * @param buf 缓冲区
 * @param size 缓冲区大小
 */
void shell_get_prompt(char *buf, int size);

/* ===== signal.c ===== */
/**
 * 初始化信号处理
 */
void shell_init_signals(void);

/* ===== readline.c ===== */
/**
 * 初始化readline
 */
void shell_readline_init(void);

/**
 * 清理readline资源
 */
void shell_readline_cleanup(void);

/**
 * 读取一行用户输入
 * @return 动态分配的字符串，调用者需要free
 */
char *shell_read_line(void);

/* ===== parse.c ===== */
/**
 * 解析命令行字符串为参数数组
 * 使用空格、制表符等作为分隔符
 */
char **shell_split_line(char *line);

/**
 * 展开路径中的 ~ 为家目录
 * @param path 路径字符串
 * @return 展开后的路径，调用者需要free
 */
char *shell_expand_tilde(const char *path);

/**
 * 解析完整命令行（支持多管道、重定向、后台运行）
 */
CommandLine *shell_parse_command_line(char *line);

/**
 * 释放命令行结构体
 */
void free_command_line(CommandLine *cmdline);

/* ===== execute.c ===== */
/**
 * 启动外部进程执行命令
 * @param args 参数数组
 * @return 1表示继续执行，0表示退出
 */
int shell_launch(char **args);

/**
 * 执行单条命令（内置命令或外部命令）
 */
int shell_execute_single(char **args);

/**
 * 执行命令（内置命令或外部命令）
 * @param args 参数数组
 * @return 1表示继续执行，0表示退出
 */
int shell_execute(char **args);

/**
 * 执行命令行（支持管道）
 * @param line 原始命令行
 * @return 1表示继续执行，0表示退出
 */
int shell_execute_line(char *line);

/* ===== builtin.c ===== */
/**
 * 获取内置命令数量
 */
int shell_num_builtins(void);

/* 内置命令函数 */
int shell_cd(char **args);
int shell_help(char **args);
int shell_exit(char **args);
int shell_history(char **args);
int shell_jobs(char **args);

/* 别名展开 */
char *shell_expand_alias(const char *cmd);

/* 后台任务管理 */
void shell_add_job(pid_t pid, const char *cmd);
void shell_remove_job(pid_t pid);
void shell_update_jobs(void);

#endif /* SHELL_H */

