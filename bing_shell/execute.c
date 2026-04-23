/**
 * execute.c - 命令执行模块
 *
 * 功能：执行外部命令和内置命令的分发，支持多管道、重定向、后台运行
 */

#include "shell.h"

/* 外部引用：内置命令表（定义在builtin.c） */
extern char *builtin_str[];
extern int (*builtin_func[])(char **);

/**
 * 设置重定向
 */
static void setup_redirection(Command *cmd) {
    /* 输入重定向 */
    if (cmd->input_file) {
        int fd = open(cmd->input_file, O_RDONLY);
        if (fd < 0) {
            perror("bing_shell: input redirect");
            exit(EXIT_FAILURE);
        }
        dup2(fd, STDIN_FILENO);
        close(fd);
    }

    /* 输出重定向 */
    if (cmd->output_file) {
        int flags = O_WRONLY | O_CREAT;
        flags |= cmd->append_output ? O_APPEND : O_TRUNC;
        int fd = open(cmd->output_file, flags, 0644);
        if (fd < 0) {
            perror("bing_shell: output redirect");
            exit(EXIT_FAILURE);
        }
        dup2(fd, STDOUT_FILENO);
        close(fd);
    }
}

/**
 * 执行多管道命令
 */
static int shell_launch_pipeline(CommandLine *cmdline) {
    int pipes[MAX_PIPES][2];
    pid_t pids[MAX_PIPES + 1];
    int i;
    int status;

    /* 创建所有管道 */
    for (i = 0; i < cmdline->cmd_count - 1; i++) {
        if (pipe(pipes[i]) == -1) {
            perror("bing_shell: pipe");
            return 1;
        }
    }

    /* 为每个命令创建子进程 */
    for (i = 0; i < cmdline->cmd_count; i++) {
        Command *cmd = &cmdline->commands[i];

        pids[i] = fork();

        if (pids[i] == 0) {
            /* 第一个命令：设置标准输入重定向 */
            if (i == 0 && cmd->input_file) {
                int fd = open(cmd->input_file, O_RDONLY);
                if (fd < 0) {
                    perror("bing_shell");
                    exit(EXIT_FAILURE);
                }
                dup2(fd, STDIN_FILENO);
                close(fd);
            }

            /* 最后一个命令：设置标准输出重定向 */
            if (i == cmdline->cmd_count - 1 && cmd->output_file) {
                int flags = O_WRONLY | O_CREAT;
                flags |= cmd->append_output ? O_APPEND : O_TRUNC;
                int fd = open(cmd->output_file, flags, 0644);
                if (fd < 0) {
                    perror("bing_shell");
                    exit(EXIT_FAILURE);
                }
                dup2(fd, STDOUT_FILENO);
                close(fd);
            }

            /* 非第一个命令：从上一个管道读 */
            if (i > 0) {
                dup2(pipes[i - 1][0], STDIN_FILENO);
            }

            /* 非最后一个命令：写入下一个管道 */
            if (i < cmdline->cmd_count - 1) {
                dup2(pipes[i][1], STDOUT_FILENO);
            }

            /* 关闭所有管道描述符 */
            int j;
            for (j = 0; j < cmdline->cmd_count - 1; j++) {
                close(pipes[j][0]);
                close(pipes[j][1]);
            }

            if (cmd->args[0] == NULL) {
                exit(EXIT_SUCCESS);
            }

            execvp(cmd->args[0], cmd->args);
            perror("bing_shell");
            exit(EXIT_FAILURE);
        }
    }

    /* 父进程关闭所有管道 */
    for (i = 0; i < cmdline->cmd_count - 1; i++) {
        close(pipes[i][0]);
        close(pipes[i][1]);
    }

    /* 等待所有子进程 */
    for (i = 0; i < cmdline->cmd_count; i++) {
        waitpid(pids[i], &status, 0);
    }

    return 1;
}

/**
 * 启动单个外部进程执行命令
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
 * 执行单个命令（带重定向和后台运行支持）
 * @param cmd 命令结构体
 * @param cmdline_str 原始命令行字符串（用于记录后台任务）
 */
static int shell_launch_command(Command *cmd, const char *cmdline_str) {
    pid_t pid;
    int status;

    if (cmd->args[0] == NULL) {
        return 1;
    }

    pid = fork();

    if (pid == 0) {
        setup_redirection(cmd);

        if (execvp(cmd->args[0], cmd->args) == -1) {
            perror("bing_shell");
        }
        exit(EXIT_FAILURE);
    } else if (pid < 0) {
        perror("bing_shell");
    } else {
        if (!cmd->background) {
            do {
                waitpid(pid, &status, WUNTRACED);
            } while (!WIFEXITED(status) && !WIFSIGNALED(status));
        } else {
            /* 后台任务：添加到任务列表 */
            shell_add_job(pid, cmdline_str ? cmdline_str : cmd->args[0]);
            printf("[%d]\n", pid);
        }
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
 * 执行命令
 */
int shell_execute(char **args) {
    if (args[0] == NULL) {
        return 1;
    }

    return shell_execute_single(args);
}

/**
 * 执行命令行（支持多管道、重定向、后台运行、别名）
 */
int shell_execute_line(char *line) {
    CommandLine *cmdline;
    int result;
    char *expanded_line = NULL;

    /* 更新后台任务状态 */
    shell_update_jobs();

    /* 检查并展开别名 */
    char *line_copy = strdup(line);
    char *first_word = strtok(line_copy, " \t");

    if (first_word) {
        char *alias_expanded = shell_expand_alias(first_word);
        if (alias_expanded) {
            /* 获取剩余参数 */
            char *rest = strtok(NULL, "");

            /* 构建展开后的命令行 */
            if (rest) {
                expanded_line = malloc(strlen(alias_expanded) + strlen(rest) + 2);
                sprintf(expanded_line, "%s %s", alias_expanded, rest);
            } else {
                expanded_line = strdup(alias_expanded);
            }

            free(line_copy);
            line = expanded_line;
        } else {
            free(line_copy);
            line_copy = strdup(line);
        }
    } else {
        free(line_copy);
    }

    cmdline = shell_parse_command_line(line);
    if (!cmdline || cmdline->cmd_count == 0) {
        if (expanded_line) free(expanded_line);
        return 1;
    }

    /* 单个命令 */
    if (cmdline->cmd_count == 1) {
        Command *cmd = &cmdline->commands[0];

        /* 检查内置命令 */
        int i;
        for (i = 0; i < shell_num_builtins(); i++) {
            if (cmd->args[0] && strcmp(cmd->args[0], builtin_str[i]) == 0) {
                result = (*builtin_func[i])(cmd->args);
                free_command_line(cmdline);
                if (expanded_line) free(expanded_line);
                return result;
            }
        }

        result = shell_launch_command(cmd, line);
    } else {
        /* 多管道命令 */
        result = shell_launch_pipeline(cmdline);
    }

    free_command_line(cmdline);
    if (expanded_line) free(expanded_line);
    return result;
}

