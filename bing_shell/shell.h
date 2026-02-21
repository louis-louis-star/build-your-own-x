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

/* 缓冲区大小定义 */
#define SHELL_RL_BUFSIZE 1024
#define SHELL_TOK_BUFSIZE 64
#define SHELL_TOK_DELIM " \t\r\n\a"

/* ===== readline.c ===== */
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

/* ===== execute.c ===== */
/**
 * 启动外部进程执行命令
 * @param args 参数数组
 * @return 1表示继续执行，0表示退出
 */
int shell_launch(char **args);

/**
 * 执行命令（内置命令或外部命令）
 * @param args 参数数组
 * @return 1表示继续执行，0表示退出
 */
int shell_execute(char **args);

/* ===== builtin.c ===== */
/**
 * 获取内置命令数量
 */
int shell_num_builtins(void);

/* 内置命令函数 */
int shell_cd(char **args);
int shell_help(char **args);
int shell_exit(char **args);

#endif /* SHELL_H */

