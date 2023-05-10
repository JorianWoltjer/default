from default.main import *
from colorama import Fore, Style


def fake_info(ARGS):
    from faker import Faker

    faker = Faker(ARGS.locale)

    for i in range(ARGS.number):
        profile = faker.profile()
        if ARGS.number > 1:
            success(f"Profile {i+1}:")
        else:
            success("Profile:")

        print(f"{Fore.LIGHTBLACK_EX}- Name: {Style.RESET_ALL}{profile['name']}")
        print(f"{Fore.LIGHTBLACK_EX}- Username: {Style.RESET_ALL}{profile['username']}")
        print(f"{Fore.LIGHTBLACK_EX}- Email: {Style.RESET_ALL}{profile['mail']}")
        print(f"{Fore.LIGHTBLACK_EX}- Phone (MSISDN): {Style.RESET_ALL}{faker.msisdn()}")
        print(f"{Fore.LIGHTBLACK_EX}- Address: \n{Style.RESET_ALL}{profile['address']}")
        print(f"{Fore.LIGHTBLACK_EX}- Website: {Style.RESET_ALL}{', '.join(profile['website'])}")
        coord = profile["current_location"]
        print(f"{Fore.LIGHTBLACK_EX}- Coordinates: {Style.RESET_ALL}{coord[0]}, {coord[1]}")
        print(f"{Fore.LIGHTBLACK_EX}- Date & Time: {Style.RESET_ALL}{faker.date_time()}")
        print()


def fake_text(ARGS):
    from faker import Faker

    faker = Faker(ARGS.locale)

    for _ in range(ARGS.paragraphs):
        print(" ".join(faker.paragraphs(nb=ARGS.sentences)), end="\n\n")


def setup(subparsers):
    parser = subparsers.add_parser("fake", help="Create fake things")
    parser_subparsers = parser.add_subparsers(dest="action", required=True)

    parser_info = parser_subparsers.add_parser("info", help="Print a list of various fake information")
    parser_info.add_argument("number", nargs="?", type=int, default=1, help="The amount of repeated fake information to print")
    parser_info.add_argument("--locale", "-l", default="en_US", help="The locale to use for the fake information")
    parser_info.set_defaults(func=fake_info)

    parser_text = parser_subparsers.add_parser("text", help="Create fake text")
    parser_text.add_argument("paragraphs", nargs="?", type=int, default=2, help="The amount of paragraphs to generate")
    parser_text.add_argument("sentences", nargs="?", type=int, default=5, help="The number of sentences per paragraph")
    parser_text.add_argument("--locale", "-l", default="en_US", help="The locale to use for the fake text")
    parser_text.set_defaults(func=fake_text)
