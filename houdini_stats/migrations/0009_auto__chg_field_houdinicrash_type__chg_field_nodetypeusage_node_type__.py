# encoding: utf-8
import datetime
import south.db
from south.db import dbs
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db = dbs['stats']
        db.dry_run = south.db.db.dry_run
        
        # Changing field 'HoudiniCrash.type'
        db.alter_column(u'houdini_stats_houdinicrash', 'type', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'NodeTypeUsage.node_type'
        db.alter_column(u'houdini_stats_nodetypeusage', 'node_type', self.gf('django.db.models.fields.CharField')(max_length=60))

        # Changing field 'MachineConfig.graphics_card'
        db.alter_column(u'houdini_stats_machineconfig', 'graphics_card', self.gf('django.db.models.fields.CharField')(max_length=40))

        # Changing field 'MachineConfig.product'
        db.alter_column(u'houdini_stats_machineconfig', 'product', self.gf('django.db.models.fields.CharField')(max_length=40))

        # Changing field 'MachineConfig.cpu_info'
        db.alter_column(u'houdini_stats_machineconfig', 'cpu_info', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'MachineConfig.system_resolution'
        db.alter_column(u'houdini_stats_machineconfig', 'system_resolution', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'MachineConfig.operating_system'
        db.alter_column(u'houdini_stats_machineconfig', 'operating_system', self.gf('django.db.models.fields.CharField')(max_length=40))

        # Changing field 'MachineConfig.graphics_card_vendor'
        db.alter_column(u'houdini_stats_machineconfig', 'graphics_card_vendor', self.gf('django.db.models.fields.CharField')(max_length=40))


    def backwards(self, orm):
        db = dbs['stats']
        
        # Changing field 'HoudiniCrash.type'
        db.alter_column(u'houdini_stats_houdinicrash', 'type', self.gf('django.db.models.fields.CharField')(max_length=10))

        # Changing field 'NodeTypeUsage.node_type'
        db.alter_column(u'houdini_stats_nodetypeusage', 'node_type', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'MachineConfig.graphics_card'
        db.alter_column(u'houdini_stats_machineconfig', 'graphics_card', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'MachineConfig.product'
        db.alter_column(u'houdini_stats_machineconfig', 'product', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'MachineConfig.cpu_info'
        db.alter_column(u'houdini_stats_machineconfig', 'cpu_info', self.gf('django.db.models.fields.CharField')(max_length=10))

        # Changing field 'MachineConfig.system_resolution'
        db.alter_column(u'houdini_stats_machineconfig', 'system_resolution', self.gf('django.db.models.fields.CharField')(max_length=10))

        # Changing field 'MachineConfig.operating_system'
        db.alter_column(u'houdini_stats_machineconfig', 'operating_system', self.gf('django.db.models.fields.CharField')(max_length=20))

        # Changing field 'MachineConfig.graphics_card_vendor'
        db.alter_column(u'houdini_stats_machineconfig', 'graphics_card_vendor', self.gf('django.db.models.fields.CharField')(max_length=20))


    models = {
        u'houdini_stats.event': {
            'Meta': {'ordering': "('date',)", 'object_name': 'Event'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        u'houdini_stats.houdinicrash': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniCrash'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
            'stack_trace': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20'})
        },
        u'houdini_stats.machineconfig': {
            'Meta': {'ordering': "('last_active_date',)", 'object_name': 'MachineConfig'},
            'config_hash': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'cpu_info': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'graphics_card': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'graphics_card_vendor': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'hardware_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'houdini_build_number': ('django.db.models.fields.CharField', [], {'default': '0', 'max_length': '10'}),
            'houdini_major_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'houdini_minor_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'is_apprentice': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_active_date': ('django.db.models.fields.DateTimeField', [], {}),
            'number_of_processors': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'system_memory': ('django.db.models.fields.FloatField', [], {'default': '0', 'blank': 'True'}),
            'system_resolution': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        u'houdini_stats.nodetypeusage': {
            'Meta': {'ordering': "('date',)", 'object_name': 'NodeTypeUsage'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_asset': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_builtin': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
            'node_creation_mode': ('django.db.models.fields.IntegerField', [], {}),
            'node_type': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        u'houdini_stats.uptime': {
            'Meta': {'ordering': "('date', 'number_of_seconds')", 'object_name': 'Uptime'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
            'number_of_seconds': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['houdini_stats']
