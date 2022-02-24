import argparse




parser = argparse.ArgumentParser()
subp = parser.add_subparsers(dest='subparser_name')

add_member_parser = subp.add_parser('add', help='Add a member to quicksight')
remove_member_parser = subp.add_parser('remove', help='Remove a member from quicksight')
get_members_parser = subp.add_parser('get', help='Lists quicksight members')

args = parser.parse_args()
if args.subparser_name == 'add':
    print("add")
elif args.subparser_name == 'remove':
    print("remove")
elif args.subparser_name == 'get':
    print("get")