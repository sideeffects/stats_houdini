# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import dbs
import south.db
from south.v2 import DataMigration

class Migration(DataMigration):

    def forwards(self, orm):
        """ 
        Update old foreign keys to point to stats.MachineConfig.
        """        
        db = dbs['stats']
        db.dry_run = south.db.db.dry_run
        
        # Update houdini crashes
        for houdini_crash in orm.HoudiniCrash.objects.using("stats").all():
            stats_machine_config = orm['stats_main.MachineConfig'].objects.using(
                "stats").get(config_hash = houdini_crash.machine_config.config_hash) 
            
            houdini_crash.stats_machine_config = stats_machine_config
            houdini_crash.save()
             
        # Update houdini tools usages
        for houdini_tool_usage in orm.HoudiniToolUsage.objects.using("stats").all():
            stats_machine_config = orm['stats_main.MachineConfig'].objects.using(
                "stats").get(config_hash = houdini_tool_usage.machine_config.config_hash) 
            
            houdini_tool_usage.stats_machine_config = stats_machine_config
            houdini_tool_usage.save()
        
        # Update houdini usage counts
        for houdini_usage_count in orm.HoudiniUsageCount.objects.using("stats").all():
            stats_machine_config = orm['stats_main.MachineConfig'].objects.using(
                "stats").get(config_hash = houdini_usage_count.machine_config.config_hash) 
            
            houdini_usage_count.stats_machine_config = stats_machine_config
            houdini_usage_count.save()
        
        # Update houdini usage flags
        for houdini_usage_flag in orm.HoudiniUsageFlag.objects.using("stats").all():
            stats_machine_config = orm['stats_main.MachineConfig'].objects.using(
                "stats").get(config_hash = houdini_usage_flag.machine_config.config_hash) 
            
            houdini_usage_flag.stats_machine_config = stats_machine_config
            houdini_usage_flag.save()
        
        # Update houdini usage log
        for houdini_usage_log in orm.HoudiniUsageLog.objects.using("stats").all():
            stats_machine_config = orm['stats_main.MachineConfig'].objects.using(
                "stats").get(config_hash = houdini_usage_log.machine_config.config_hash) 
            
            houdini_usage_log.stats_machine_config = stats_machine_config
            houdini_usage_log.save()
        
        # Update houdini uptime
        for houdini_uptime in orm.Uptime.objects.using("stats").all():
            stats_machine_config = orm['stats_main.MachineConfig'].objects.using(
                "stats").get(config_hash = houdini_uptime.machine_config.config_hash) 
            
            houdini_uptime.stats_machine_config = stats_machine_config
            houdini_uptime.save()
    
    def backwards(self, orm):
        db = dbs['stats']
        db.dry_run = south.db.db.dry_run
        
    models = {
        u'houdini_stats.houdinicrash': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniCrash'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
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
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
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
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"})
        },
        u'houdini_stats.houdiniusageflag': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniUsageFlag'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"})
        },
        u'houdini_stats.houdiniusagelog': {
            'Meta': {'ordering': "('date',)", 'object_name': 'HoudiniUsageLog'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
            'message': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'stats_machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stats_main.MachineConfig']"})
        },
        u'houdini_stats.machine': {
            'Meta': {'object_name': 'Machine'},
            'hardware_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'houdini_stats.machineconfig': {
            'Meta': {'ordering': "('creation_date',)", 'object_name': 'MachineConfig'},
            'config_hash': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'cpu_info': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'graphics_card': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'graphics_card_version': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'houdini_build_number': ('django.db.models.fields.CharField', [], {'default': '0', 'max_length': '10'}),
            'houdini_major_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'houdini_minor_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'is_apprentice': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'machine': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.Machine']"}),
            'number_of_processors': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'operating_system': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'raw_user_info': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'system_memory': ('django.db.models.fields.FloatField', [], {'default': '0', 'blank': 'True'}),
            'system_resolution': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        },
        u'houdini_stats.uptime': {
            'Meta': {'ordering': "('date', 'number_of_seconds')", 'object_name': 'Uptime'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idle_time': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'machine_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['houdini_stats.MachineConfig']"}),
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
    symmetrical = True
