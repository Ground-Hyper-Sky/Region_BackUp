import json
import codecs
from typing import *


class Edit_Read:

    @classmethod
    def get_file_obj(cls, path: AnyStr, mode: AnyStr = "r", coding: AnyStr = "utf-8-sig"):
        try:
            fp = codecs.open(path, mode, encoding=coding)
            return fp

        except Exception as e:
            raise e

    @classmethod
    def get_json_object(cls, path, coding="utf-8-sig"):
        with codecs.open(path, "r", encoding=coding) as fp:
            return json.load(fp)

    @classmethod
    def new_json_file(cls, path, json_object, coding="utf-8-sig"):
        with codecs.open(path, "w", encoding=coding) as fp:
            json.dump(json_object, fp, ensure_ascii=False, indent=4)
            return True

    @classmethod
    def edit_element(cls, obj, keys=None, content=None, mode="edit"):
        if not isinstance(obj, (list, dict)):
            return None

        if isinstance(keys, (int, str)):
            keys = [keys]

        if isinstance(obj, list):
            if mode == "edit" and isinstance(keys[0], int) and -len(obj) <= keys[0] < len(obj):
                if len(keys) == 1:
                    obj[keys[0]] = content
                    return True
                return cls.edit_element(obj[keys[0]], keys[1:], content)

            elif mode in ["+", "-"]:
                if keys is None:
                    if mode == "+":
                        obj.append(content)
                        return True
                elif isinstance(keys[0], int) and -len(obj) <= keys[0] < len(obj):
                    if len(keys) == 1:
                        if mode == "+":
                            obj[keys[0]].append(content)
                        elif mode == "-":
                            obj.pop(keys[0])
                        return True
                    return cls.edit_element(obj[keys[0]], keys[1:], content, mode=mode)

            return None

        elif isinstance(obj, dict):
            if mode == "edit" and isinstance(keys[0], str) and keys[0] in obj:
                if len(keys) == 1:
                    obj[keys[0]] = content
                    return True
                return cls.edit_element(obj[keys[0]], keys[1:], content)

            elif mode == "s+" and len(keys) == 1 and isinstance(keys[0], str):
                obj[keys[0]] = content
                return True

            elif mode in ["+", "s-"]:
                if keys is not None:
                    if isinstance(keys[0], str) and len(keys) == 1:
                        if mode == "+":
                            if isinstance(obj[keys[0]], list):
                                obj[keys[0]].append(content)
                                return True

                            elif keys[0] not in obj[keys[0]]:
                                obj[keys[0]] = content
                                return True
                        elif mode == "s-" and keys[0] in obj:
                            obj.pop(keys[0])
                            return True
                    elif isinstance(keys[0], str) and keys[0] in obj:
                        return cls.edit_element(obj[keys[0]], keys[1:], content, mode=mode)

            elif mode == "-" and keys is not None:
                if isinstance(keys[0], str) and len(keys) == 1 and keys[0] in obj:
                    obj.pop(keys[0])
                    return True
                elif isinstance(keys[0], str) and keys[0] in obj:
                    return cls.edit_element(obj[keys[0]], keys[1:], mode=mode)

        return None

    @classmethod
    def edit_json_file(cls, path, loc, content, coding="utf-8-sig", mode="edit"):
        with codecs.open(path, "r+", encoding=coding) as fp:
            if not fp.read():
                return None
            fp.seek(0)
            file = json.load(fp)
            if cls.edit_element(file, loc, content, mode):
                fp.seek(0)
                fp.truncate()
                json.dump(file, fp, ensure_ascii=False, indent=4)
                return True

            return None
