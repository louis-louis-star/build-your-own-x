/**
 * readline.c - 读取用户输入模块
 *
 * 功能：使用 readline 库读取命令，支持历史记录和自动补全
 */

#include "shell.h"
#include <readline/readline.h>
#include <readline/history.h>

/* 内置命令列表（用于Tab补全） */
extern char *builtin_str[];
extern int shell_num_builtins(void);

/**
 * Tab补全生成函数
 */
char *command_generator(const char *text, int state) {
    static int list_index, len;
    char *name;

    if (!state) {
        list_index = 0;
        len = strlen(text);
    }

    while (list_index < shell_num_builtins()) {
        name = builtin_str[list_index++];
        if (strncmp(name, text, len) == 0) {
            return strdup(name);
        }
    }

    return NULL;
}

/**
 * Tab补全匹配函数
 */
char **shell_completion(const char *text, int start, int end) {
    (void)end;
    /* 只在命令开头进行补全 */
    if (start == 0) {
        return rl_completion_matches(text, command_generator);
    }
    return NULL;
}

/**
 * 初始化 readline
 */
void shell_readline_init(void) {
    /* 启用Tab补全 */
    rl_attempted_completion_function = shell_completion;

    /* 读取历史记录文件 */
    char *home = getenv("HOME");
    if (home) {
        char hist_path[PATH_MAX];
        snprintf(hist_path, sizeof(hist_path), "%s/%s", home, HISTORY_FILE);
        read_history(hist_path);
    }
}

/**
 * 清理 readline 资源
 */
void shell_readline_cleanup(void) {
    char *home = getenv("HOME");
    if (home) {
        char hist_path[PATH_MAX];
        snprintf(hist_path, sizeof(hist_path), "%s/%s", home, HISTORY_FILE);
        write_history(hist_path);
    }
}

/**
 * 读取一行用户输入
 * 使用 readline 库，支持方向键、历史记录等
 */
char *shell_read_line(void) {
    char prompt[256];
    char *line;

    shell_get_prompt(prompt, sizeof(prompt));
    line = readline(prompt);

    /* 添加到历史记录（非空行） */
    if (line && *line) {
        add_history(line);
    }

    return line;
}

