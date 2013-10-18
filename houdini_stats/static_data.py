try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

top_menu_options = { "houdini":{ "menu_name": "Houdini", 
                                 "menu_view": "hou_reports",
                                 "menu_options": OrderedDict([
                                                    ("overview", "Overview"),
                                                    ("uptime", "Session Information"),
                                                    ("crashes", "Crashes"),                        
                                                    ("node_usage", "Node Usage"),
                                                    ("versions_and_builds", "Versions and builds"),
                                                ])  
                                }, 
                     "licensing": { "menu_name": "Licensing",
                                    "menu_view": "hou_licenses",
                                    "menu_options": OrderedDict([("apprentice_activations", "Apprentice Activations")])
                                   },
                     "surveys": { "menu_name": "Surveys",
                                  "menu_view": "hou_surveys",
                                  "menu_options": OrderedDict([("sidefx_labs", "labs.sidefx.com survey"),
                                                  ("apprentice_followup","Apprentice survey")])
                                 },
                     "sidefx.com": { "menu_name": "Website",
                                     "menu_view": "hou_forum",
                                     "menu_options": OrderedDict([("login_registration", "Login & Registration")])
                                    }
                    }

top_menu_options_ordered = (top_menu_options["houdini"],
                            top_menu_options["licensing"],
                            top_menu_options["surveys"],
                            top_menu_options["sidefx.com"])


