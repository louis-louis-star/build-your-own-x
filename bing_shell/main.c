/**
 * main.c - 主程序入口
 * 
 * 功能：shell主循环和初始化
 */

#include "shell.h"

/**
 * shell主循环
 * 读取命令 -> 解析 -> 执行 -> 重复
 */
void shell_loop(void) {
    char *line;
    char **args;
    int status;

    do {
        printf("bing_shell> ");
        line = shell_read_line();
        args = shell_split_line(line);
        status = shell_execute(args);

        free(line);
        free(args);
    } while (status);
}

/**
 * 程序入口
 */
int main(int argc, char **argv) {
    (void)argc;  /* 未使用的参数 */
    (void)argv;  /* 未使用的参数 */

    /* 运行主循环 */
    shell_loop();

    return EXIT_SUCCESS;
}

