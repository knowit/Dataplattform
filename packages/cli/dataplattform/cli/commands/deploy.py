from argparse import ArgumentParser, Namespace
import os
import yaml
import copy
import subprocess

targets = dict()
ignore = [
    'node_modules',
    '.serverless',
    'tests',
    'dist',
    'templates'
]

install_commands = dict({
    'requirements.txt': 'pip install -r requirements.txt',
    'package.json': 'npm install',
    'yarn.lock': 'yarn install --frozen-lockfile'
})


class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
    def ignore_unknown(self, node):
        return None


SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown)


def parse_yaml(path: str) -> dict:
    try:
        return yaml.load(open(path), Loader=SafeLoaderIgnoreUnknown)
    except Exception as e:
        print("Failed to parse yaml file: " + path + "\n" + str(e))


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


def contains_path(path_list: list, path: str) -> bool:
    i = 0
    while i < len(path_list):
        item = path_list[i]
        exists = False
        try:
            exists = os.path.samefile(item, path)
        except OSError as e:
            print(e)
        finally:
            if exists:
                return True
            else:
                i += 1
    return False


def remove_path(path_list: list, path: str):
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


def search(target: str):
    for entry in os.scandir(target):
        if entry.is_file():
            if entry.name == 'serverless.yml' or entry.name == 'serverless.yaml':
                if not contains_path(list(targets), target):
                    targets[target] = resolve_dependencies(target, entry.path)
        elif entry.name not in ignore:
            search(entry.path)


def inverse_path(path: str) -> str:
    return os.path.relpath(os.path.curdir, path)


def get_deployment_commands(path: str) -> list:
    commands = ['cd ' + path]
    for file in os.listdir(path):
        if file in install_commands.keys():
            commands.append(install_commands[file])
    commands.append('sls deploy --aws-profile sandbox')
    commands.append('cd ' + inverse_path(path))
    return commands


def get_remove_commands(path: str) -> list:
    return ['cd ' + path, 'sls remove --aws-profile sandbox', 'cd ' + inverse_path(path)]


def run_commands(commands: list, error_message: str):
    try:
        retcode = subprocess.call(' && '.join(commands), shell=True)
        if retcode is not 0:
            raise Exception(error_message)
    except OSError as e:
        print("OSError: " + e)


def print_status(status: str):
    message = "\nDataplattform: " + status
    line = '\n' + ''.join(['-'*(len(message)-1)])
    print("\n" + line + message + line)


def deploy(paths):
    print_status("Starting deployment")
    success = True
    for path in paths:
        print("\n\nDeploying service: " + path)
        try:
            run_commands(get_deployment_commands(path), "An error occured when deploying service: " + path)
        except Exception as e:
            print("\n\n" + str(e))
            success = False
            break

    print_status("Deployment complete" if success else "Deployment stopped")


def remove(paths):
    print_status("Starting removal")
    success = True
    for path in paths:
        print("\n\nRemoving service: " + path)
        try:
            run_commands(get_remove_commands(path), "An error occured when removing service: " + path)
        except Exception as e:
            print("\n\n" + str(e))
            success = False
            break

    print_status("Removal complete" if success else "Removal stopped")


def init(parser: ArgumentParser):
    parser.add_argument('-s', '--services', default='.', type=str, nargs='*')
    parser.add_argument('-e', '--stage', default='dev', choices=['dev', 'test', 'prod'])
    parser.add_argument('-c', '--config-file', default=None, dest='config_file')
    parser.add_argument('-r', '--remove', default=False, action='store_true')


def run(args: Namespace, _):

    # TODO: Configure SSM-parameters

    for target in args.services:
        search(target)

    paths = topological_sort(targets)

    if args.remove:
        paths.reverse()
        remove(paths)
    else:
        deploy(paths)

    # TODO: Register all Glue tables

    # TODO: Update Glue tables
