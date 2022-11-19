#!/usr/python
#
# verify.py
# Author: Xu.Cao (steve curcy)
# Created at 2022-11-19 09:19
# Version: v0.1.1.221119_build_b0_Xu.C
# License under GPLv2.0 ("License")
#
import util

def verifyPlugins(plugins: dict) -> bool:
    allPlugNames = set()
    allSrcNames = set()
    for plugin in plugins:
        if "name" in plugin:
            if plugin["name"] in allPlugNames:
                util.printError("Duplicated module name: {}.".format(plugin["name"]))
                return False
            allPlugNames.add(plugin["name"])
        if "src" not in plugin:
            util.printError("Essential \"src\" file is lost.")
            return False
        if plugin["src"][-2:] != ".c":
            util.printWarn("\"{}\" is not a \".c\" file. Do you mean it?".format(plugin["src"]))
        if plugin["src"] in allSrcNames:
            util.printError("Duplicated module \"src\" file: {}.".format(plugin["src"]))
            return False
        allSrcNames.add(plugin["src"])
        if "methods" not in plugin:
            util.printError("Essential methods mappings are lost.")
            return False
        if "perf_event" not in plugin:
            util.printError("\"perf_event\" must be provided.")
            return False
        if "ctl" not in plugin:
            if "struct" not in plugin:
                util.printError("ctl or struct must be provided one at least.")
                return False
            util.printWarn("Default output handler will be used by default.")
    return True