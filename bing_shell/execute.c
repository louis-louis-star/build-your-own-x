/**
 * execute.c - 命令执行模块
 * 
 * 功能：执行外部命令和内置命令的分发
 */

#include "shell.h"

/* 外部引用：内置命令表（定义在builtin.c） */
extern char *builtin_str[];
extern int (*builtin_func[])(char **);

/**
 * 启动外部进程执行命令
 * 使用fork()创建子进程，execvp()执行程序
 */
int shell_launch(char **args) {
    pid_t pid;
    int status;

    pid = fork();
    
    if (pid == 0) {
        /* 子进程：执行命令 */
        if (execvp(args[0], args) == -1) {
            perror("bing_shell");
        }
        exit(EXIT_FAILURE);
    } else if (pid < 0) {
        /* fork出错 */
        perror("bing_shell");
    } else {
        /* 父进程：等待子进程结束 */
        do {
            waitpid(pid, &status, WUNTRACED);
        } while (!WIFEXITED(status) && !WIFSIGNALED(status));
    }

    return 1;
}

/**
 * 执行命令
 * 先检查是否为内置命令，否则作为外部命令执行
 */
int shell_execute(char **args) {
    int i;

    /* 空命令直接返回 */
    if (args[0] == NULL) {
        return 1;
    }

    /* 检查是否为内置命令 */
    for (i = 0; i < shell_num_builtins(); i++) {
        if (strcmp(args[0], builtin_str[i]) == 0) {
            return (*builtin_func[i])(args);
        }
    }

    /* 作为外部命令执行 */
    return shell_launch(args);
}

