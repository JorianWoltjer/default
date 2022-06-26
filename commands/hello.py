from main import *

def hello(ARGS):
    print(f"Hello, {ARGS.name}!")

def setup(subparsers):
    parser = subparsers.add_parser('hello', help='Say hello')
    parser.set_defaults(func=hello)

    parser.add_argument('name', help='The name to say hello to')
