#!/usr/bin/env python
"""
Helper script to run database migrations.
Usage: python run_migrations.py [upgrade|downgrade|revision|history]
"""
import sys
import os
from alembic.config import Config
from alembic import command

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_migrations.py [upgrade|downgrade|revision|history] [args...]")
        sys.exit(1)
    
    alembic_cfg = Config("alembic.ini")
    action = sys.argv[1]
    
    if action == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        print(f"Upgrading database to revision: {revision}")
        command.upgrade(alembic_cfg, revision)
    elif action == "downgrade":
        if len(sys.argv) < 3:
            print("Usage: python run_migrations.py downgrade <revision>")
            sys.exit(1)
        revision = sys.argv[2]
        print(f"Downgrading database to revision: {revision}")
        command.downgrade(alembic_cfg, revision)
    elif action == "revision":
        message = sys.argv[2] if len(sys.argv) > 2 else "auto migration"
        autogenerate = "--autogenerate" in sys.argv
        print(f"Creating new revision: {message}")
        command.revision(alembic_cfg, message=message, autogenerate=autogenerate)
    elif action == "history":
        print("Migration history:")
        command.history(alembic_cfg)
    elif action == "current":
        print("Current database revision:")
        command.current(alembic_cfg)
    else:
        print(f"Unknown action: {action}")
        print("Available actions: upgrade, downgrade, revision, history, current")
        sys.exit(1)

if __name__ == "__main__":
    main()

