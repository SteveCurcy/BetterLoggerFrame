def printData(cpu, data, size):
    event = b["events"].event(data)
    print("[cpu: %d], [pid: %d], [ts: %d], [comm: %s]" % (cpu, event.pid, event.ts, event.comm))