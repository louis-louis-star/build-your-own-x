/**
 * builtin.c - 内置命令模块
 *
 * 功能：实现shell内置命令
 */

#include "shell.h"
#include <readline/history.h>

/* 内置命令列表 */
char *builtin_str[] = {
    "cd", "help", "exit", "history", "jobs", "fg", "bg", "export", "unset"
};

int (*builtin_func[])(char **) = {
    &shell_cd, &shell_help, &shell_exit, &shell_history,
    &shell_jobs, &shell_fg, &shell_bg, &shell_export, &shell_unset
};

/* 别名定义 */
static struct { char *alias; char *command; } aliases[] = {
    {"ll", "ls -alF"}, {"la", "ls -A"}, {"l", "ls -CF"}, {NULL, NULL}
};

char *shell_expand_alias(const char *cmd) {
    for (int i = 0; aliases[i].alias; i++) {
        if (strcmp(cmd, aliases[i].alias) == 0) return aliases[i].command;
    }
    return NULL;
}

int shell_num_builtins(void) { return sizeof(builtin_str) / sizeof(char *); }

int shell_cd(char **args) {
    char *path = args[1] ? shell_expand_tilde(args[1]) : getenv("HOME");
    if (!path) { fprintf(stderr, "bing_shell: HOME not set\n"); return 1; }
    if (chdir(path) != 0) perror("bing_shell");
    return 1;
}

int shell_help(char **args) {
    (void)args;
    printf("%sbing_shell%s - A Unix shell written in C\n\n", COLOR_CYAN, COLOR_RESET);
    printf("Built-in commands:\n");
    printf("  cd [dir]     - change directory (~ supported)\n");
    printf("  help         - show this help\n");
    printf("  exit         - exit shell\n");
    printf("  history      - show command history\n");
    printf("  jobs         - list background jobs\n");
    printf("  fg [%%job]    - bring job to foreground\n");
    printf("  bg [%%job]    - continue job in background\n");
    printf("  export VAR=val - set environment variable\n");
    printf("  unset VAR    - remove environment variable\n");
    printf("\nFeatures:\n");
    printf("  Pipes: cmd1 | cmd2 | cmd3\n");
    printf("  Redirects: <, >, >>\n");
    printf("  Background: cmd &\n");
    printf("  Wildcards: *, ?, [...]\n");
    printf("  Variables: $VAR, $?\n");
    printf("  Ctrl+Z: stop foreground job\n");
    return 1;
}

int shell_history(char **args) {
    (void)args;
    HIST_ENTRY **list = history_list();
    if (list) for (int i = 0; list[i]; i++) printf("%5d  %s\n", i + 1, list[i]->line);
    return 1;
}

int shell_exit(char **args) { (void)args; return 0; }

int shell_jobs(char **args) {
    (void)args;
    shell_update_jobs();
    int count = 0;
    for (int i = 0; i < job_count; i++) {
        if (jobs[i].active) {
            count++;
            const char *state_str = jobs[i].state == JOB_RUNNING ? "Running" : "Stopped";
            printf("[%d]  %-20s  %s\n", jobs[i].job_id, state_str, jobs[i].command);
        }
    }
    if (count == 0) printf("No background jobs.\n");
    return 1;
}

int shell_fg(char **args) {
    int job_id = 1;
    if (args[1]) {
        if (args[1][0] == '%') job_id = atoi(args[1] + 1);
        else job_id = atoi(args[1]);
    }

    int idx = shell_find_job_by_id(job_id);
    if (idx < 0) { fprintf(stderr, "fg: job %d not found\n", job_id); return 1; }

    printf("%s\n", jobs[idx].command);
    shell_continue_job(jobs[idx].pid, 1);
    return 1;
}

int shell_bg(char **args) {
    int job_id = 1;
    if (args[1]) {
        if (args[1][0] == '%') job_id = atoi(args[1] + 1);
        else job_id = atoi(args[1]);
    }

    int idx = shell_find_job_by_id(job_id);
    if (idx < 0) { fprintf(stderr, "bg: job %d not found\n", job_id); return 1; }

    shell_continue_job(jobs[idx].pid, 0);
    printf("[%d]  %s &\n", jobs[idx].job_id, jobs[idx].command);
    return 1;
}

int shell_export(char **args) {
    if (!args[1]) { fprintf(stderr, "export: usage: export VAR=value\n"); return 1; }

    char *eq = strchr(args[1], '=');
    if (!eq) { fprintf(stderr, "export: invalid format\n"); return 1; }

    *eq = '\0';
    char *name = args[1];
    char *value = eq + 1;

    if (shell_setenv(name, value) != 0) {
        perror("export");
        return 1;
    }
    return 0;  /* 成功返回 0 */
}

int shell_unset(char **args) {
    if (!args[1]) { fprintf(stderr, "unset: usage: unset VAR\n"); return 1; }
    shell_unsetenv(args[1]);
    return 1;
}

