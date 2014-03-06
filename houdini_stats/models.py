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
        max_length=40,
        default=''
    )
        
    def __unicode__(self):
        return "Machine(%s)" % (self.hardware_id)

    class Meta:
        # How to order results when doing queries:
        db_name = 'stats'

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
        max_length=40
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
    
    def __unicode__(self):
        return "MachineConfig(%s, %s)" % (
            self.machine.hardware_id, self.config_hash)

    class Meta:
        # How to order results when doing queries:
        ordering = ('creation_date', )
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

class NodeTypeUsage(models.Model):
    """
    Represent the usage of Houdini Node Types.
    """
                        
    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine config associated with the node type used.''',
    )

    date = models.DateTimeField(
        help_text='''When this node type was used.'''
    )
    
    node_type = models.CharField(
        help_text='''The type of the node (Vops, Sops).''',
        max_length=60
    )
    
    SHELF = 1
    VIEWER = 2           
    NETWORK = 3
    
    NODE_CREATION_MODES = (
        (SHELF, "shelf"),
        (VIEWER, "viewer"),           
        (NETWORK, "network"),
    )
    
    node_creation_mode = models.IntegerField(choices=NODE_CREATION_MODES)
        
    count = models.PositiveIntegerField(
        default=0,
        help_text='''Number of times the node was used.'''
    )
        
    is_builtin = models.BooleanField(
        help_text='''Is Houdini built-in node?''',
        default=True
    )
    
    is_asset = models.BooleanField(
        help_text='''Is Houdini Asset?''',
        default=False
    )
        
    def __unicode__(self):
        return "NodeTypeUsage(%s , %d)" % \
            (self.node_type, self.count)

    class Meta:
        # How to order results when doing queries:
        ordering = ('date', )    
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

