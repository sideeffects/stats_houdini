'''
Drop all tables in the database but keep the database itself.
'''

from django.core.management.base import NoArgsCommand
from django.db import connection, transaction

class Command(NoArgsCommand):
    help = "Drop all tables in the database."
    args = ""

    def handle_noargs(self, **options):
        '''
        Execute command.
        '''
        cursor = connection.cursor()

        while True:
            remaining_tables = connection.introspection.table_names()
            if len(remaining_tables) == 0:
                break
            cursor.execute("drop table %s cascade" % remaining_tables[0])

        transaction.commit_unless_managed()

