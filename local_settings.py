STATS_APPLICATIONS += (
    "houdini_stats",
)

REPORT_MODULES += (
     'houdini_stats.reports.houdini',
)

menu_and_report_options = OrderedDict([
    ("houdini", {
        "menu_url_prefix": "houdini",
        "menu_name": "Houdini",
        "menu_options": [
            ("usage", "Usage", [
                "NewMachinesOverTime",
                "MachinesActivelySendingStats",
                "AvgNumConnectionsFromSameMachine",
            ]),
            ("uptime", "Session Information", [
                "AverageSessionLength",
                "AverageUsageByMachine",
                "BreakdownOfApprenticeUsage",
            ]),
            ("crashes", "Crashes",[
                "NumCrashesOverTime",
                "NumOfMachinesSendingCrashesOverTime",
                "AvgNumCrashesFromSameMachine",
                "CrashesByOS",
                "CrashesByProduct",
            ]),
            ("tools_usage", "Shelf & Tab menu Tools", [
                "MostPopularTools",
                "MostPopularToolsShelf",
                "MostPopularToolsViewer",
                "MostPopularToolsNetwork",
            ]),
            ("versions_and_builds", "Versions and builds",[
                "VersionsAndBuilds",
                "VersionsAndBuildsApprentice",
                "VersionsAndBuildsCommercial",
            ]),
        ],
        "groups": ['staff', 'r&d'],
    }),                        
])
   
TOP_MENU_OPTIONS = OrderedDict(TOP_MENU_OPTIONS.items() + \
                               menu_and_report_options.items())                            