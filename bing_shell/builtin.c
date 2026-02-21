/**
 * builtin.c - 内置命令模块
 * 
 * 功能：实现shell内置命令（cd, help, exit等）
 * 
 * 扩展指南：
 *   1. 在 builtin_str 数组中添加命令名
 *   2. 在 builtin_func 数组中添加对应的函数指针
 *   3. 实现新的命令函数
 */

#include "shell.h"

/* 内置命令字符串列表 */
char *builtin_str[] = {
    "cd",
    "help",
    "exit"
};

/* 内置命令函数指针列表 */
int (*builtin_func[])(char **) = {
    &shell_cd,
    &shell_help,
    &shell_exit
};

/**
 * 获取内置命令数量
 */
int shell_num_builtins(void) {
    return sizeof(builtin_str) / sizeof(char *);
}

/**
 * 内置命令：cd - 切换工作目录
 */
int shell_cd(char **args) {
    if (args[1] == NULL) {
        fprintf(stderr, "bing_shell: expected argument to \"cd\"\n");
    } else {
        if (chdir(args[1]) != 0) {
            perror("bing_shell");
        }
    }
    return 1;
}

/**
 * 内置命令：help - 显示帮助信息
 */
int shell_help(char **args) {
    int i;
    (void)args;  /* 未使用的参数 */

    printf("bing_shell - A simple Unix shell written in C\n");
    printf("\n");
    printf("Usage: type program names and arguments, then hit enter.\n");
    printf("\n");
    printf("Built-in commands:\n");
    for (i = 0; i < shell_num_builtins(); i++) {
        printf("  %-10s - ", builtin_str[i]);
        if (strcmp(builtin_str[i], "cd") == 0) {
            printf("change directory\n");
        } else if (strcmp(builtin_str[i], "help") == 0) {
            printf("show this help message\n");
        } else if (strcmp(builtin_str[i], "exit") == 0) {
            printf("exit the shell\n");
        }
    }
    printf("\n");
    printf("Use 'man <command>' for more information on external commands.\n");
    
    return 1;
}

/**
 * 内置命令：exit - 退出shell
 */
int shell_exit(char **args) {
    (void)args;  /* 未使用的参数 */
    return 0;
}

