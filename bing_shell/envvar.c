/**
 * envvar.c - 环境变量管理模块
 * 
 * 功能：管理shell环境变量
 */

#include "shell.h"

/* 导出环境变量 */
int shell_setenv(const char *name, const char *value) {
    if (!name || !value) return -1;
    return setenv(name, value, 1);
}

/* 删除环境变量 */
int shell_unsetenv(const char *name) {
    if (!name) return -1;
    return unsetenv(name);
}

/* 获取环境变量 */
char *shell_getenv(const char *name) {
    return getenv(name);
}

/* 初始化环境变量 */
void shell_init_env(void) {
    /* 设置shell相关环境变量 */
    char cwd[PATH_MAX];
    if (getcwd(cwd, sizeof(cwd))) {
        setenv("PWD", cwd, 1);
    }
    
    char *shell = getenv("_");
    if (!shell) {
        setenv("SHELL", "/bin/bing_shell", 0);
    }
}

