import copy
import os
import subprocess
import traceback
from argparse import ArgumentParser, Namespace
import multiprocessing as mp
import sys
from ..helper import safe_parse_yaml

dependencies = dict()
config_files = dict()

# Structures to ensure correct concurrency
access_levels = mp.Manager().list()
successful_services = mp.Manager().list()
lock = mp.Manager().Lock()

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
            return {}
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
def search(path: str) -> None:
    for entry in os.scandir(path):
        if entry.is_file():
            if entry.name == 'serverless.yml' or entry.name == 'serverless.yaml':
                if not contains_path(list(dependencies), path):
                    dependencies[path] = resolve_dependencies(path, entry.path)
                    config_files[path] = entry.path
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


def get_install_commands(path: str) -> list:
    message = "Installing dependencies for: " + path
    commands = ['echo ' + message]
    for file in os.listdir(path):
        if file in install_commands.keys():
            commands.append(install_commands[file])

    return commands


def get_deployment_commands(path: str, stage: str = None) -> list:
    message = "Deploying service: " + path
    commands = ['echo ' + message]
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


def services_without_dependencies(dependency_graph, dependencies, iteration):
    has_no_dependencies = []

    for path in dependencies.keys():
        if not any(x in dependencies.keys() for x in dependencies.get(path)):
            dependency_graph[iteration].append(path)
            has_no_dependencies.append(path)

    return has_no_dependencies


# Puts services dependent on 'serverless-python-requirements' plugin in an isolated level so they run in sequential
def separate_sequential_services(dependency_graph, has_no_dependencies, iteration):
    sequential_services = []
    for service in has_no_dependencies:
        config = safe_parse_yaml(config_files.get(service))
        if 'plugins' in config.keys() and 'serverless-python-requirements' in config['plugins']:
            sequential_services.append(service)

    # Add sequential services to new layer
    if len(sequential_services) > 1:
        [dependency_graph[iteration].remove(path) for path in sequential_services[1:]]
        for path in sequential_services[1:]:
            dependency_graph.append([path])
            iteration += 1

    return iteration + 1


def create_dependency_graph():
    dependencies_copy = copy.deepcopy(dependencies)
    dependency_graph = []
    iteration = 0
    while len(dependencies_copy) > 0:
        dependency_graph.append([])

        has_no_dependencies = services_without_dependencies(dependency_graph, dependencies_copy, iteration)
        [dependencies_copy.pop(path) for path in has_no_dependencies]

        iteration = separate_sequential_services(dependency_graph, has_no_dependencies, iteration)

    return dependency_graph


def catch_stdout(print_stdout, path, start_message=None, complete_message=None, failed_message=None, success=None):
    temp_file_path = path + "/" + str(os.getpid()) + ".txt"
    if print_stdout:
        start_message += " for: " + path
        complete_message += " for: " + path
        failed_message += " for: " + path

        sys.stdout = sys.__stdout__

        try:
            with open(temp_file_path, 'r') as f:
                lock.acquire()
                print_status(start_message)
                print(f.read().strip("\n"))
                print_status(complete_message if success else failed_message)
                lock.release()

            os.remove(temp_file_path)
        except FileNotFoundError as e:
            print("\nFileNotFoundError occurred when printing stdout ")
            traceback.print_stack()
            raise e
    else:
        try:
            sys.stdout = open(temp_file_path, "a")
        except IOError as e:
            print("\nIOError occurred when redirecting stdout ")
            traceback.print_stack()
            raise e


def run_process_for_one_path(
        path: str,
        get_cmd_func,
        start_message: str = None,
        failed_message: str = None,
        complete_message: str = None) -> None:
    catch_stdout(False, path)

    success = True
    commands = get_cmd_func(path)

    temp_file = str(os.getpid()) + ".txt"

    try:
        if subprocess.call(' && '.join(commands) + " >> " + temp_file, shell=True) != 0:
            raise Exception(str("\nAn error occurred while running a subprocess at " + path) if len(path) > 0
                            else "\nAn error occurred while running a subprocess")

    except Exception as e:
        print(e)
        traceback.print_stack()
        success = False

    if success:
        successful_services.append(path)

    catch_stdout(True, path, start_message, failed_message, complete_message)


def start_processes(paths_in_level, action, commands):
    running_processes = []
    for path in paths_in_level:
        p = mp.Process(target=run_process_for_one_path,
                       args=(path, commands,
                             "Starting service " + action + " (parallel)",
                             "Service " + action + " stopped (parallel)",
                             "Service " + action + " complete (parallel)"))
        p.start()
        running_processes.append(p)

    for process in running_processes:
        process.join()


def print_success_status(paths, action):
    service_status = "Number of successfull " + action + ": " + str(len(successful_services)) + "/" + str(
        len(paths))

    if len(successful_services) != len(paths):
        service_status += "\nThe following services failed: "
        for service in paths:
            if service not in successful_services:
                service_status += "\n- " + service

    print_status(service_status)


def init(parser: ArgumentParser):
    parser.add_argument('-s', '--services', default='.', type=str, nargs='*')
    parser.add_argument('-e', '--stage', default='dev', choices=['dev', 'test', 'prod'])
    parser.add_argument('-c', '--config-file', default=None, dest='config_file')
    parser.add_argument('-r', '--remove', default=False, action='store_true')
    parser.add_argument('-p', '--parallel', default=False, action='store_true')


def run(args: Namespace, _):
    print("")
    for path in args.services:
        search(path)

    paths = topological_sort(dependencies)

    if args.config_file is not None:
        # Configure specified SSM-parameters
        run_process_per_path(
            paths=[''],
            get_cmd_func=lambda _: ["dataplattform configure --config-file " + args.config_file],
            start_message="Configuring parameters",
            failed_message="Parameter configuraiton stopped",
            complete_message="Parameter configuration complete"
        )

    if args.parallel:
        deploy_order_paths = create_dependency_graph()
        if args.remove:
            deploy_order_paths.reverse()
            # Remove all specified services in parallel
            for paths_in_level in deploy_order_paths:
                start_processes(paths_in_level, "removal",
                                lambda p: ['cd ' + p] + get_install_commands(p) + get_remove_commands(p, args.stage))

            print_success_status(paths, "removals")
        else:
            deploy_order_paths = create_dependency_graph()
            # Deploy all specified services in parallel
            for paths_in_level in deploy_order_paths:
                start_processes(paths_in_level, "deployment", lambda p: (['cd ' + p] +
                                                                         get_install_commands(p) +
                                                                         get_deployment_commands(p, args.stage)))
            # Run glue commands
            run_process_per_path(
                paths=successful_services,
                get_cmd_func=lambda p: (['cd ' + p] +
                                        get_glue_commands(p)),
                start_message="Starting glue commands",
                failed_message="Failed glue commands",
                complete_message="Completed glue commands"
            )

            print_success_status(paths, "deployments")
    else:
        if args.remove:
            paths.reverse()
            # Remove all specified services
            run_process_per_path(
                paths=paths,
                get_cmd_func=lambda p: ['cd ' + p] + get_install_commands(p) + get_remove_commands(p, args.stage),
                start_message="Starting service removal",
                failed_message="Service removal stopped",
                complete_message="Service removal complete"
            )
        else:
            # Deploy all specified services sequentially
            run_process_per_path(
                paths=paths,
                get_cmd_func=lambda p: (['cd ' + p] +
                                        get_install_commands(p) +
                                        get_deployment_commands(p, args.stage) +
                                        get_glue_commands(p)),
                start_message="Starting service deployment",
                failed_message="Service deployment stopped",
                complete_message="Service deployment complete"
            )

    if len(access_levels) > 0:
        update_database()
