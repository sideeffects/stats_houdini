from django.db import models

class MachineConfig(models.Model):
    """
    Represent a particular machine configuration.
    """
    
    hardware_id = models.IntegerField(
        help_text='''Hardware id.''',
        default=0
    )
    
    ip_address = models.CharField(
        help_text='''IP address.''',
        max_length=25,
        blank=True,
    )

    last_active_date = models.DateTimeField(
        help_text='''When this machine config was last updated.'''
    )
    
    config_hash = models.CharField(
        help_text='''Hash of the field below.''',
        max_length=40
    )    
    # From this point on the information related to the fields will be in the 
    # hash
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
        max_length=20,
        blank=True,
    )
    
    is_apprentice = models.BooleanField(
        help_text='''Is the product Houdini Apprentice??''',
        default=False
    )
    
    graphics_card = models.CharField(
        help_text='''Graphic card used in the current machine.''',
        max_length=20,
        blank=True,                               
    )
    
    graphics_card_vendor = models.CharField(
        help_text='''Graphic card vendor.''',
        max_length=20,
        blank=True,                               
    )
    
    operating_system = models.CharField(
        help_text='''Operating System installed in the machine.''',
        max_length=20 ,
        blank=True,                              
    )

    system_memory = models.FloatField(
        help_text='''System memory.''',
        default=0,
        blank=True,
    )
    
    system_resolution = models.CharField(
        help_text='''System resolution.''',
        max_length=10,
        blank=True,
    )
    
    number_of_processors = models.PositiveIntegerField(
        help_text='''Number of processors the machine has.''',
        default=0,
        blank=True,
        
    )
                        
    cpu_info = models.CharField(
        help_text='''CPU information.''',
        max_length=10,
        blank=True,
                                       
    )
    
    def __unicode__(self):
        return "MachineConfig( %s, %s)" % (self.hardware_id, self.config_hash)
    
    class Meta:
        '''How to order results when doing queries.'''
        ordering = ('last_active_date', )
            
#-------------------------------------------------------------------------------
    
class HoudiniCrash(models.Model):
    """
    Represent a Houdini Crash.
    """
                        
    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine associated with the crash.''',
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
        max_length=10
    )
    
    def __unicode__(self):
        return "HoudiniCrash(%s)" % \
            (self.stack_trace)

    class Meta:
        '''How to order results when doing queries.'''
        ordering = ('date', )

#-------------------------------------------------------------------------------

class NodeTypeUsage(models.Model):
    """
    Represent the usage of Houdini Node Types.
    """
                        
    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine associated with the node type used.''',
    )

    date = models.DateTimeField(
        help_text='''When this node type was used.'''
    )
    
    node_type = models.CharField(
        help_text='''The type of the node (Vops, Sops).''',
        max_length=20
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
        help_text='''Is the node a built-in Houdini node??''',
        default=True
    )
    
    is_asset = models.BooleanField(
        help_text='''Is the node a 3D Asset??''',
        default=False
    )
        
    def __unicode__(self):
        return "NodeTypeUsage(%s , %d)" % \
            (self.node_type, self.count)

    class Meta:
        '''How to order results when doing queries.'''
        ordering = ('date', )    

#-------------------------------------------------------------------------------

class Uptime(models.Model):
    """
    Represent the uptime of a machine using houdini.
    """
                        
    machine_config = models.ForeignKey(
        'MachineConfig',
        help_text='''The machine associated with the uptime.''',
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
        '''How to order results when doing queries.'''
        ordering = ('date','number_of_seconds')    
        
    
    
    

    