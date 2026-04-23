/**
 * builtin.c - 内置命令模块
 *
 * 功能：实现shell内置命令（cd, help, exit, history等）
 */

#include "shell.h"
#include <readline/history.h>

/* 内置命令字符串列表 */
char *builtin_str[] = {
    "cd",
    "help",
    "exit",
    "history"
};

/* 内置命令函数指针列表 */
int (*builtin_func[])(char **) = {
    &shell_cd,
    &shell_help,
    &shell_exit,
    &shell_history
};

/**
 * 获取内置命令数量
 */
int shell_num_builtins(void) {
    return sizeof(builtin_str) / sizeof(char *);
}

/**
 * 内置命令：cd - 切换工作目录
 * 支持 ~ 展开
 */
int shell_cd(char **args) {
    char *path;

    if (args[1] == NULL) {
        path = getenv("HOME");
        if (!path) {
            fprintf(stderr, "bing_shell: HOME not set\n");
            return 1;
        }
    } else {
        path = shell_expand_tilde(args[1]);
    }

    if (chdir(path) != 0) {
        perror("bing_shell");
    }

    return 1;
}

/**
 * 内置命令：help - 显示帮助信息
 */
int shell_help(char **args) {
    int i;
    (void)args;

    printf("bing_shell - A simple Unix shell written in C\n\n");
    printf("Built-in commands:\n");
    for (i = 0; i < shell_num_builtins(); i++) {
        printf("  %-10s ", builtin_str[i]);
        if (strcmp(builtin_str[i], "cd") == 0) {
            printf("- change directory (supports ~)\n");
        } else if (strcmp(builtin_str[i], "help") == 0) {
            printf("- show this help message\n");
        } else if (strcmp(builtin_str[i], "exit") == 0) {
            printf("- exit the shell\n");
        } else if (strcmp(builtin_str[i], "history") == 0) {
            printf("- show command history\n");
        }
    }
    printf("\nFeatures:\n");
    printf("  - Tab completion for built-in commands\n");
    printf("  - Arrow keys for history navigation\n");
    printf("  - Ctrl+L to clear screen\n");
    printf("  - ~ expansion in paths\n");

    return 1;
}

/**
 * 内置命令：history - 显示命令历史
 */
int shell_history(char **args) {
    HIST_ENTRY **list;
    int i;
    (void)args;

    list = history_list();
    if (list) {
        for (i = 0; list[i]; i++) {
            printf("%5d  %s\n", i + 1, list[i]->line);
        }
    }

    return 1;
}

/**
 * 内置命令：exit - 退出shell
 */
int shell_exit(char **args) {
    (void)args;
    return 0;
}

