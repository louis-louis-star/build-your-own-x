/**
 * parse.c - 命令行解析模块
 *
 * 功能：解析命令行，支持引号、变量展开、通配符、管道、重定向
 */

#include "shell.h"

/* 跳过空白字符 */
static char *skip_whitespace(char *str) {
    while (*str == ' ' || *str == '\t') str++;
    return str;
}

/* 展开变量 $VAR 和 $? */
char *shell_expand_variables(const char *str) {
    static char result[4096];
    char *out = result;
    const char *p = str;

    while (*p && (out - result) < (int)sizeof(result) - 1) {
        if (*p == '$') {
            p++;
            if (*p == '?') {
                out += sprintf(out, "%d", last_exit_status);
                p++;
            } else if (*p == '{') {
                p++;
                char varname[256];
                int i = 0;
                while (*p && *p != '}' && i < 255) varname[i++] = *p++;
                varname[i] = '\0';
                if (*p == '}') p++;
                char *val = shell_getenv(varname);
                if (val) out += sprintf(out, "%s", val);
            } else if (isalnum(*p) || *p == '_') {
                char varname[256];
                int i = 0;
                while ((isalnum(*p) || *p == '_') && i < 255) varname[i++] = *p++;
                varname[i] = '\0';
                char *val = shell_getenv(varname);
                if (val) out += sprintf(out, "%s", val);
            } else {
                *out++ = '$';
            }
        } else {
            *out++ = *p++;
        }
    }
    *out = '\0';
    return result;
}

/* 通配符展开 */
char **shell_expand_wildcards(char **args, int *argc) {
    if (!args || !argc) return args;

    char **new_args = malloc(SHELL_TOK_BUFSIZE * sizeof(char *));
    int new_argc = 0;

    for (int i = 0; args[i] && new_argc < SHELL_TOK_BUFSIZE - 1; i++) {
        if (strchr(args[i], '*') || strchr(args[i], '?') || strchr(args[i], '[')) {
            glob_t globbuf;
            if (glob(args[i], GLOB_NOCHECK | GLOB_TILDE, NULL, &globbuf) == 0) {
                for (size_t j = 0; j < globbuf.gl_pathc && new_argc < SHELL_TOK_BUFSIZE - 1; j++) {
                    new_args[new_argc++] = strdup(globbuf.gl_pathv[j]);
                }
                globfree(&globbuf);
            } else {
                new_args[new_argc++] = strdup(args[i]);
            }
        } else {
            new_args[new_argc++] = strdup(args[i]);
        }
        free(args[i]);
    }
    new_args[new_argc] = NULL;
    free(args);
    *argc = new_argc;
    return new_args;
}

/**
 * 解析带引号的参数
 * 从字符串中提取一个参数，正确处理引号
 * 返回: 下一个参数的起始位置，NULL 表示结束
 */
static char *parse_quoted_arg(char *str, char **arg_out) {
    char *p = str;
    char quote = 0;
    char *result;
    int result_len = 0;
    int result_size = 256;

    /* 跳过前导空白 */
    while (*p == ' ' || *p == '\t') p++;

    if (*p == '\0') {
        *arg_out = NULL;
        return NULL;
    }

    result = malloc(result_size);

    /* 解析参数 */
    while (*p != '\0') {
        /* 检查引号 */
        if ((*p == '"' || *p == '\'') && quote == 0) {
            quote = *p;
            p++;
            continue;
        }

        /* 检查引号结束 */
        if (quote != 0 && *p == quote) {
            quote = 0;
            p++;
            continue;
        }

        /* 如果不在引号内，检查分隔符 */
        if (quote == 0) {
            if (*p == ' ' || *p == '\t' || *p == ';') {
                break;
            }
            /* 检查特殊字符 */
            if (*p == '<' || *p == '>' || *p == '|' || *p == '&') {
                /* 如果已经有内容，停止；否则单独返回这个字符 */
                if (result_len > 0) break;
                result[result_len++] = *p++;
                break;
            }
        }

        /* 添加字符到结果 */
        if (result_len >= result_size - 1) {
            result_size *= 2;
            result = realloc(result, result_size);
        }
        result[result_len++] = *p++;
    }

    result[result_len] = '\0';
    *arg_out = result;

    /* 跳过尾部空白 */
    while (*p == ' ' || *p == '\t') p++;

    return p;
}

/**
 * 解析单个命令（处理重定向和引号）
 */
static int parse_single_command(char *cmd_str, Command *cmd) {
    int bufsize = SHELL_TOK_BUFSIZE;
    int argc = 0;
    char *p = cmd_str;
    char *arg;

    cmd->args = malloc(bufsize * sizeof(char *));
    cmd->input_file = NULL;
    cmd->output_file = NULL;
    cmd->append_output = false;
    cmd->background = false;

    if (!cmd->args) {
        return -1;
    }

    while (*p != '\0') {
        /* 跳过空白 */
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '\0') break;

        /* 输入重定向 */
        if (strcmp(p, "<") == 0 || strncmp(p, "< ", 2) == 0) {
            p++; /* 跳过 < */
            while (*p == ' ' || *p == '\t') p++;
            p = parse_quoted_arg(p, &arg);
            if (arg) {
                cmd->input_file = arg;
            }
        }
        /* 输出重定向（追加） */
        else if (strncmp(p, ">>", 2) == 0) {
            p += 2; /* 跳过 >> */
            while (*p == ' ' || *p == '\t') p++;
            p = parse_quoted_arg(p, &arg);
            if (arg) {
                cmd->output_file = arg;
                cmd->append_output = true;
            }
        }
        /* 输出重定向（覆盖） */
        else if (*p == '>') {
            p++; /* 跳过 > */
            while (*p == ' ' || *p == '\t') p++;
            p = parse_quoted_arg(p, &arg);
            if (arg) {
                cmd->output_file = arg;
                cmd->append_output = false;
            }
        }
        /* 后台运行 - 单独的 & */
        else if (*p == '&' && (*(p+1) == '\0' || *(p+1) == ' ' || *(p+1) == '\t')) {
            cmd->background = true;
            p++;
        }
        /* 普通参数 */
        else {
            p = parse_quoted_arg(p, &arg);
            if (arg) {
                cmd->args[argc++] = arg;

                if (argc >= bufsize) {
                    bufsize += SHELL_TOK_BUFSIZE;
                    cmd->args = realloc(cmd->args, bufsize * sizeof(char *));
                }
            }
        }
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

