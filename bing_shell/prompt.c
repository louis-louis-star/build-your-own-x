/**
 * prompt.c - 提示符生成模块
 * 
 * 功能：生成类似 "user@hostname:/path$" 格式的提示符
 */

#include "shell.h"

/**
 * 生成提示符字符串
 * 格式: user@hostname:current_dir$
 */
void shell_get_prompt(char *buf, int size) {
    char hostname[256];
    char cwd[PATH_MAX];
    char *username;
    char *home;
    int offset;
    
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
        /* 替换家目录为 ~ */
        offset = strlen(home);
        snprintf(buf, size, "%s@%s:~%s$ ", username, hostname, cwd + offset);
    } else {
        snprintf(buf, size, "%s@%s:%s$ ", username, hostname, cwd);
    }
}

