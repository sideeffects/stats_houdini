'''
Drop all tables in the database but keep the database itself.
'''

import optparse

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.db import connections, transaction

class Command(BaseCommand):
    help = "Drop all tables in the database."
    args = ""

    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "-d", "--database",
            dest="database",
            default="default",
            help="Database name from settings.py",
        ),
    )

    def handle(self, *args, **options):
        '''
        Execute command.
        '''
        connection = connections[options["database"]]
        cursor = connection.cursor()

        while True:
            remaining_tables = connection.introspection.table_names()
            if len(remaining_tables) == 0:
                break

            for remaining_table in remaining_tables:
                try:
                    cursor.execute("drop table %s cascade" % remaining_table)
                except IntegrityError:
                    # We can't delete this table before deleting others, so
                    # try the next one
                    pass
                else:
                    break

        transaction.commit_unless_managed()

