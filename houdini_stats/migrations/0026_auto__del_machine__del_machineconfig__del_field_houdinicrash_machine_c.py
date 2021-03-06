# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import dbs
import south.db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        db = dbs['stats']
        db.dry_run = south.db.db.dry_run
        
        # Deleting model 'Machine'
        db.delete_table(u'houdini_stats_machine')

        # Deleting model 'MachineConfig'
        db.delete_table(u'houdini_stats_machineconfig')

        # Deleting field 'HoudiniCrash.machine_config'
        db.delete_column(u'houdini_stats_houdinicrash', 'machine_config_id')

        # Deleting field 'HoudiniUsageLog.machine_config'
        db.delete_column(u'houdini_stats_houdiniusagelog', 'machine_config_id')

        # Deleting field 'HoudiniToolUsage.machine_config'
        db.delete_column(u'houdini_stats_houdinitoolusage', 'machine_config_id')

        # Deleting field 'HoudiniUsageCount.machine_config'
        db.delete_column(u'houdini_stats_houdiniusagecount', 'machine_config_id')

        # Deleting field 'Uptime.machine_config'
        db.delete_column(u'houdini_stats_uptime', 'machine_config_id')

        # Deleting field 'HoudiniUsageFlag.machine_config'
        db.delete_column(u'houdini_stats_houdiniusageflag', 'machine_config_id')


    def backwards(self, orm):
        db = dbs['stats']
        db.dry_run = south.db.db.dry_run

        # Adding model 'Machine'
        db.create_table(u'houdini_stats_machine', (
            ('hardware_id', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'houdini_stats', ['Machine'])

        # Adding model 'MachineConfig'
        db.create_table(u'houdini_stats_machineconfig', (
            ('machine', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['houdini_stats.Machine'])),
            ('graphics_card', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('product', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('is_apprentice', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('operating_system', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('houdini_build_number', self.gf('django.db.models.fields.CharField')(default=0, max_length=10)),
            ('houdini_minor_version', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('config_hash', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('system_memory', self.gf('django.db.models.fields.FloatField')(default=0, blank=True)),
            ('raw_user_info', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ip_address', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
            ('cpu_info', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('system_resolution', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('houdini_major_version', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('number_of_processors', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('graphics_card_version', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'houdini_stats', ['MachineConfig'])

        # Adding field 'HoudiniCrash.machine_config'
        db.add_column(u'houdini_stats_houdinicrash', 'machine_config',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['houdini_stats.MachineConfig']),
                      keep_default=False)

        # Adding field 'HoudiniUsageLog.machine_config'
        db.add_column(u'houdini_stats_houdiniusagelog', 'machine_config',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['houdini_stats.MachineConfig']),
                      keep_default=False)

        # Adding field 'HoudiniToolUsage.machine_config'
        db.add_column(u'houdini_stats_houdinitoolusage', 'machine_config',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['houdini_stats.MachineConfig']),
                      keep_default=False)

        # Adding field 'HoudiniUsageCount.machine_config'
        db.add_column(u'houdini_stats_houdiniusagecount', 'machine_config',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['houdini_stats.MachineConfig']),
                      keep_default=False)

        # Adding field 'Uptime.machine_config'
        db.add_column(u'houdini_stats_uptime', 'machine_config',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['houdini_stats.MachineConfig']),
                      keep_default=False)

        # Adding field 'HoudiniUsageFlag.machine_config'
        db.add_column(u'houdini_stats_houdiniusageflag', 'machine_config',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['houdini_stats.MachineConfig']),
                      keep_default=False)


    models = {
        u'houdini_stats.houdinicrash': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniCrash'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stack_trace': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20'})
        },
        u'houdini_stats.houdinimachineconfig': {
            'Meta': {'object_name': 'HoudiniMachineConfig'},
            'houdini_build_number': ('django.db.models.fields.CharField', [], {'default': '0', 'max_length': '10'}),
            'houdini_major_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'houdini_minor_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_apprentice': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'machine_config': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['stats_main.MachineConfig']", 'unique': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        },
        u'houdini_stats.houdinitoolusage': {
            'Meta': {'ordering': "('date', 'count')", 'object_name': 'HoudiniToolUsage'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_asset': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_builtin': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"}),
            'tool_creation_location': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'tool_creation_mode': ('django.db.models.fields.IntegerField', [], {}),
            'tool_name': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        u'houdini_stats.houdiniusagecount': {
            'Meta': {'ordering': "('date', 'count')", 'object_name': 'HoudiniUsageCount'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"})
        },
        u'houdini_stats.houdiniusageflag': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniUsageFlag'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"})
        },
        u'houdini_stats.houdiniusagelog': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniUsageLog'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'message': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"})
        },
        u'houdini_stats.uptime': {
            'Meta': {'ordering': "('date', 'number_of_seconds')", 'object_name': 'Uptime'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idle_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'number_of_seconds': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"})
        },
        u'stats_main.machine': {
            'Meta': {'object_name': 'Machine'},
            'hardware_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'stats_main.machineconfig': {
            'Meta': {'ordering': "('creation_date',)", 'object_name': 'MachineConfig'},
            'config_hash': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'cpu_info': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'graphics_card': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'graphics_card_version': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'machine': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.Machine']"}),
            'number_of_processors': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'raw_user_info': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'system_memory': ('django.db.models.fields.FloatField', [], {'default': '0', 'blank': 'True'}),
            'system_resolution': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        }
    }

    complete_apps = ['houdini_stats']