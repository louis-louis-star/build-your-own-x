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
    int status;

    do {
        line = shell_read_line();
        if (!line) {
            /* EOF (Ctrl+D) */
            printf("\n");
            break;
        }

        /* 使用支持管道的执行函数 */
        status = shell_execute_line(line);

        free(line);
    } while (status);
}

/**
 * 程序入口
 */
int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    /* 初始化信号处理 */
    shell_init_signals();

    /* 初始化 readline */
    shell_readline_init();

    /* 运行主循环 */
    shell_loop();

    /* 清理资源 */
    shell_readline_cleanup();

    return EXIT_SUCCESS;
}

