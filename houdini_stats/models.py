from django.db import models
import django.db.models.options as options

# Keep django from complaining about the db_name meta attribute.
if "db_name" not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + ("db_name",)
    
#-------------------------------------------------------------------------------

class HoudiniMachineConfig(models.Model):
    """
    Machine Config for a PC running Houdini. This model extend the generic 
    model MachinConfig from stats main.
    """
    
    machine_config = models.OneToOneField(
        'stats_main.MachineConfig',
        related_name='get_extra_fields',
        help_text='''Required to extend the Machine Config model.'''
    )
    
    houdini_major_version = models.IntegerField(  
        help_text='''Houdini major version.''',
        default=0
    )

    houdini_minor_version = models.IntegerField(  
        help_text='''Houdini minor version.''',
        default=0
    )
    
    houdini_build_number = models.CharField(  
        help_text='''Houdini build number.''',
        default=0,
        max_length=10
    )
        
    product = models.CharField(                                              
        help_text='''Name of the product used (houdini hexper, hescape, hbatch
                     mantra, mplay.''',
        max_length=40,
        blank=True,
    )
    
    is_apprentice = models.BooleanField(
        help_text='''Is the product Houdini Apprentice??''',
        default=False
    )
    
    def major_minor_version(self):
        return "%d.%d" % (
            self.houdini_major_version, self.houdini_minor_version)

    def __unicode__(self):
        return "MachineConfig(%s)" % (
            self.machine_config.config_hash)

    class Meta:
        db_name = 'stats'

def create_machine_config_extension(machine_config, user_info):
    """This is a specially-named function that stats_main will look for
    to extend the information in the machine config.
    """
    # Create new houdini machine config with the rest of the data 
    return HoudiniMachineConfig(
        machine_config = machine_config,
        houdini_major_version = user_info.get('houdini_major_version',0),
        houdini_minor_version = user_info.get('houdini_minor_version',0),
        houdini_build_number = user_info.get('houdini_build_version',0),
        product = user_info.get('application_name',"").title(),
        is_apprentice = user_info.get('license_category',"") == 'Apprentice',
    )

#-------------------------------------------------------------------------------

class HoudiniCrash(models.Model):
    """
    Represents a Houdini Crash and corresponding stack trace.
    """
    
    stats_machine_config = models.ForeignKey(
        'stats_main.MachineConfig',
        help_text='''The machine config associated with the crash.''',
    )

    date = models.DateTimeField(
        help_text='''When this crash occurred .'''
    )
    
    stack_trace = models.TextField(
        help_text='''Stack Trace for the crash.''',
        blank=True,
        default=''
    )
    
    type = models.CharField(
        help_text='''Type logged.''',
        default='',
        max_length=20
    )

    group = models.ForeignKey(
        'HoudiniCrashGroup',
        default=None,
        null=True,
    )
    
    def __unicode__(self):
        return "HoudiniCrash(%s)" % self.stack_trace

    class Meta:
        # How to order results when doing queries:
        ordering = ('date', )
        db_name = 'stats'

#-------------------------------------------------------------------------------

class HoudiniCrashGroup(models.Model):
    """
    Represents a group of HoudiniCrashes (i.e. stack traces) that are the same.
    """
    representative_stack_trace = models.TextField(
        help_text='''Stack trace representing this group.''',
        blank=True,
        default=''
    )

    fixed_in_houdini_build = models.CharField(
        help_text='''The Houdini build where this was fixed.''',
        default='',
        max_length=12
    )

    is_fixed = models.BooleanField(
        help_text='''Was the problem causing this crash fixed?''',
        default=False
    )

    def __unicode__(self):
        return "HoudiniCrashGroup(%s)" % self.representative_stack_trace

    class Meta:
        db_name = 'stats'

#-------------------------------------------------------------------------------

class HoudiniToolUsage(models.Model):
    """
    Represent the usage of Houdini Houdini Tools. Specifically the ones
    on the Shelf and the Tab Menu.
    """
                        
    stats_machine_config = models.ForeignKey(
        'stats_main.MachineConfig',
        help_text='''The machine config associated with the crash.''',
    )

    date = models.DateTimeField(
        help_text='''When was this tool used.'''
    )
    
    tool_name = models.CharField(
        help_text='''The name of the tool (Ex. torus, box).''',
        max_length=60
    )
    
    tool_creation_location = models.CharField(
        help_text='''The location where the tool was created 
                    (Ex. Object, Sop, Vop).''',
        max_length=20,
        blank=True,
        default=''
    )
    
    SHELF = 1
    VIEWER = 2           
    NETWORK = 3
    
    TOOL_CREATION_MODES = (
        (SHELF, "shelf"),
        (VIEWER, "viewer"),           
        (NETWORK, "network"),
    )
    
    tool_creation_mode = models.IntegerField(choices=TOOL_CREATION_MODES)
        
    count = models.PositiveIntegerField(
        default=0,
        help_text='''Number of times the tool was used.'''
    )
        
    is_builtin = models.BooleanField(
        help_text='''Is Houdini built-in tool?''',
        default=True
    )
    
    is_asset = models.BooleanField(
        help_text='''Is Houdini Asset?''',
        default=False
    )
        
    def __unicode__(self):
        return "HoudiniToolUsage(%s , %d)" % \
            (self.tool_name, self.count)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date', 'count')    
        db_name = 'stats'


#-------------------------------------------------------------------------------

class HoudiniUsageCount(models.Model):
    """
    Model to represent houdini usage keys different from the tools.
    """
    
    stats_machine_config = models.ForeignKey(
        'stats_main.MachineConfig',
        help_text='''The machine config associated with the counts.''',
    )
    
    date = models.DateTimeField(
        help_text='''Date to record the key.'''
    )
        
    key = models.CharField(
        help_text='''The key.''',
        max_length=100
    )
            
    count = models.PositiveIntegerField(
        default=0,
        help_text='''Number of times the key was used.'''
    )
        
    def __unicode__(self):
        return "HoudiniUsageCounts(%s, %s)" % \
            (self.key, self.stats_machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date','count')    
        db_name = 'stats'        

#-------------------------------------------------------------------------------

class HoudiniSumAndCount(models.Model):
    """
    Model to represent sums and counts.
    """
    
    stats_machine_config = models.ForeignKey(
        'stats_main.MachineConfig',
        help_text='''The machine config associated with the sum and count.''',
    )
    
    date = models.DateTimeField(
        help_text='''Date to record the sum and count.'''
    )
        
    key = models.CharField(
        help_text='''The key.''',
        max_length=100
    )
            
    sum = models.FloatField(
        help_text='''Sum.''',
    )
    
    count = models.PositiveIntegerField(
        default=0,
        help_text='''Count.'''
    )
        
    def __unicode__(self):
        return "HoudiniSumAndCount(%s, %s)" % \
            (self.key, self.stats_machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date',)    
        db_name = 'stats'        
        
#-------------------------------------------------------------------------------

class HoudiniFlag(models.Model):
    """
    Model to represent houdini flags.
    """

    stats_machine_config = models.ForeignKey(
        'stats_main.MachineConfig',
        help_text='''The machine config associated with the flag.''',
    )
    
    date = models.DateTimeField(
        help_text='''Date to record the flag.'''
    )
        
    key = models.CharField(
        help_text='''The key.''',
        max_length=100
    )
    
    def __unicode__(self):
        return "HoudiniFlags(%s, %s)" % \
            (self.key, self.stats_machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date',)    
        db_name = 'stats'        


#-------------------------------------------------------------------------------

class HoudiniLog(models.Model):
    """
    Model to represent houdini logs.
    """
    
    stats_machine_config = models.ForeignKey(
        'stats_main.MachineConfig',
        help_text='''The machine config associated with the log.''',
    )
    
    date = models.DateTimeField(
        help_text='''Date to record the log.'''
    )
        
    key = models.CharField(
        help_text='''The key.''',
        max_length=100
    )
    
    timestamp = models.FloatField(
        help_text='''Timestamp.''',
    )
    
    log_entry = models.CharField(
        help_text='''Log Entry.''',
        max_length=100
    )
    
    def __unicode__(self):
        return "HoudiniLog(%s, %s)" % \
            (self.key, self.stats_machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date',)    
        db_name = 'stats'            
#-------------------------------------------------------------------------------

class Uptime(models.Model):
    """
    Represent the uptime of a machine using houdini.
    """

    stats_machine_config = models.ForeignKey(
        'stats_main.MachineConfig',
        help_text='''The machine config associated with the crash.''',
    )

    date = models.DateTimeField(
        help_text='''Date to record the uptime.'''
    )
    
    number_of_seconds = models.PositiveIntegerField(
        default=0,
        help_text='''Number of seconds houdini was used.'''
    )
    
    idle_time= models.PositiveIntegerField(
        default=0,
        help_text='''Number of seconds houdini was open but inactive.'''
    )
        
    def __unicode__(self):
        return "Uptime(%s, %d, %s)" % \
            (self.stats_machine_config.config_hash, self.number_of_seconds, self.date)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date','number_of_seconds')    
        db_name = 'stats'   
        

#-------------------------------------------------------------------------------

class HoudiniPersistentStats(models.Model):
    """
    Model to represent houdini persistent stats.
    """
    
    stats_machine_config = models.ForeignKey(
        'stats_main.MachineConfig',
        help_text='''The machine config associated with the persistent stats.''',
    )
    
    date = models.DateTimeField(
        help_text='''Date to record the log.'''
    )
        
    key = models.CharField(
        help_text='''The key.''',
        max_length=100
    )
    
    value = models.CharField(
        help_text='''The key.''',
        max_length=100
    )

    def __unicode__(self):
        return "HoudiniPersistentStats(%s, %s)" % \
            (self.key, self.stats_machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date',)    
        db_name = 'stats'                     
