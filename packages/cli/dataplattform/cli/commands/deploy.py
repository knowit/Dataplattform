import copy
import os
import subprocess
import traceback
from argparse import ArgumentParser, Namespace
from ..helper import safe_parse_yaml

targets = dict()
config_files = dict()
access_levels = []

# Do not search these directories for serverless.yml files
ignore = [
    'node_modules',
    '.serverless',
    'tests',
    'dist',
    'templates'
]

# Pre-deployment commands upon detected config files
install_commands = dict({
    'requirements.txt': 'pip install -r requirements.txt',
    'package.json': 'npm install',
    'yarn.lock': 'yarn install --frozen-lockfile'
})


def get_dataplattform_config(path: str) -> dict:
    filename = config_files[path]
    try:
        config = safe_parse_yaml(filename)
        if 'dataplattform' in config.keys():
            return config['dataplattform']
        else:
            return dict()
    except Exception as e:
        print("\nException occurred when parsing dataplattform config for " + filename)
        traceback.print_stack()
        raise e


# Search a Dataplattform service for dependencies on other Dataplattform services
def resolve_dependencies(path: str, filename: str) -> list:
    config = safe_parse_yaml(filename)
    if 'dataplattform' in config.keys() and 'dependencies' in config['dataplattform'].keys():
        result = []
        abspath = os.path.abspath(path)
        for relpath in config['dataplattform']['dependencies']:
            result.append(os.path.relpath(os.path.join(abspath, relpath), os.curdir))
        return result

    else:
        return []


# Check if a list of paths contain a path that refers to the same file
def contains_path(path_list: list, path: str) -> bool:
    i = 0
    while i < len(path_list):
        item = path_list[i]
        exists = False
        try:
            exists = os.path.samefile(item, path)
        except OSError as e:
            raise e
        finally:
            if exists:
                return True
            else:
                i += 1
    return False


# Remove any path from the list that refers to the same file
def remove_path(path_list: list, path: str) -> None:
    i = 0
    while i < len(path_list):
        item = path_list[i]
        if os.path.samefile(item, path):
            path_list.remove(item)
            return
        else:
            i += 1
    raise IndexError('Path list does not include element: ' + path + "\n" + str(path_list))


# Find all service directories
def search(target: str) -> None:
    for entry in os.scandir(target):
        if entry.is_file():
            if entry.name == 'serverless.yml' or entry.name == 'serverless.yaml':
                if not contains_path(list(targets), target):
                    targets[target] = resolve_dependencies(target, entry.path)
                    config_files[target] = entry.path
        elif entry.name not in ignore:
            search(entry.path)


# Sort services topologically by their dependencies
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
            print("Warning: Service " + path + " depends on a service that is not within the working directory: " + dep)

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


def print_status(status: str = None) -> None:
    if status is not None:
        message = "\nDataplattform: " + status
        line = '\n' + ''.join(['-' * (len(message) - 1)])
        print("\n" + line + message + line)


def get_deployment_commands(path: str, stage: str = None) -> list:
    message = "Deploying service: " + path
    commands = ['echo ' + message, 'cd ' + path]
    for file in os.listdir(path):
        if file in install_commands.keys():
            commands.append(install_commands[file])
    commands.append('sls deploy' + ((" --stage " + stage) if stage is not None else ""))
    return commands


def get_glue_commands(path: str) -> list:
    dp_config = get_dataplattform_config(path)

    if 'glue' in dp_config.keys() and 'tableName' in dp_config['glue'].keys():

        if 'accessLevel' in dp_config['glue'].keys():
            access_level = dp_config['glue']['accessLevel']
            if access_level not in access_levels:
                access_levels.append(access_level)

        table_name = dp_config['glue']['tableName']
        message = 'Registering glue table: ' + table_name
        return ['echo ' + message, 'dataplattform register-table ' + table_name]
    else:
        return []


def get_remove_commands(path: str, stage: str = None) -> list:
    message = "Removing service: " + path
    return ['echo ' + message,
            'cd ' + path,
            'sls remove' + ((" --stage " + stage) if stage is not None else "")]


def run_process(command: str) -> None:
    try:
        if subprocess.call(command, shell=True) != 0:
            raise Exception("An error occurred while running a subprocess")
    except Exception as e:
        print(e)
        traceback.print_stack()
        raise e


def update_database() -> None:
    print_status("Starting database update")
    success = True
    for access_level in access_levels:
        message = "Updating database level " + str(access_level)
        try:
            run_process("echo " + message + " && dataplattform database -a " + str(access_level) + " update-tables")
        except Exception as e:
            print("\nException occurred when updating database with access-level " + str(access_level) + "\n" + str(e))
            traceback.print_stack()
            success = False
            break
    print_status("Database update complete" if success else "Database update stopped")


def run_process_per_path(
        paths: list,
        get_cmd_func,
        start_message: str = None,
        failed_message: str = None,
        complete_message: str = None) -> None:
    print_status(start_message)
    success = True

    for path in paths:
        commands = get_cmd_func(path)
        try:
            if subprocess.call(' && '.join(commands), shell=True) != 0:
                raise Exception(str("\nAn error occurred while running a subprocess at " + path) if len(path) > 0
                                else "\nAn error occurred while running a subprocess")

        except Exception as e:
            print(e)
            traceback.print_stack()
            success = False
            break

    print_status(complete_message if success else failed_message)


def init(parser: ArgumentParser):
    parser.add_argument('-s', '--services', default='.', type=str, nargs='*')
    parser.add_argument('-e', '--stage', default='dev', choices=['dev', 'test', 'prod'])
    parser.add_argument('-c', '--config-file', default=None, dest='config_file')
    parser.add_argument('-r', '--remove', default=False, action='store_true')


def run(args: Namespace, _):
    print("")
    for target in args.services:
        search(target)

    paths = topological_sort(targets)

    if args.remove:
        paths.reverse()
        # Remove all specified services
        run_process_per_path(
            paths=paths,
            get_cmd_func=lambda path: get_remove_commands(path, args.stage),
            start_message="Starting service removal",
            failed_message="Service removal stopped",
            complete_message="Service removal complete"
        )

    else:
        if args.config_file is not None:
            # Configure specified SSM-parameters
            run_process_per_path(
                paths=[''],
                get_cmd_func=lambda path: ["dataplattform configure --config-file " + args.config_file],
                start_message="Configuring parameters",
                failed_message="Parameter configuraiton stopped",
                complete_message="Parameter configuration complete"
            )

        # Deploy all specified services
        run_process_per_path(
            paths=paths,
            get_cmd_func=lambda path: get_deployment_commands(path, args.stage) + get_glue_commands(path),
            start_message="Starting service deployment",
            failed_message="Service deployment stopped",
            complete_message="Service deployment complete"
        )

        if len(access_levels) > 0:
            update_database()
