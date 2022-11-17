#!/usr/bin/python
#
import re
import os
import json
import util

perfEventTemplate = """
def print_{}(cpu, data, size):
    event = b["{}"].event(data)
    print("[cpu: %d], {}" % (cpu, {}))
"""


def getStructure(src: str, structName: str) -> list:
    structRegion = re.search(r"struct\s+%s\s*{\s*([a-z0-9A-Z_ \[\]]+;\s+)+};" % structName, src, re.DOTALL)
    if structRegion is None:
        util.printError("struct {} is not found.".format(structName))
        return None
    var = re.findall(r"[ \t\n]+([a-zA-Z0-9_]+\s+[a-zA-Z0-9_]+)[a-zA-Z0-9_\[\]]*;", structRegion.group(), re.DOTALL)
    if var is None or not len(var):
        return None
    ret = list()
    for item in var:
        ret.append(item.split())
    return ret


def loadPlugin(plugin: dict) -> dict:
    if plugin is None:
        return None
    ret = {"headers": "", "prog": None, "attach": "", "handler": None, "buffer": None}
    src = util.safeRead("src/" + plugin["src"])
    headers = re.search(r"(#include[</.a-z \n]+>\s+)+", src, re.DOTALL)
    if headers:
        src = src[:headers.span()[0]] + src[headers.span()[1]:]
        headers = headers.group()
    struct = getStructure(src, plugin["struct"])
    fmt, val, l = "", "", len(struct)
    for i in range(l):
        if struct[i][0] == "char":
            fmt += "[{}: %s]{}".format(struct[i][1], "" if i == l - 1 else ", ")
        else:
            fmt += "[{}: %d]{}".format(struct[i][1], "" if i == l - 1 else ", ")
        val += "event.{}{}".format(struct[i][1], "" if i == l - 1 else ", ")
    ret["headers"] = headers
    ret["prog"] = src
    for m in plugin["methods"]:
        ret["attach"] += "b.attach_{}(event=b.get_syscall_fnname(\"{}\"), fn_name=\"{}\")\n".format(m["type"],
                                                                                                    m["target"],
                                                                                                    m["name"])
        util.printOk("Attach to function {} to kernel function sys_{}.".format(m["name"], m["target"]))
    ret["handler"] = perfEventTemplate.format(plugin["perf_event"], plugin["perf_event"], fmt, val)
    ret["buffer"] = "b[\"{}\"].open_perf_buffer(print_{})".format(plugin["perf_event"], plugin["perf_event"])

    util.printOk("{} loaded successfully.".format(plugin["name"] if "name" in plugin else plugin["src"]))
    return ret


if __name__ == "__main__":
    print("-------- generating eBPF python program --------")
    prog = """#!/usr/bin/python
from bcc import BPF
from bcc.utils import printb

prog = \"\"\"{prog}\"\"\"

b = BPF(text=prog)
{attach}

print("Bpf program loaded. Ctrl + C to stop...")

{handler}

{buffer}

while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        exit(0)
    """
    headers, progs, attaches, handlers, buffers = "", "", "", "", ""
    plugins = util.getJson("plugins.json")
    if plugins is None:
        exit(-1)
    for p in plugins:
        plugin = loadPlugin(p)
        headers += plugin["headers"]
        progs += plugin["prog"] + "\n\n"
        attaches += plugin["attach"]
        handlers += plugin["handler"]
        buffers += plugin["buffer"]
    # print(prog.format(prog=headers + progs, attach=attaches, handler=handlers, buffer=buffers))
    if util.safeWrite("ebpf.py", prog.format(prog=headers + progs, attach=attaches, handler=handlers, buffer=buffers)):
        os.system("chmod u+x ebpf.py")
        util.printOk("ebpf.py has been generated.")
    else:
        util.printError("ebpf.py generated failed.")
