try:
    import sys

    print(f'sys.path: {sys.path}')
finally:
    pass

from takahom.server import server

if __name__ == "__main__":
    def f_parse_args() -> None:
        import argparse
        parser = argparse.ArgumentParser()

        parser.add_argument("mode", choices=["demo", "run"], help="subcmd")

        parser.add_argument("--profile", type=str,
                            default="prod", choices=["prod", "dev"], help="profile")

        parser.add_argument("--conf", type=str, default='env.conf', help="config file")

        args = parser.parse_args()

        server.main(args)


    f_parse_args()
