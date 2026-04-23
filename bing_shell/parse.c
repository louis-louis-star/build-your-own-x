/**
 * parse.c - 命令行解析模块
 *
 * 功能：将命令行字符串解析为参数数组
 */

#include "shell.h"

/**
 * 解析命令行字符串为参数数组
 * 使用空格、制表符等作为分隔符
 */
char **shell_split_line(char *line) {
    int bufsize = SHELL_TOK_BUFSIZE;
    int position = 0;
    char **tokens = malloc(bufsize * sizeof(char *));
    char *token;

    if (!tokens) {
        fprintf(stderr, "bing_shell: allocation error\n");
        exit(EXIT_FAILURE);
    }

    token = strtok(line, SHELL_TOK_DELIM);
    while (token != NULL) {
        tokens[position] = token;
        position++;

        if (position >= bufsize) {
            bufsize += SHELL_TOK_BUFSIZE;
            tokens = realloc(tokens, bufsize * sizeof(char *));
            if (!tokens) {
                fprintf(stderr, "bing_shell: allocation error\n");
                exit(EXIT_FAILURE);
            }
        }

        token = strtok(NULL, SHELL_TOK_DELIM);
    }

    tokens[position] = NULL;
    return tokens;
}

/**
 * 检查命令行是否包含管道
 * @param line 命令行
 * @return 管道位置指针，无管道返回NULL
 */
char *find_pipe(char *line) {
    return strchr(line, '|');
}

/**
 * 解析管道命令
 * 将 "ls | grep txt" 解析为两个命令
 * @param line 完整命令行
 * @param cmd1 第一条命令（输出）
 * @param cmd2 第二条命令（输入）
 */
void split_pipe_command(char *line, char **cmd1, char **cmd2) {
    char *pipe_pos = find_pipe(line);

    if (!pipe_pos) {
        *cmd1 = NULL;
        *cmd2 = NULL;
        return;
    }

    /* 分割命令 */
    *pipe_pos = '\0';
    *cmd1 = line;
    *cmd2 = pipe_pos + 1;

    /* 去除前导空格 */
    while (**cmd2 == ' ' || **cmd2 == '\t') {
        (*cmd2)++;
    }

    /* 去除cmd1尾部空格 */
    char *end = *cmd1 + strlen(*cmd1) - 1;
    while (end > *cmd1 && (*end == ' ' || *end == '\t')) {
        *end = '\0';
        end--;
    }
}

