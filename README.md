stats_houdini
=============

Houdini-specific statistics data collection and reporting system, as an add-on to stats_core

The stats_houdini package comes with a default horizontal menu and a set of already made reports. But you can easily extend or modify the menus and add reports if you want. 


+ **How to extend or modify menus?**

The default menu is divided by report categories based on the information we collect from Houdini. You can extend/modify the default menu layout by changing the configuration of the Ordered Dictionary 'menu_and_report_options' in local_settings.py

The generic estructure of the menu_and_report_options Dictionary is:

```python
menu_and_report_options = OrderedDict([
    ("menu_internal_name", {
        "menu_url_prefix": "menu_url",
        "menu_name": "Menu Display Name",
        "menu_image": "menu_image_file_name", # Image to be shown in Home page. 
                                              # This image must be saved first 
                                              # in stats_core/stats_main/static
                                              # /images  
        "menu_description": '''Brief description of the menu and reports in it.''',
        
        # Menu options and reports (below some examples)
        "menu_options": [
            ("option_internal_name", "Option Display Name", [
                "ReportName1",
                "ReportName2",
                ..............
                "ReportNameN",
            ]),
           # ... more menu options withe te same format
        ],
        # Which user grouod can access the reports in the current menu
        "groups": ['staff', 'r&d'],
    }),  
    
  # ... more menus with the same format above ...
])

```

+ **How to create new reports?**

The package gives you a set of more than 15 already made reports. Each report is implemented as a python class which inherit from one of the two main report generic classes, _ChartReport_ or _HeatMapReport_, both implemented in stats_core/stats_main/genericreportclasses.py.

......To be continued









