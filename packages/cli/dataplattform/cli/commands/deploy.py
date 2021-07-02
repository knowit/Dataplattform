from argparse import ArgumentParser, Namespace
import os
import yaml
import copy

targets = dict()
ignore = [
    'node_modules',
    '.serverless',
    'tests',
    'dist',
    'templates'
]


class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
    def ignore_unknown(self, node):
        return None


SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown)


def parse_yaml(path: str) -> dict:
    try:
        return yaml.load(open(path), Loader=SafeLoaderIgnoreUnknown)
    except Exception as e:
        print("Failed to parse yaml file: " + path + "\n" + str(e))


def init(parser: ArgumentParser):
    parser.add_argument('-s', '--service', default='.', dest='target')
    parser.add_argument('-e', '--stage', default='dev', choices=['dev', 'test', 'prod'])
    parser.add_argument('-c', '--config-file', default=None, dest='config_file')


def resolve_dependencies(path: str, filename: str):
    config = parse_yaml(filename)
    if 'dataplattform' in config.keys() and 'dependencies' in config['dataplattform'].keys():
        result = []
        abspath = os.path.abspath(path)
        for relpath in config['dataplattform']['dependencies']:
            result.append(os.path.relpath(os.path.join(abspath, relpath), os.curdir))
        return result

    else:
        return []


def search(target: str):
    for entry in os.scandir(target):
        if entry.is_file():
            if (entry.name == 'serverless.yml' or entry.name == 'serverless.yaml') and entry.path not in targets:
                targets[target] = resolve_dependencies(target, entry.path)
        elif entry.name not in ignore:
            search(entry.path)


def contains_path(path_list: list, path: str) -> bool:
    for item in path_list:
        if os.path.samefile(item, path):
            return True
    return False


def remove_path(path_list: list, path: str) -> bool:
    i = 0
    while i < len(path_list):
        item = path_list[i]
        if os.path.samefile(item, path):
            path_list.remove(item)
            return
        else:
            i += 1
    raise IndexError('Path list does not include element: ' + path + "\n" + str(path_list))


def topological_sort(source: dict) -> list:
    a = copy.deepcopy(source)
    keys_list = list(a)

    for path in keys_list:
        deps = a[path]
        rem = []
        for dep in deps:
            if not contains_path(keys_list, dep) and dep not in rem:
                rem.append(dep)
        for dep in rem:
            deps.remove(dep)

    keys_list.sort(key=lambda j: len(a[j]))

    result = []
    i = 0
    while i < len(keys_list):
        key = keys_list[i]
        if len(a[key]) == 0:
            i = 0
            result.append(key)
            keys_list.remove(key)
            a.pop(key)

            for k in keys_list:
                if contains_path(a[k], key):
                    remove_path(a[k], key)
            if len(keys_list) == 0:
                return result
        else:
            i += 1
    raise Exception('Dataplattform dependency graph has a cycle:\n' + str(keys_list))


def run(args: Namespace, _):
    search(args.target)

    for path in topological_sort(targets):
        print(path)
