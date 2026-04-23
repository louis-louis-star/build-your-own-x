/**
 * prompt.c - 提示符生成模块
 *
 * 功能：生成带颜色的提示符
 */

#include "shell.h"

/**
 * 生成带颜色的提示符字符串
 * 格式: user@hostname:current_dir$
 * 颜色: 绿色用户名@蓝色主机名:黄色目录$
 */
void shell_get_prompt(char *buf, int size) {
    char hostname[256];
    char cwd[PATH_MAX];
    char *username;
    char *home;
    char *dir_display;

    /* 获取用户名 */
    username = getenv("USER");
    if (!username) {
        struct passwd *pw = getpwuid(getuid());
        username = pw ? pw->pw_name : "unknown";
    }

    /* 获取主机名 */
    if (gethostname(hostname, sizeof(hostname)) != 0) {
        strcpy(hostname, "localhost");
    }

    /* 获取当前工作目录 */
    if (getcwd(cwd, sizeof(cwd)) == NULL) {
        strcpy(cwd, "?");
    }

    /* 将家目录替换为 ~ */
    home = getenv("HOME");
    if (home && strncmp(cwd, home, strlen(home)) == 0) {
        static char cwd_display[PATH_MAX];
        snprintf(cwd_display, sizeof(cwd_display), "~%s", cwd + strlen(home));
        dir_display = cwd_display;
    } else {
        dir_display = cwd;
    }

    /* 生成带颜色的提示符 */
    /* 绿色用户名@蓝色主机名:黄色目录$ 重置颜色 */
    snprintf(buf, size, "%s%s%s@%s%s%s:%s%s%s$ %s",
             COLOR_GREEN, username, COLOR_RESET,
             COLOR_BLUE, hostname, COLOR_RESET,
             COLOR_YELLOW, dir_display, COLOR_RESET,
             COLOR_RESET);
}

