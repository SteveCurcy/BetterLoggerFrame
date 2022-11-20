/*
 * shell.c
 * Author: Xu.Cao (steve curcy)
 * Created at 2022-11-20 08:44
 * Version: v0.2.1.221120_build_b0_Xu.C
 * License under GPLv2.0 ("License")
 */

struct command_t {
    u32 pid;
    char cmd[32];   // the command user input in shell
    char arg0[32];
    char arg1[32];
    char arg2[32];
    char arg3[32];
    char arg4[32];
};
BPF_PERF_OUTPUT(commands);

/**
 * @brief This method will be attached to kernel function {@code execve}.
 * 
 * @param ctx - context of the program
 * @param filename - executive file to exert
 * @param argv - command arguments
 * @param envp - envirenmental parameters
 * @return int - no meaning, return 0 commonly
 */
int shell_execve(struct pt_regs *ctx, const char *filename, 
                char* const *argv, char* const *envp) {
    struct command_t command = {};
    command.pid = bpf_get_current_pid_tgid();
    bpf_probe_read_user_str(&command.cmd, 32, argv[0]);
    if (bpf_probe_read_user_str(&command.arg0, 32, argv[1]) >= 0)
    if (bpf_probe_read_user_str(&command.arg1, 32, argv[2]) >= 0)
    if (bpf_probe_read_user_str(&command.arg2, 32, argv[3]) >= 0)
    if (bpf_probe_read_user_str(&command.arg3, 32, argv[4]) >= 0)
    bpf_probe_read_user_str(&command.arg4, 32, argv[5]);
    commands.perf_submit(ctx, &command, sizeof(command));
    return 0;
}