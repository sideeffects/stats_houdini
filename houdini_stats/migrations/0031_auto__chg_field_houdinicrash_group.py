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

        # Changing field 'HoudiniCrash.group'
        db.alter_column(u'houdini_stats_houdinicrash', 'group_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['houdini_stats.HoudiniCrashGroup'], null=True))

    def backwards(self, orm):
        db = dbs['stats']
        db.dry_run = south.db.db.dry_run

        # Changing field 'HoudiniCrash.group'
        db.alter_column(u'houdini_stats_houdinicrash', 'group_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['houdini_stats.HoudiniCrashGroup']))

    models = {
        u'houdini_stats.houdinicrash': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniCrash'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['houdini_stats.HoudiniCrashGroup']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stack_trace': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20'})
        },
        u'houdini_stats.houdinicrashgroup': {
            'Meta': {'object_name': 'HoudiniCrashGroup'},
            'fixed_in_houdini_build': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '12'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_fixed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'representative_stack_trace': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        u'houdini_stats.houdiniflag': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniFlag'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"})
        },
        u'houdini_stats.houdinilog': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniLog'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'log_entry': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"}),
            'timestamp': ('django.db.models.fields.FloatField', [], {})
        },
        u'houdini_stats.houdinimachineconfig': {
            'Meta': {'object_name': 'HoudiniMachineConfig'},
            'houdini_build_number': ('django.db.models.fields.CharField', [], {'default': '0', 'max_length': '10'}),
            'houdini_major_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'houdini_minor_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_apprentice': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'machine_config': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'get_extra_fields'", 'unique': 'True', 'to': u"orm['stats_main.MachineConfig']"}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        },
        u'houdini_stats.houdinipersistentstats': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniPersistentStats'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'houdini_stats.houdinisumandcount': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniSumAndCount'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"}),
            'sum': ('django.db.models.fields.FloatField', [], {})
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
            'hardware_id': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'stats_main.machineconfig': {
            'Meta': {'ordering': "('creation_date',)", 'unique_together': "(('machine', 'config_hash'),)", 'object_name': 'MachineConfig'},
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
