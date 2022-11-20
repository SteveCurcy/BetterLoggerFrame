#!/usr/python
#
import os
import util

def verifyPlugins(plugins: dict) -> bool:
    # record if there are duplicated module names or source files.
    allPlugNames = set()
    allSrcNames = set()
    allTarNames = set()
    for plugin in plugins:
        # check module names
        if "name" in plugin:
            if plugin["name"] in allPlugNames:
                util.printError("Duplicated module name: {}.".format(plugin["name"]))
                return False
            allPlugNames.add(plugin["name"])

        # check if src file exists or is a file
        if "src" not in plugin:
            util.printError("Essential \"src\" file is lost.")
            return False
        if not os.path.exists("src/" + plugin["src"]):
            util.printError("src/{} not exists.".format(plugin["src"]))
            return False
        if not os.path.isfile("src/" + plugin["src"]):
            util.printError("src/{} is not a file.".format(plugin["src"]))
            return False

        # check the type of src file
        if plugin["src"][-2:] != ".c":
            util.printWarn("\"{}\" is not a \".c\" file. Do you mean it?".format(plugin["src"]))
        if plugin["src"] in allSrcNames:
            util.printError("Duplicated module \"src\" file: {}.".format(plugin["src"]))
            return False
        allSrcNames.add(plugin["src"])

        # check methods infoes
        if "methods" not in plugin:
            util.printError("Essential methods mappings are lost.")
            return False
        for m in plugin["methods"]:
            if "type" not in m or "name" not in m or "target" not in m:
                util.printError("\"methods\" need be specified all of \"type\" (kprobe/uprobe), \"name\" (your ebpf function) and \"target\" (attach which one).")
                return False
            if m["type"] != "kprobe" and m["type"] != "uprobe":
                util.printError("Methods' type can only be assigned as \"kprobe\" or \"uprobe\".")
                return False
            if m["target"] in allTarNames:
                util.printWarn("\"{}\" has been attached more than once. Trying to integrate the functions of modules to clear the modules's structure will be better.".format(m["target"]))
            else:
                allTarNames.add(m["target"])

        if "perf_event" not in plugin:
            util.printError("\"perf_event\" must be provided.")
            return False
        
        # check the controller file
        if "ctl" not in plugin:
            if "struct" not in plugin:
                util.printError("ctl or struct must be provided one at least.")
                return False
            util.printTip("Default output handler will be used by default.")
        else:
            if not os.path.exists("ctl/" + plugin["ctl"]):
                util.printError("ctl/{} not exists.".format(plugin["ctl"]))
                if "struct" in plugin:
                    util.printWarn("Default handler will be generated because of broken \"ctl\" file.")
                    del plugin["ctl"]
                else:
                    return False
            if "ctl" in plugin and not os.path.isfile("ctl/" + plugin["ctl"]):
                util.printError("ctl/{} is not a file.".format(plugin["ctl"]))
                if "struct" in plugin:
                    util.printWarn("Default handler will be generated because of broken \"ctl\" file.")
                    del plugin["ctl"]
                else:
                    return False
    return True