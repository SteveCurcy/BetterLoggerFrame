import re
import json


def printError(values: str) -> None:
    print("\033[1;31m[Error]\033[0m " + values)


def printOk(values: str) -> None:
    print("\033[1;32m[Ok]\033[0m " + values)


def printWarn(values: str) -> None:
    print("\033[1;33m[Warning]\033[0m " + values)


def printTip(values: str) -> None:
    print("[Tip] " + values)


def getJson(path: str) -> dict:
    try:
        tmp_file = open(path, "r")
        plugins = json.load(tmp_file)
        tmp_file.close()
        return plugins
    except:
        printError("\"{}\" opened failed.".format(path))
        return None


def safeRead(path: str) -> str:
    try:
        tmp_file = open(path, "r")
        ret = tmp_file.read()
        tmp_file.close()
        return ret
    except:
        printError("\"{}\" opened failed.".format(path))
        return None


def safeWrite(path: str, values: str) -> bool:
    try:
        tmp_file = open(path, "w")
        tmp_file.write(values)
        tmp_file.close()
        return True
    except:
        printError("\"{}\" opened failed.".format(path))
        return False
