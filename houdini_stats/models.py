from django.db import models
import django.db.models.options as options

# Keep django from complaining about the db_name meta attribute.
if "db_name" not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + ("db_name",)
    

class Machine(models.Model):
    """
    Represent a unique machine.
    """    
    
    hardware_id = models.CharField(
        help_text='''Mac address hash.''',
        max_length=80,
        default=''
    )
        
    def __unicode__(self):
        return "Machine(%s)" % (self.hardware_id)

    class Meta:
        # How to order results when doing queries:
        db_name = 'stats'

#-------------------------------------------------------------------------------

class MachineConfig(models.Model):
    """
    Represent a particular configuration for a machine.
    """

    machine = models.ForeignKey(
        'Machine',
        help_text='''The machine associated with this machine config.''',
    )

    creation_date = models.DateTimeField(
        help_text='''When this machine config was created.''',
        auto_now_add=True,
    )

    config_hash = models.CharField(
        help_text='''Hash of the information from the user machine.''',
        max_length=80
    )    
    
    ip_address = models.CharField(
        help_text='''IP address.''',
        max_length=25,
        blank=True,
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
    
    graphics_card = models.CharField(
        help_text='''Graphic card used in the current machine.''',
        max_length=40,
        blank=True,                               
    )
    
    graphics_card_version = models.CharField(
        help_text='''Graphic card version.''',
        max_length=40,
        blank=True,                               
    )
    
    operating_system = models.CharField(
        help_text='''Operating System installed in the machine.''',
        max_length=40,
        blank=True,                              
    )

    system_memory = models.FloatField(
        help_text='''System memory.''',
        default=0,
        blank=True,
    )
    
    system_resolution = models.CharField(
        help_text='''System resolution.''',
        max_length=20,
        blank=True,
    )
    
    number_of_processors = models.PositiveIntegerField(
        help_text='''Number of processors the machine has.''',
        default=0,
        blank=True,
        
    )
                        
    cpu_info = models.CharField(
        help_text='''CPU information.''',
        max_length=20,
        blank=True,
                                       
    )
    
    raw_user_info = models.TextField(
        help_text='''All the machine info data that was sent from Houdini.''',
        blank=True,
        default=''
    )
    
    def __unicode__(self):
        return "MachineConfig(%s, %s)" % (
            self.machine.hardware_id, self.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('creation_date', )
        db_name = 'stats'
            
#-------------------------------------------------------------------------------

class LogId(models.Model):
    """
    LogId to identify which stats have been already saved in the db and not
    save the same info more than once.
    """
    
    log_id = models.CharField(
        help_text='''Lod id.''',
        max_length=80
    )  

    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine config associated with this log.''',
    )

    logging_date = models.DateTimeField(
        help_text='''When this particular log was saved.''',
        auto_now_add=True,
    )
    
    def __unicode__(self):
        return "LogId(%s, %s)" % (
            self.log_id, self.machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('logging_date',)
        db_name = 'stats'
            
#-------------------------------------------------------------------------------
    
class HoudiniCrash(models.Model):
    """
    Represent a Houdini Crash.
    """
    
    machine_config = models.ForeignKey(
        'MachineConfig',
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
    
    def __unicode__(self):
        return "HoudiniCrash(%s)" % self.stack_trace

    class Meta:
        # How to order results when doing queries:
        ordering = ('date', )
        db_name = 'stats'

#-------------------------------------------------------------------------------

class HoudiniToolUsage(models.Model):
    """
    Represent the usage of Houdini Houdini Tools. Specifically the ones
    on the Shelf and the Tab Menu.
    """
                        
    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine config associated with the tool type used.''',
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

    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine config associated with the key.''',
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
            (self.key, self.machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date','count')    
        db_name = 'stats'        
    

#-------------------------------------------------------------------------------

class HoudiniUsageFlag(models.Model):
    """
    Model to represent houdini usage flags.
    """

    machine_config = models.ForeignKey(
        'MachineConfig',
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
        return "HoudiniUsageFlags(%s, %s)" % \
            (self.key, self.machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date',)    
        db_name = 'stats'        


#-------------------------------------------------------------------------------

class HoudiniUsageLog(models.Model):
    """
    Model to represent houdini usage logs.
    """
    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine config associated with the log.''',
    )
    
    date = models.DateTimeField(
        help_text='''Date to record the log.'''
    )
        
    key = models.CharField(
        help_text='''The key.''',
        max_length=100
    )
    
    message = models.TextField(
        help_text='''Message for the log.''',
        default=''
    )
            
    def __unicode__(self):
        return "HoudiniUsageLog(%s, %s)" % \
            (self.key, self.machine_config.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date',)    
        db_name = 'stats'            
#-------------------------------------------------------------------------------

class Uptime(models.Model):
    """
    Represent the uptime of a machine using houdini.
    """

    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine config associated with the uptime.''',
    )

    date = models.DateTimeField(
        help_text='''Date to record the uptime.'''
    )
    
    number_of_seconds = models.PositiveIntegerField(
        default=0,
        help_text='''Number of seconds houdini was used.'''
    )
        
    def __unicode__(self):
        return "Uptime(%s, %d, %s)" % \
            (self.machine_config.config_hash, self.number_of_seconds, self.date)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date','number_of_seconds')    
        db_name = 'stats'
     

#-------------------------------------------------------------------------------

class Event(models.Model):
    """
    Represent an Event that will be used to annotate specific dates in the
    reports.
    """
    
    title = models.CharField(
        help_text='''The title of the event.''',
        max_length=40
    )   
    
    date = models.DateTimeField(
        help_text='''Date when the event took place.'''
    )
    
    description = models.TextField(
        help_text='''Brief Description of the event.''',
        blank=True,
        default=''
    ) 
    
    show = models.BooleanField(
        help_text='''To hide or show an event from the graphs''',
        default=False
    )
        
    def __unicode__(self):
        return "Event(%s, %s)" % \
            (self.title, self.date)
        
    class Meta:
        # How to order results when doing queries:
        ordering = ('date',)    
        db_name = 'stats'

