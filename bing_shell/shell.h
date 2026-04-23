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

/* 缓冲区大小定义 */
#define SHELL_TOK_BUFSIZE 64
#define SHELL_TOK_DELIM " \t\r\n\a"
#define HISTORY_FILE ".bing_shell_history"
#define MAX_HISTORY 1000

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
 * @param line 命令行字符串
 * @return 动态分配的参数数组，调用者需要free
 */
char **shell_split_line(char *line);

/**
 * 展开路径中的 ~ 为家目录
 * @param path 路径字符串
 * @return 展开后的路径，调用者需要free
 */
char *shell_expand_tilde(const char *path);

/**
 * 检查命令行是否包含管道
 */
char *find_pipe(char *line);

/**
 * 解析管道命令
 */
void split_pipe_command(char *line, char **cmd1, char **cmd2);

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

#endif /* SHELL_H */

