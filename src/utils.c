#define DNAME_LEN 32

int ebpf_strcmp_dname(const char* dst, const char* src) {
    for (int i = 0; i < DNAME_LEN; i++) {
        if (dst[i] != src[i]) return -1;
    }
    return 0;
}