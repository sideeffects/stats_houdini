from settings import * 

STATS_APPLICATIONS += (
    "houdini_stats",
)

REPORT_MODULES += (
     'houdini_stats.reports.houdini',
)

# SESI internal machines ip patterns
# You can modify this to have your own internal machines patterns
IP_PATTERNS = ["192.168.%%", "10.1.%%"]

# Default layout - horizontal menu by reports category 
menu_and_report_options = OrderedDict([
    ("usage", {
        "menu_url_prefix": "usage",
        "menu_name": "Houdini Usage",
        "menu_image": "",
        "menu_description": '''Set of reports for Houdini Usage. Examples of them
                            are the Number of Machine subscribed and the Number
                            of Machines sending stats.''',
        "menu_options": [
            ("usage_overview", "Usage Overview", [
                "NewMachinesOverTime",
                "MachinesActivelySendingStats",
                "AvgNumConnectionsFromSameMachine",
                 "InternalMachinesSendingStatsByOS",
                 "ExternalMachinesSendingStatsByOS",
            ]),
            
            ("tools_usage", "Shelf & Tab Tools usage", [
                "MostPopularTools",
                "MostPopularToolsShelf",
                "MostPopularToolsViewer",
                "MostPopularToolsNetwork",
            ]),
        ],
        "groups": ['staff', 'r&d'],
    }),  
     ("session_information", {
        "menu_url_prefix": "session_information",
        "menu_name": "Session Information",
        "menu_image": "",
        "menu_description":'''Set of reports for Houdini Session Information.
                            Examples of them are the Average Session Length and
                            the Average Usage by Machine.''',
        "menu_options": [
            ("uptimes_overview", "Uptimes Overview", [
                "AverageSessionLength",
                "AverageUsageByMachine",
                 
            ]),             
            ("uptimes_apprentice", "Apprentice Uptimes", [
                "BreakdownOfApprenticeUsage",
            ]),
        ],
        "groups":['staff', 'r&d'],
    }),
    ("crashes", {
        "menu_url_prefix": "crashes",
        "menu_name": "Crashes",
        "menu_image": "",
        "menu_description":'''Set of reports for Houdini Crashes.
                            Examples of them are the Number of Crashes over Time
                            and Average Crashes from the same Machine.''',
        "menu_options": [
            ("crashes_overview", "Crashes Overview", [
                "NumCrashesOverTime",
                "NumOfMachinesSendingCrashesOverTime",
                "AvgNumCrashesFromSameMachine",                
            ]),             
            ("crashes_by_os", "Crashes by OS", [
                "CrashesByOS",
            ]),
            ("crashes_by_product", "Crashes by Product",[
                "CrashesByProduct",
            ]),
        ],
        "groups":['staff', 'r&d'],
    }),
    ("versions_and_builds", {
        "menu_url_prefix": "versions_and_builds",
        "menu_name": "Versions and Builds",
        "menu_image": "",
        "menu_description":'''Set of reports for Houdini Versions and Builds.
                            Mainly pie charts reportst.''',
        "menu_options": [
            ("versions_and_builds_overview", "Overview", [
                "VersionsAndBuilds",
                "VersionsAndBuildsApprentice",
                "VersionsAndBuildsCommercial",            
            ]),             
        ],
        "groups":['staff', 'r&d'],
    }),                                                   
])

# Dropdown list menu layout - best options when you have many apps using the
# same stats system. Preferred option for sesi internal reports.
# menu_and_report_options = OrderedDict([
#     ("houdini", {
#         "menu_url_prefix": "houdini",
#         "menu_name": "Houdini",
#         "menu_image": "houdini.png", # default image
#         "menu_description": '''Graphic reports from data being collected 
#                                from inside Houdini.''', # default text
#         # Menu options and reports
#         "menu_options": [
#             ("usage", "Usage", [
#                 "NewMachinesOverTime",
#                 "MachinesActivelySendingStats",
#                 "AvgNumConnectionsFromSameMachine",
#                 "InternalMachinesSendingStatsByOS",
#                 "ExternalMachinesSendingStatsByOS",
#             ]),
#             ("uptime", "Session Information", [
#                 "AverageSessionLength",
#                 "AverageUsageByMachine",
#                 "BreakdownOfApprenticeUsage",
#             ]),
#             ("crashes", "Crashes",[
#                 "NumCrashesOverTime",
#                 "NumOfMachinesSendingCrashesOverTime",
#                 "AvgNumCrashesFromSameMachine",
#                 "CrashesByOS",
#                 "CrashesByProduct",
#             ]),
#             ("tools_usage", "Shelf & Tab menu Tools", [
#                 "MostPopularTools",
#                 "MostPopularToolsShelf",
#                 "MostPopularToolsViewer",
#                 "MostPopularToolsNetwork",
#             ]),
#             ("versions_and_builds", "Versions and builds",[
#                 "VersionsAndBuilds",
#                 "VersionsAndBuildsApprentice",
#                 "VersionsAndBuildsCommercial",
#             ]),
#         ],
#         "groups": ['staff', 'r&d'],
#     }),                        
# ])
   
TOP_MENU_OPTIONS = OrderedDict(TOP_MENU_OPTIONS.items() + \
                               menu_and_report_options.items())                            
