#include <uapi/linux/ptrace.h>
#include <linux/fs.h>
#include <linux/sched.h>
#include <linux/dcache.h>

// DNAME_INLINE_LEN = 32

struct file_info_t {
    u32 i_ino;
};
BPF_HASH(file_info, struct file_info_t, u8);

struct file_t {
    u32 uid;
    char filename[DNAME_INLINE_LEN];
};
BPF_PERF_OUTPUT(files);

int trace_file_open(struct pt_regs *ctx, struct inode *inode,
    struct file *file) {
    struct file_t data = {};
    data.uid = (u32)bpf_get_current_uid_gid();
    bpf_probe_read_kernel(&data.filename, sizeof(data.filename), (void *)file->f_path.dentry->d_name.name);
    struct file_info_t info = {};
    info.i_ino = inode->i_ino;
    if (file_info.lookup(&info) != 0)
        files.perf_submit(ctx, &data, sizeof(data));
    return 0;
}