#!/usr/bin/python
# -*- coding: utf-8 -*-
#
import re
import os
import time
import util
import verify

perfEventTemplate = """
def print_{}(cpu, data, size):
    event = b["{}"].event(data)
    print("[cpu: %d], {}" % (cpu, {}))

"""


initDataTemplate = """
# init for {name}.
{name}_key = {key}
{name}_leaf = {leaf}
for i in range(len({name}_key)):
    cur_key = b[\"{name}\"].Key({keys})
    b[\"{name}\"][cur_key] = b[\"{name}\"].Leaf({leaves})

"""


#
# @brief generate the handlers of inserting datas into BPF_MAPs.
# @param initDatas - list of data infos
# @return str - handlers to insert datas
#
def getInitHandlers(initDatas: list) -> str:
    ret = ""
    for dataInfo in initDatas:
        keyLen, leafLen = 0, 0
        key, leaf = "[", "["
        keys, leaves = "", ""
        for i in range(len(dataInfo["key"])):
            if i == 0:
                key += "["
                leaf += "["
                keyLen = len(dataInfo["key"][i])
                leafLen = len(dataInfo["leaf"][i])
                for j in range(keyLen):
                    if j == 0:
                        keys += "{}_key[i][{}]".format(dataInfo["name"], j)
                    else:
                        keys += ",{}_key[i][{}]".format(dataInfo["name"], j)
                for j in range(leafLen):
                    if j == 0:
                        leaves += "{}_leaf[i][{}]".format(dataInfo["name"], j)
                    else:
                        leaves += ",{}_leaf[i][{}]".format(dataInfo["name"], j)
            else:
                key += ",["
                leaf += ",["
            for j in range(keyLen):
                if j == 0:
                    key += "{}".format(dataInfo["key"][i][j])  
                else:
                    key += ",{}".format(dataInfo["key"][i][j])
            for j in range(leafLen):
                if j == 0:
                    leaf += "{}".format(dataInfo["leaf"][i][j])
                else:
                    leaf += ",{}".format(dataInfo["leaf"][i][j])
            key += "]"
            leaf += "]"
        key += "]"
        leaf += "]"
    ret += initDataTemplate.format(name=dataInfo["name"], key=key, leaf=leaf, keys=keys, leaves=leaves)
    return ret


#
# @brief To return a handler in the ctl file, replace the method name if invalid.
# @param ctlPath - the "ctl" file's path
# @param event - "perf_event"'s name
# @return str - the handler in `str`
#
def getHandlerByCtl(ctlPath: str, event: str) -> str:
    ctl = util.safeRead(ctlPath)
    if not ctl:
        return None
    if len(re.findall(r"def [a-zA-Z_ ,]+\(", ctl)) != 1:
        util.printError("Only one perf_event handler is supported.")
        return None
    ctl = re.sub(r"def [a-zA-Z_ ,]+\(", "def print_{}(".format(event), ctl)
    return ctl + "\n"


#
# @brief To return a handler based on the specified struct
# @param src - src file's content
# @param structName - the name of specified struct in plugins.json
# @param event - "perf_event"'s name
# @return str - the handler in `str`
#
def getHandlerByStruct(src: str, structName: str, event: str) -> str:
    structRegion = re.search(r"struct\s+%s\s*{\s*([a-z0-9A-Z_ \[\]]+;\s*[/a-zA-Z _0-9]*\s+)+};" % structName, src, re.DOTALL)
    if structRegion is None:
        util.printError("struct {} is not found.".format(structName))
        return None
    var = re.findall(r"[ \t\n]+([a-zA-Z0-9_]+\s+[a-zA-Z0-9_]+)[a-zA-Z0-9_\[\]]*;", structRegion.group(), re.DOTALL)
    if not var or not len(var):
        return None
    ret = list()
    for item in var:
        ret.append(item.split())
    fmt, val, l = "", "", len(ret)
    for i in range(l):
        if ret[i][0] == "char":
            fmt += "[{}: %s]{}".format(ret[i][1], "" if i == l - 1 else ", ")
        else:
            fmt += "[{}: %d]{}".format(ret[i][1], "" if i == l - 1 else ", ")
        val += "event.{}{}".format(ret[i][1], "" if i == l - 1 else ", ")
    return perfEventTemplate.format(event, event, fmt, val)


#
# @brief to get the info of this plugin
# @param plugin - the plugin to load
# @return dict - infoes of this plugin
#
def loadPlugin(plugin: dict) -> dict:
    if plugin is None:
        return None
    util.printTip("Trying to load module {}.".format(plugin["name"] if "name" in plugin else plugin["src"]))

    ret = {"headers": None, "prog": None, "attach": "", "handler": None, "buffer": None, "init": None}
    src = util.safeRead("src/" + plugin["src"])
    if not src or not len(src):
        util.printError("Cannot get the content of {}, loaded failed.".format(plugin["src"]))
        return None
    headers = re.search(r"(#include[</.a-z \n]+>\s+)+", src, re.DOTALL)
    if headers:
        src = src[:headers.span()[0]] + src[headers.span()[1]:]
        headers = headers.group()
    else:
        headers = ""
    src = re.sub(r"\\", "\\\\\\\\", src)
    ret["headers"] = headers
    ret["prog"] = src
    for m in plugin["methods"]:
        if m["type"] == "kprobe":
            if "kprobe" in m:
                if m["kprobe"] == "raw":
                    ret["attach"] += "b.attach_{}(event=\"{}\", fn_name=\"{}\")\n".format(m["type"],
                                                                                        m["target"],
                                                                                        m["name"])
            else:
                ret["attach"] += "b.attach_{}(event=b.get_syscall_fnname(\"{}\"), fn_name=\"{}\")\n".format(m["type"],
                                                                                                    m["target"],
                                                                                                    m["name"])
        else:
            ret["attach"] += "b.attach_{}(name=\"c\", sym=\"{}\", fn_name=\"{}\")\n".format(m["type"],
                                                                                            m["target"],
                                                                                            m["name"])
        util.printOk("Attach the function \"{}\" to function \"{}\".".format(m["name"], m["target"]))
    if ret["attach"] == "":
        util.printWarn("No method of this module was attached, do you mean it?")
    if "ctl" in plugin:
        ret["handler"] = getHandlerByCtl("ctl/" + plugin["ctl"], plugin["perf_event"])
    else:
        ret["handler"] = getHandlerByStruct(src, plugin["struct"], plugin["perf_event"])
    if not ret["handler"]:
        util.printError("No perf_event handler was loaded!")
        return None
    ret["buffer"] = "b[\"{}\"].open_perf_buffer(print_{})\n".format(plugin["perf_event"], plugin["perf_event"])

    if "init_data" in plugin:
        ret["init"] = getInitHandlers(plugin["init_data"])
    else:
        ret["init"] = ""

    util.printOk("module \"{}\" loaded successfully.".format(plugin["name"] if "name" in plugin else plugin["src"]))
    return ret


#
# @brief generate the synthetic ebpf file and give it executive power.
#
def gen():
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

{init}

while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        exit(0)
    """

    startTime = time.perf_counter_ns()
    headers, progs, attaches, handlers, buffers, init = "", "", "", "", "", ""
    plugins = util.getJson("plugins.json")
    if not plugins:
        util.printError("\"plugins.json\" loaded failed.")
        exit(-1)
    if plugins is list:
        util.printError("\"plugin.json\" is in wrong format.")
        exit(-1)
    if not verify.verifyPlugins(plugins):
        util.printError("Validation failed: Invalid syntax checked in plugins.json.")
        exit(-1)
    util.printOk("Validation passed in {:.2f}s.".format((time.perf_counter_ns() - startTime) / 1e9))

    for p in plugins:
        plugin = loadPlugin(p)
        if not plugin:
            continue
        headers += plugin["headers"]
        progs += plugin["prog"] + "\n"
        attaches += plugin["attach"]
        handlers += plugin["handler"]
        buffers += plugin["buffer"]
        init += plugin["init"]

    
    if progs == "" or handlers == "":
        util.printError("No module was loaded.")
    if attaches == "":
        util.printWarn("No method attach to kernel functions, do you mean it?")

    if util.safeWrite("ebpf.py", prog.format(prog=headers + progs, attach=attaches, handler=handlers, buffer=buffers, init=init)):
        os.system("chmod u+x ebpf.py")
        util.printOk("ebpf.py has been generated in {:.2f}s.".format((time.perf_counter_ns() - startTime) / 1e9))
    else:
        util.printError("ebpf.py generated failed.")



if __name__ == "__main__":
    gen()
