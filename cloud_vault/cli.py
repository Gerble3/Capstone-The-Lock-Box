
from __future__ import annotations
import argparse, getpass, json
from .db import init_vault, open_vault, add_entry, list_entries, get_entry


def _prompt_pw(pw_opt: str | None) -> str:
    return pw_opt if pw_opt else getpass.getpass("Master password: ")


def cmd_init(args):
    pw = _prompt_pw(args.pw)
    v = init_vault(args.db, pw)
    print(f"Initialized vault at {args.db}")


def cmd_add(args):
    pw = _prompt_pw(args.pw)
    v = open_vault(args.db, pw)
    eid = add_entry(v, args.title, args.url or "", args.username or "", args.password or "", args.notes or "")
    print(f"Added entry id={eid}")


def cmd_list(args):
    pw = _prompt_pw(args.pw)
    v = open_vault(args.db, pw)
    rows = list_entries(v)
    print(json.dumps(rows, indent=2))


def cmd_show(args):
    pw = _prompt_pw(args.pw)
    v = open_vault(args.db, pw)
    print(json.dumps(get_entry(v, args.id, reveal_password=args.reveal), indent=2))


def main():
    ap = argparse.ArgumentParser(prog="cloud_vault")
    sub = ap.add_subparsers(required=True)

    p = sub.add_parser("init"); p.add_argument("--db", required=True); p.add_argument("--user"); p.add_argument("--pw")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add"); p.add_argument("--db", required=True); p.add_argument("--pw")
    p.add_argument("--title", required=True); p.add_argument("--url"); p.add_argument("--username"); p.add_argument("--password"); p.add_argument("--notes")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list"); p.add_argument("--db", required=True); p.add_argument("--pw")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show"); p.add_argument("--db", required=True); p.add_argument("--pw"); p.add_argument("--id", type=int, required=True); p.add_argument("--reveal", action="store_true")
    p.set_defaults(func=cmd_show)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
