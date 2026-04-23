/**
 * signal.c - 信号处理模块
 *
 * 功能：处理 Ctrl+C (SIGINT), Ctrl+Z (SIGTSTP) 等信号
 */

#include "shell.h"
#include <signal.h>
#include <readline/readline.h>

/* 设置当前前台进程 */
void shell_set_foreground(pid_t pid) {
    current_foreground_pid = pid;
}

/* SIGINT (Ctrl+C) 处理函数 */
static void sigint_handler(int sig) {
    (void)sig;

    if (current_foreground_pid > 0) {
        /* 有前台进程运行，发送信号给它 */
        kill(current_foreground_pid, SIGINT);
    } else {
        /* 无前台进程，显示新行并重新显示提示符 */
        printf("\n");
        rl_on_new_line();
        rl_replace_line("", 0);
        rl_redisplay();
    }
}

/* SIGTSTP (Ctrl+Z) 处理函数 */
static void sigtstp_handler(int sig) {
    (void)sig;

    if (current_foreground_pid > 0) {
        /* 停止前台进程 */
        kill(current_foreground_pid, SIGTSTP);
        /* 任务状态会在 waitpid 返回后处理 */
    }
}

/**
 * 初始化信号处理
 */
void shell_init_signals(void) {
    struct sigaction sa;

    /* Ctrl+C */
    sa.sa_handler = sigint_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    sigaction(SIGINT, &sa, NULL);

    /* Ctrl+Z */
    sa.sa_handler = sigtstp_handler;
    sigaction(SIGTSTP, &sa, NULL);

    /* 忽略 SIGQUIT (Ctrl+\) */
    signal(SIGQUIT, SIG_IGN);
}

