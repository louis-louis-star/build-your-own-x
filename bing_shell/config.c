/**
 * config.c - 配置文件模块
 * 
 * 功能：加载 .bingshellrc 配置文件
 */

#include "shell.h"
#include <readline/history.h>

/**
 * 加载配置文件
 */
void shell_load_config(void) {
    char config_path[PATH_MAX];
    char *home = getenv("HOME");
    
    if (!home) return;
    
    snprintf(config_path, sizeof(config_path), "%s/%s", home, CONFIG_FILE);
    
    FILE *fp = fopen(config_path, "r");
    if (!fp) return;  /* 配置文件不存在是正常的 */
    
    char line[1024];
    while (fgets(line, sizeof(line), fp)) {
        /* 跳过注释和空行 */
        if (line[0] == '#' || line[0] == '\n') continue;
        
        /* 去除换行符 */
        line[strcspn(line, "\n")] = '\0';
        
        /* 执行配置命令 */
        if (strlen(line) > 0) {
            shell_execute_line(line);
        }
    }
    
    fclose(fp);
}

