/**
 * main.c - 主程序入口
 *
 * 功能：shell主循环和初始化
 */

#include "shell.h"

/**
 * 显示欢迎信息
 */
static void shell_welcome(void) {
    printf("\n");
    printf("%s========================================%s\n", COLOR_CYAN, COLOR_RESET);
    printf("%s   Welcome to %sbing_shell%s!%s\n", COLOR_CYAN, COLOR_GREEN, COLOR_CYAN, COLOR_RESET);
    printf("%s   A professional Unix shell in C%s\n", COLOR_CYAN, COLOR_RESET);
    printf("%s========================================%s\n", COLOR_CYAN, COLOR_RESET);
    printf("\n");
    printf("Features:\n");
    printf("  - Pipes: cmd1 | cmd2 | cmd3\n");
    printf("  - Redirects: <, >, >>\n");
    printf("  - Background: cmd &\n");
    printf("  - Variables: $VAR, $?\n");
    printf("  - Wildcards: *, ?, [...]\n");
    printf("  - Job control: jobs, fg, bg, Ctrl+Z\n");
    printf("\n");
    printf("Type 'help' for more information.\n");
    printf("\n");
}

/**
 * shell主循环
 */
void shell_loop(void) {
    char *line;
    int status;

    do {
        line = shell_read_line();
        if (!line) {
            printf("\n");
            break;
        }

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

    /* 初始化环境变量 */
    shell_init_env();

    /* 初始化信号处理 */
    shell_init_signals();

    /* 初始化 readline */
    shell_readline_init();

    /* 加载配置文件 */
    shell_load_config();

    /* 显示欢迎信息 */
    shell_welcome();

    /* 运行主循环 */
    shell_loop();

    /* 清理资源 */
    shell_readline_cleanup();

    printf("Goodbye!\n");
    return EXIT_SUCCESS;
}

