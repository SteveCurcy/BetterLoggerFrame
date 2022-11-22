#!/usr/python
#
import os
import util


#
# @brief check plugins' validity.
# @param plugins - plugins in json
# @return bool - if the plugins are valid
#
def verifyPlugins(plugins: list) -> bool:
    # record if there are duplicated module names or source files.
    allPlugNames = set()
    allSrcNames = set()
    allTarNames = set()
    for plugin in plugins:
        if plugin is not dict:
            util.printError("A plugin must be in `dict`")
            return False

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
        if plugin["methods"] is not list:
            util.printError("\"methods\" item must be a list.")
            return False
        for m in plugin["methods"]:
            if m is not dict:
                util.printError("Every method in \"methods\" must be a `dict`")
                return False
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
        
        # check the init_data item
        if "init_data" in plugin:
            if plugin["init_data"] is not list:
                util.printError("\"init_data\" must be a `list`")
                return False
            for item in plugin["init_data"]:
                if item is not dict:
                    util.printError("Every item of \"init_data\" must be a `dict`")
                    return False
                if "name" not in item:
                    util.printError("Name is essential in init_data.")
                    return False
                if "key" not in item and "leaf" not in item:
                    util.printError("Key and leaf is needed at least one.")
                    return False
                hasKey, hasLeaf = "key" in item, "leaf" in item
                if hasKey and item["key"] is not list:
                    util.printError("\"key\" of item in \"init_data\" must be a list")
                    return False
                if hasLeaf and item["leaf"] is not list:
                    util.printError("\"leaf\" of item in \"init_data\" must be a list")
                    return False
                if hasKey and hasLeaf and len(item["key"]) != len(item["leaf"]):
                    util.printError("The number of keys and leaves must be equal.")
                    return False
                if not hasKey:
                    util.printWarn("Key will be stuffed as 1 for {} by default.".format(item["name"]))
                    item["key"] = list()
                    for i in item["leaf"]:
                        item["key"].append([1])
                elif not hasLeaf:
                    util.printWarn("Leaf will be stuffed as 1 for {} by default.".format(item["name"]))
                    item["leaf"] = list()
                    for i in item["key"]:
                        item["leaf"].append([1])
                if hasKey and len(item["key"]) == 0:
                    util.printWarn("No key and leaf was provided, do you mean it?")
                    plugin["init_data"].remove(item)
                    continue
                keyLen, leafLen = len(item["key"][0]), len(item["leaf"][0])
                for i in range(1, len(item["key"])):
                    if item["key"][i] is not list or item["leaf"][i] is not list:
                        util.printError("keys and leaves must be list.")
                        return False
                    if len(item["key"][i]) != keyLen:
                        util.printError("Every key must have same number of fields.")
                        return False
                    if len(item["leaf"][i]) != leafLen:
                        util.printError("Every leaf must have same number of fields.")
                        return False
    return True