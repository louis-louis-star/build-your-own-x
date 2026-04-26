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
 * 使用 readline 库，支持方向键、历史记录、多行续行
 */
char *shell_read_line(void) {
    char prompt[256];
    char *line;
    char *full_line = NULL;
    size_t full_len = 0;
    int continue_input = 0;

    do {
        /* 如果是续行，使用 > 提示符 */
        if (continue_input) {
            line = readline("> ");
        } else {
            shell_get_prompt(prompt, sizeof(prompt));
            line = readline(prompt);
        }

        if (!line) {
            /* EOF (Ctrl+D) */
            if (full_line) {
                free(full_line);
            }
            return NULL;
        }

        /* 检查是否以 \ 结尾（续行） */
        size_t line_len = strlen(line);
        if (line_len > 0 && line[line_len - 1] == '\\') {
            /* 移除末尾的 \，继续读取下一行 */
            line[line_len - 1] = '\0';
            continue_input = 1;

            /* 追加到 full_line */
            char *new_full = realloc(full_line, full_len + line_len + 1);
            if (!new_full) {
                free(line);
                if (full_line) free(full_line);
                return NULL;
            }
            full_line = new_full;
            strcpy(full_line + full_len, line);
            full_len += line_len;

            free(line);
        } else {
            /* 行结束，合并所有内容 */
            continue_input = 0;

            if (full_line) {
                char *new_full = realloc(full_line, full_len + line_len + 1);
                if (!new_full) {
                    free(line);
                    free(full_line);
                    return NULL;
                }
                full_line = new_full;
                strcpy(full_line + full_len, line);
                full_len += line_len;
                free(line);
            } else {
                full_line = strdup(line);
                free(line);
            }
        }
    } while (continue_input);

    /* 添加到历史记录（非空行） */
    if (full_line && *full_line) {
        add_history(full_line);
    }

    return full_line;
}

