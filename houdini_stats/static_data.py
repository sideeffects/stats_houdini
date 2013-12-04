try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

top_menu_options = OrderedDict([
    ("houdini", {
        "menu_name": "Houdini",
        "menu_view": "hou_reports",
        "menu_options": OrderedDict([
            ("overview", "Overview"),
            ("uptime", "Session Information"),
            ("crashes", "Crashes"),
            ("node_usage", "Node Usage"),
            ("versions_and_builds", "Versions and builds"),
        ]),
    }),
    ("licensing", {
        "menu_name": "Downloads & Licensing",
        "menu_view": "hou_licenses",
        "menu_options": OrderedDict([
            ("downloads", "Houdini Downloads"),
            ("apprentice_activations", "Apprentice Activations"),
            ("apprentice_hd", "Apprentice HD"),
        ]),
    }),
    ("surveys", {
        "menu_name": "Surveys",
        "menu_view": "hou_surveys",
        "menu_options": OrderedDict([
            ("sidefx_labs", "labs.sidefx.com survey"),
            ("apprentice_followup","Apprentice survey"),
        ]),
    }),
    ("sidefx.com", {
        "menu_name": "Website",
        "menu_view": "hou_forum",
        "menu_options": OrderedDict([
            ("login_registration", "Login & Registration"),
        ]),
    }),
#                                
#    ("orbolt", {
#        "menu_name": "Orbolt",
#        "menu_view": "hou_orbolt",
#        "menu_options": OrderedDict([
#        ]),
#    }),
])

