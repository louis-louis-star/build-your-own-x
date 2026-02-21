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

        /* 缓冲区不足时动态扩展 */
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

