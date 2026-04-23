/**
 * execute.c - 命令执行模块
 *
 * 功能：执行外部命令和内置命令的分发，支持管道
 */

#include "shell.h"

/* 外部引用：内置命令表（定义在builtin.c） */
extern char *builtin_str[];
extern int (*builtin_func[])(char **);

/**
 * 执行管道命令
 * 支持 command1 | command2 格式
 */
int shell_launch_pipe(char **args1, char **args2) {
    int pipefd[2];
    pid_t pid1, pid2;
    int status;

    /* 创建管道 */
    if (pipe(pipefd) == -1) {
        perror("bing_shell: pipe");
        return 1;
    }

    /* 第一个子进程（写端） */
    pid1 = fork();
    if (pid1 == 0) {
        /* 重定向标准输出到管道写端 */
        dup2(pipefd[1], STDOUT_FILENO);
        close(pipefd[0]);
        close(pipefd[1]);

        if (execvp(args1[0], args1) == -1) {
            perror("bing_shell");
        }
        exit(EXIT_FAILURE);
    }

    /* 第二个子进程（读端） */
    pid2 = fork();
    if (pid2 == 0) {
        /* 重定向标准输入到管道读端 */
        dup2(pipefd[0], STDIN_FILENO);
        close(pipefd[1]);
        close(pipefd[0]);

        if (execvp(args2[0], args2) == -1) {
            perror("bing_shell");
        }
        exit(EXIT_FAILURE);
    }

    /* 父进程关闭管道并等待 */
    close(pipefd[0]);
    close(pipefd[1]);

    waitpid(pid1, &status, 0);
    waitpid(pid2, &status, 0);

    return 1;
}

/**
 * 启动外部进程执行命令
 * 使用fork()创建子进程，execvp()执行程序
 */
int shell_launch(char **args) {
    pid_t pid;
    int status;

    pid = fork();

    if (pid == 0) {
        if (execvp(args[0], args) == -1) {
            perror("bing_shell");
        }
        exit(EXIT_FAILURE);
    } else if (pid < 0) {
        perror("bing_shell");
    } else {
        do {
            waitpid(pid, &status, WUNTRACED);
        } while (!WIFEXITED(status) && !WIFSIGNALED(status));
    }

    return 1;
}

/**
 * 执行单条命令（检查内置命令）
 */
int shell_execute_single(char **args) {
    int i;

    if (args[0] == NULL) {
        return 1;
    }

    for (i = 0; i < shell_num_builtins(); i++) {
        if (strcmp(args[0], builtin_str[i]) == 0) {
            return (*builtin_func[i])(args);
        }
    }

    return shell_launch(args);
}

/**
 * 执行命令（支持管道）
 */
int shell_execute(char **args) {
    char *line_copy;
    char *cmd1, *cmd2;
    char **args1, **args2;
    static char last_line[1024] = "";
    static char **last_args = NULL;

    if (args[0] == NULL) {
        return 1;
    }

    /* 保存原始命令行用于管道检测 */
    /* 这里用一个简化的方法：检查是否有管道符号 */

    return shell_execute_single(args);
}

/**
 * 执行包含管道的命令行
 * @param line 原始命令行
 */
int shell_execute_line(char *line) {
    char *line_copy;
    char *cmd1, *cmd2;
    char **args;

    /* 检查是否有管道 */
    if (find_pipe(line)) {
        line_copy = strdup(line);
        split_pipe_command(line_copy, &cmd1, &cmd2);

        if (cmd1 && cmd2) {
            args = shell_split_line(strdup(cmd1));
            char **args1 = args;
            char **args2 = shell_split_line(strdup(cmd2));

            shell_launch_pipe(args1, args2);

            free(args1);
            free(args2);
            free(line_copy);
            return 1;
        }
        free(line_copy);
    }

    /* 无管道，普通执行 */
    args = shell_split_line(line);
    int result = shell_execute_single(args);
    free(args);
    return result;
}

