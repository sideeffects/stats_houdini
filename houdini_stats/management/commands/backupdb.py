"""
 Command for backup database
"""

import os
import popen2
import time
import optparse
import subprocess
import pwd

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = ("Backup database. Only Mysql, Postgresql, and sqlite are"
        " supported")

    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "-l", "--load",
            dest="load_from_file",
            default=None,
            help="Load data instead of dumping data",
        ),
        optparse.make_option(
            "-r", "--redirect",
            action="store_true",
            dest="redirect_to_file",
            default=False,
            help="Redirect the output to a file",
        ),
        optparse.make_option(
            "-d", "--database",
            dest="database",
            default="default",
            help="Database name from settings.py",
        ),
    )

    def handle(self, *args, **options):
        from django.db import connection
        from django.conf import settings

        database_settings = settings.DATABASES[options["database"]]

        self.engine = database_settings["ENGINE"].split(".")[-1]
        self.db = database_settings["NAME"]
        self.user = database_settings["USER"]
        self.passwd = database_settings["PASSWORD"]
        self.host = database_settings["HOST"]
        self.port = database_settings["PORT"]

        if options["load_from_file"] is not None:
            self.load_database(options["load_from_file"])
        else:
            self.dump_database(options["redirect_to_file"])

    def dump_database(self, redirect_to_file):
        backup_dir = 'db_backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        outfile = (os.path.join(
                backup_dir, 'backup_%s.sql' % time.strftime('%Y-%m-%d'))
            if redirect_to_file else None)

        if self.engine == 'mysql':
            self.do_mysql_backup(outfile)
        elif self.engine in ('postgresql_psycopg2', 'postgresql'):
            self.do_postgresql_backup(outfile)
        elif self.engine == 'sqlite3':
            self.do_sqlite_backup(outfile)
        else:
            print 'Backup in %s engine not implemented' % self.engine

    def load_database(self, file_name):
        if self.engine == 'mysql':
            self.do_mysql_load(file_name)
        elif self.engine in ('postgresql_psycopg2', 'postgresql'):
            self.do_postgresql_load(file_name)
        elif self.engine == 'sqlite3':
            self.do_sqlite_load(file_name)
        else:
            print 'Load in %s engine not implemented' % self.engine

    def redirect_for_file(self, outfile):
        return ("" if outfile is None else " > " + outfile)

    def do_mysql_backup(self, outfile):
        os.system(('mysqldump %s %s' % (self.mysql_options(), self.db)) +
            self.redirect_for_file(outfile))

    def do_mysql_load(self, file_name):
        os.system('mysql %s %s < %s' % (
            self.mysql_options(), self.db, file_name))

    def mysql_options(self):
        args = []
        if self.user:
            args += ["--user=%s" % self.user]
        if self.passwd:
            args += ["--password=%s" % self.passwd]
        if self.host:
            args += ["--host=%s" % self.host]
        if self.port:
            args += ["--port=%s" % self.port]
        return " ".join(args)

    def do_postgresql_backup(self, outfile):
        pg_pass_file = self.create_pg_pass_file()
        os.system(
            ('pg_dump --clean %s %s' % (self.postgres_options(), self.db)) +
            self.redirect_for_file(outfile))
        os.unlink(pg_pass_file)

    def do_postgresql_load(self, file_name):
        pg_pass_file = self.create_pg_pass_file()
        os.system('psql %s %s < %s' % (
            self.postgres_options(), self.db, file_name))
        os.unlink(pg_pass_file)

    def create_pg_pass_file(self):
        """Create a password file for postgres to read in."""
        pg_pass_file = "/tmp/.pgpass"
        os.environ["PGPASSFILE"] = pg_pass_file

        with open(pg_pass_file, "w") as open_file:
            open_file.write("localhost:*:%s:%s:%s\n" % (
                self.db, self.user, self.passwd))

        os.chmod(pg_pass_file, 0600)
        return pg_pass_file

    def postgres_options(self):
        args = []
        if self.user:
            args += ["--username=%s" % self.user]
        if self.host:
            args += ["--host=%s" % self.host]
        if self.port:
            args += ["--port=%s" % self.port]
        return " ".join(args)

    def do_sqlite_backup(self, outfile):
        os.system(('echo .dump | sqlite3 %s' % self.db) +
            self.redirect_for_file(outfile))

    def do_sqlite_load(self, file_name):
        if os.path.exists(self.db):
            os.unlink(self.db)
        os.system('echo .dump | sqlite3 %s < %s' % (self.db, file_name))

