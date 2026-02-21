/**
 * readline.c - 读取用户输入模块
 * 
 * 功能：从标准输入读取一行命令
 */

#include "shell.h"

/**
 * 读取一行用户输入
 * 支持动态扩展缓冲区
 */
char *shell_read_line(void) {
    int bufsize = SHELL_RL_BUFSIZE;
    int position = 0;
    char *buffer = malloc(sizeof(char) * bufsize);
    int c;

    if (!buffer) {
        fprintf(stderr, "bing_shell: allocation error\n");
        exit(EXIT_FAILURE);
    }

    while (1) {
        c = getchar();

        /* 遇到EOF或换行符则结束 */
        if (c == EOF || c == '\n') {
            buffer[position] = '\0';
            return buffer;
        } else {
            buffer[position] = c;
        }
        position++;

        /* 缓冲区不足时动态扩展 */
        if (position >= bufsize) {
            bufsize += SHELL_RL_BUFSIZE;
            buffer = realloc(buffer, bufsize);
            if (!buffer) {
                fprintf(stderr, "bing_shell: allocation error\n");
                exit(EXIT_FAILURE);
            }
        }
    }
}

