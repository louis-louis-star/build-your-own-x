/**
 * parse.c - 命令行解析模块
 *
 * 功能：解析命令行，支持多管道、重定向、后台运行
 */

#include "shell.h"

/**
 * 跳过空白字符
 */
static char *skip_whitespace(char *str) {
    while (*str == ' ' || *str == '\t') {
        str++;
    }
    return str;
}

/**
 * 解析单个命令（处理重定向）
 */
static int parse_single_command(char *cmd_str, Command *cmd) {
    int bufsize = SHELL_TOK_BUFSIZE;
    int argc = 0;
    char *token;
    char *saveptr;

    cmd->args = malloc(bufsize * sizeof(char *));
    cmd->input_file = NULL;
    cmd->output_file = NULL;
    cmd->append_output = false;
    cmd->background = false;

    if (!cmd->args) {
        return -1;
    }

    token = strtok_r(cmd_str, " \t", &saveptr);
    while (token != NULL) {
        /* 输入重定向 */
        if (strcmp(token, "<") == 0) {
            token = strtok_r(NULL, " \t", &saveptr);
            if (token) {
                cmd->input_file = strdup(token);
            }
        }
        /* 输出重定向（覆盖） */
        else if (strcmp(token, ">") == 0) {
            token = strtok_r(NULL, " \t", &saveptr);
            if (token) {
                cmd->output_file = strdup(token);
                cmd->append_output = false;
            }
        }
        /* 输出重定向（追加） */
        else if (strcmp(token, ">>") == 0) {
            token = strtok_r(NULL, " \t", &saveptr);
            if (token) {
                cmd->output_file = strdup(token);
                cmd->append_output = true;
            }
        }
        /* 后台运行 */
        else if (strcmp(token, "&") == 0) {
            cmd->background = true;
        }
        /* 普通参数 */
        else {
            cmd->args[argc++] = strdup(token);

            if (argc >= bufsize) {
                bufsize += SHELL_TOK_BUFSIZE;
                cmd->args = realloc(cmd->args, bufsize * sizeof(char *));
            }
        }

        token = strtok_r(NULL, " \t", &saveptr);
    }

    cmd->args[argc] = NULL;
    cmd->argc = argc;

    return argc;
}

/**
 * 解析完整命令行
 */
CommandLine *shell_parse_command_line(char *line) {
    CommandLine *cmdline;
    char *line_copy;
    char *token;
    char *saveptr;
    int cmd_count = 0;

    cmdline = malloc(sizeof(CommandLine));
    if (!cmdline) {
        return NULL;
    }

    cmdline->commands = malloc((MAX_PIPES + 1) * sizeof(Command));
    cmdline->cmd_count = 0;
    cmdline->has_pipe = false;

    line_copy = strdup(line);

    /* 按管道分割 */
    token = strtok_r(line_copy, "|", &saveptr);
    while (token != NULL && cmd_count < MAX_PIPES + 1) {
        token = skip_whitespace(token);

        if (*token != '\0') {
            char *cmd_copy = strdup(token);
            parse_single_command(cmd_copy, &cmdline->commands[cmd_count]);
            free(cmd_copy);
            cmd_count++;
        }

        token = strtok_r(NULL, "|", &saveptr);
    }

    if (cmd_count > 1) {
        cmdline->has_pipe = true;
    }

    cmdline->cmd_count = cmd_count;
    free(line_copy);

    return cmdline;
}

/**
 * 释放命令行结构体
 */
void free_command_line(CommandLine *cmdline) {
    int i, j;

    if (!cmdline) return;

    for (i = 0; i < cmdline->cmd_count; i++) {
        if (cmdline->commands[i].args) {
            for (j = 0; j < cmdline->commands[i].argc; j++) {
                free(cmdline->commands[i].args[j]);
            }
            free(cmdline->commands[i].args);
        }
        free(cmdline->commands[i].input_file);
        free(cmdline->commands[i].output_file);
    }

    free(cmdline->commands);
    free(cmdline);
}

/**
 * 解析命令行字符串为参数数组（简化版本）
 */
char **shell_split_line(char *line) {
    int bufsize = SHELL_TOK_BUFSIZE;
    int position = 0;
    char **tokens = malloc(bufsize * sizeof(char *));
    char *token;

    if (!tokens) {
        return NULL;
    }

    token = strtok(line, SHELL_TOK_DELIM);
    while (token != NULL) {
        tokens[position++] = strdup(token);

        if (position >= bufsize) {
            bufsize += SHELL_TOK_BUFSIZE;
            tokens = realloc(tokens, bufsize * sizeof(char *));
        }

        token = strtok(NULL, SHELL_TOK_DELIM);
    }

    tokens[position] = NULL;
    return tokens;
}

/**
 * 展开路径中的 ~ 为家目录
 */
char *shell_expand_tilde(const char *path) {
    static char expanded[PATH_MAX];

    if (path && path[0] == '~') {
        char *home = getenv("HOME");
        if (home) {
            if (path[1] == '\0') {
                return strdup(home);
            } else {
                snprintf(expanded, sizeof(expanded), "%s%s", home, path + 1);
                return strdup(expanded);
            }
        }
    }

    return path ? strdup(path) : NULL;
}

