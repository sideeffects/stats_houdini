# encoding: utf-8
import datetime
from south.db import dbs
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MachineConfig'
        db = dbs['stats']
        db.create_table('houdini_stats_machineconfig', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hardware_id', self.gf('django.db.models.fields.IntegerField')()),
            ('ip_address', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('last_active_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('config_hash', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('houdini_major_version', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('houdini_minor_version', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('houdini_build_number', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('product', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('graphics_card', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('graphics_card_version', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('operating_system', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('system_memory', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('system_resolution', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('number_of_processors', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('cpu_info', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('houdini_stats', ['MachineConfig'])

        # Adding model 'HoudiniCrash'
        db.create_table('houdini_stats_houdinicrash', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('machine_config', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['houdini_stats.MachineConfig'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('stack_trace', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('houdini_stats', ['HoudiniCrash'])

        # Adding model 'NodeTypeUsage'
        db.create_table('houdini_stats_nodetypeusage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('machine_config', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['houdini_stats.MachineConfig'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('node_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('is_builtin', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_asset', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('houdini_stats', ['NodeTypeUsage'])

        # Adding model 'Uptime'
        db.create_table('houdini_stats_uptime', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('machine_config', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['houdini_stats.MachineConfig'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('number_of_seconds', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('houdini_stats', ['Uptime'])


    def backwards(self, orm):
        
        # Deleting model 'MachineConfig'
        db = dbs['stats']
        db.delete_table('houdini_stats_machineconfig')

        # Deleting model 'HoudiniCrash'
        db.delete_table('houdini_stats_houdinicrash')

        # Deleting model 'NodeTypeUsage'
        db.delete_table('houdini_stats_nodetypeusage')

        # Deleting model 'Uptime'
        db.delete_table('houdini_stats_uptime')


    models = {
        'houdini_stats.houdinicrash': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniCrash'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['houdini_stats.MachineConfig']"}),
            'stack_trace': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'houdini_stats.machineconfig': {
            'Meta': {'ordering': "('last_active_date',)", 'object_name': 'MachineConfig'},
            'config_hash': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'cpu_info': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'graphics_card': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'graphics_card_version': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'hardware_id': ('django.db.models.fields.IntegerField', [], {}),
            'houdini_build_number': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'houdini_major_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'houdini_minor_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'last_active_date': ('django.db.models.fields.DateTimeField', [], {}),
            'number_of_processors': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'system_memory': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'system_resolution': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'houdini_stats.nodetypeusage': {
            'Meta': {'ordering': "('date',)", 'object_name': 'NodeTypeUsage'},
            'count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_asset': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_builtin': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['houdini_stats.MachineConfig']"}),
            'node_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'houdini_stats.uptime': {
            'Meta': {'ordering': "('date', 'number_of_seconds')", 'object_name': 'Uptime'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['houdini_stats.MachineConfig']"}),
            'number_of_seconds': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['houdini_stats']
