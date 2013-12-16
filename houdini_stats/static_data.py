try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

top_menu_options = OrderedDict([
    ("houdini", {
        "menu_name": "Houdini",
        "menu_view": "hou_reports",
        "menu_options": OrderedDict([
            ("downloads", "Houdini Downloads"),                         
            ("usage", "Usage"),
            ("uptime", "Session Information"),
            ("crashes", "Crashes"),
            ("node_usage", "Node Usage"),
            ("versions_and_builds", "Versions and builds"),
        ]),
    }),
                                
    ("apprentice", {
        "menu_name": "Apprentice",
        "menu_view": "hou_apprentice",
        "menu_options": OrderedDict([
            ("apprentice_activations", "Apprentice Activations"),
            ("apprentice_hd", "Apprentice HD"),
            ("apprentice_heatmap", "Apprentice Activations Heatmap"),
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

])

