/**
 * jobs.c - 后台任务管理模块
 *
 * 功能：管理后台运行的任务，支持fg/bg切换
 */

#include "shell.h"

/* 全局变量定义 */
Job jobs[MAX_JOBS];
int job_count = 0;
pid_t current_foreground_pid = -1;
int last_exit_status = 0;

/**
 * 添加后台任务
 */
int shell_add_job(pid_t pid, const char *cmd) {
    if (job_count >= MAX_JOBS) {
        fprintf(stderr, "bing_shell: too many jobs\n");
        return -1;
    }

    int job_id = 1;
    for (int i = 0; i < job_count; i++) {
        if (jobs[i].job_id >= job_id) {
            job_id = jobs[i].job_id + 1;
        }
    }

    jobs[job_count].pid = pid;
    jobs[job_count].job_id = job_id;
    jobs[job_count].state = JOB_RUNNING;
    jobs[job_count].active = 1;
    strncpy(jobs[job_count].command, cmd, sizeof(jobs[job_count].command) - 1);
    job_count++;

    return job_id;
}

/**
 * 移除后台任务
 */
void shell_remove_job(pid_t pid) {
    for (int i = 0; i < job_count; i++) {
        if (jobs[i].pid == pid && jobs[i].active) {
            jobs[i].active = 0;
            break;
        }
    }
}

/**
 * 更新后台任务状态
 */
void shell_update_jobs(void) {
    int status;
    pid_t result;

    for (int i = 0; i < job_count; i++) {
        if (jobs[i].active && jobs[i].state != JOB_STOPPED) {
            result = waitpid(jobs[i].pid, &status, WNOHANG | WUNTRACED | WCONTINUED);

            if (result > 0) {
                if (WIFEXITED(status) || WIFSIGNALED(status)) {
                    jobs[i].state = JOB_DONE;
                    jobs[i].active = 0;
                    printf("[%d]  Done                    %s\n", jobs[i].job_id, jobs[i].command);
                } else if (WIFSTOPPED(status)) {
                    jobs[i].state = JOB_STOPPED;
                    printf("[%d]  Stopped                 %s\n", jobs[i].job_id, jobs[i].command);
                }
            }
        }
    }
}

/**
 * 通过任务ID查找任务
 */
int shell_find_job_by_id(int job_id) {
    for (int i = 0; i < job_count; i++) {
        if (jobs[i].active && jobs[i].job_id == job_id) {
            return i;
        }
    }
    return -1;
}

/**
 * 停止任务（Ctrl+Z）
 */
void shell_stop_job(pid_t pid) {
    for (int i = 0; i < job_count; i++) {
        if (jobs[i].pid == pid && jobs[i].active) {
            jobs[i].state = JOB_STOPPED;
            printf("\n[%d]  Stopped                 %s\n", jobs[i].job_id, jobs[i].command);
            break;
        }
    }
}

/**
 * 继续任务
 */
void shell_continue_job(pid_t pid, int foreground) {
    for (int i = 0; i < job_count; i++) {
        if (jobs[i].pid == pid && jobs[i].active) {
            jobs[i].state = JOB_RUNNING;
            kill(pid, SIGCONT);

            if (foreground) {
                current_foreground_pid = pid;
                printf("%s\n", jobs[i].command);

                int status;
                waitpid(pid, &status, WUNTRACED);
                current_foreground_pid = -1;

                if (WIFSTOPPED(status)) {
                    shell_stop_job(pid);
                } else {
                    last_exit_status = WEXITSTATUS(status);
                    shell_remove_job(pid);
                }
            }
            break;
        }
    }
}

