from datetime import datetime
from datetime import timedelta
from functools import lru_cache
from functools import wraps
import os
from typing import Any
from typing import Dict
from typing import List

import git
from tick import constants
import yaml


base_path = os.path.join(os.path.dirname(__file__))


def filter_key(key: str) -> str:
    """Filter the provided task key by lowering and remove task number.

    :param str key: Task Key
    """
    return constants.RE_KEY.findall(key.lower())[0]


def is_correct_repo(branch, path: str = "./"):
    try:
        repo = git.Repo(path)
        _ = repo.git_dir
        if repo.active_branch.name == branch:
            return True
    except git.exc.InvalidGitRepositoryError:
        return False


def resolve(attribute: str, key: str) -> str:
    """Resolves any custom rules for attribute or key.

    If no default or value is provided it will return the filtered key.

    :param str attribute: Rule attribute (e.g. project, repo...)
    :param str key: Task Key
    """
    rules = get_config("rules").get(attribute)
    filtered_key = filter_key(key)
    return rules.get(filtered_key, rules.get("default", filtered_key))


def get_config(key: str = None, keys: list = None) -> dict or None:
    """Retrieves local configuration for specific key.

    :param str key: Config key
    :param list keys: Config keys to be used with deep_get
    """
    with open(f"{base_path}/config.yaml", "r") as yaml_data:
        data = yaml.load(yaml_data, Loader=yaml.Loader)
    if key:
        return data.get(key, None)
    if keys:
        return deep_get(data, keys)


def save_config(key: str, data: dict = None) -> None:
    """Saves local configuration for specific key.

    :param str key: Config key
    :param dict data: Data to save to config
    """
    with open(f"{base_path}/config.yaml", "r+") as file:
        content = yaml.safe_load(file)
        content.update({key: data})
        file.seek(0)
        yaml.dump(content, file)
        file.truncate()


def deep_get(json_data: Dict, keys_list: List[Any], header: str = None):
    """Method for extracting value from the JSON dict with nested dicts.

    The important thing is that since key_list is a list (which is mutable) inside this method
    copy of key_list is created not to modify the initial key_list value.

    :param list keys_list: the list containing the path to the value (nested dicts).
        A wildcard constants.GET_ALL can be used to get all elements.
    :param dict json_data: dict of JSON data.
    :param str header: Final key to return the data with.
    :return: value.
    """
    keys_list = keys_list.copy()

    if json_data is None:
        return {}
    elif not keys_list:
        if header:
            return {header: json_data}
        return json_data

    key = keys_list.pop(0)

    if key == "GET_ALL":
        result = []

        for item in json_data.values() if isinstance(json_data, dict) else json_data:
            element = deep_get(item, keys_list, header)

            if element is not None:
                result.extend(element) if isinstance(element, list) else result.append(element)

        return result

    elif isinstance(key, str):
        try:
            return deep_get(json_data.get(key, None), keys_list, header)
        except AttributeError:
            return None

    elif isinstance(key, int):
        try:
            return deep_get(json_data[key], keys_list, header)
        except (IndexError, KeyError):
            return None

    else:
        raise ValueError("Unsupported key: {0}".format(key))


def map_deep_get(json_data: Dict | List[Dict], list_of_keys: List[List[str]], headers: List[str] = None) -> List | Dict:
    """This function allows us to use a list of keys to retrieve multiple sets of data.

    If headers are provided, the data will be packaged in dictionary with the headers
    matching the order. For json_data that is a list, the data will be mapped as well,
    extracting the list of keys for each dictionary in the list.

    :param dict or List[dict] json_data: dict of JSON data or a list of dicts.
    :param List[List[str]] list_of_keys: the list containing the path to the value (nested dicts).
        A wildcard constants.GET_ALL can be used to get all elements.
    :param List[str] headers: list of strings t
    :return: value
    """
    if isinstance(json_data, list):
        result = []
        for json in json_data:
            result.append(map_deep_get(json, list_of_keys, headers))
        return result
    elif isinstance(json_data, dict):
        if headers:
            data = [deep_get(json_data, keys, header) for keys, header in zip(list_of_keys, headers)]
            return {k: v for d in data for k, v in d.items()}
        else:
            return [deep_get(json_data, keys) for keys in list_of_keys]
    else:
        raise ValueError("Unsupported dat: {0}".format(json_data))


def timed_lru_cache(seconds: int, maxsize: int = 128):
    """Wraps lru cache and provides decorator with timed caching.

    :param int seconds: Seconds until refresh
    :param int maxsize: Max Size of cache
    """

    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.utcnow() + func.lifetime

            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache
