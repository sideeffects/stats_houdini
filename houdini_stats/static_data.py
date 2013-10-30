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
                     "licensing": { "menu_name": "Downloads & Licensing",
                                    "menu_view": "hou_licenses",
                                    "menu_options": OrderedDict([("downloads", "Houdini Downloads"),
                                                                ("apprentice_activations", "Apprentice Activations")])
                                   },
                     "surveys": { "menu_name": "Surveys",
                                  "menu_view": "hou_surveys",
                                  "menu_options": OrderedDict([("sidefx_labs", "labs.sidefx.com survey"),
                                                  ("apprentice_followup","Apprentice survey")])
                                 },
                     "sidefx.com": { "menu_name": "Website",
                                     "menu_view": "hou_forum",
                                     "menu_options": OrderedDict([("login_registration", "Login & Registration"),
                                                                  ])
                                    },
                     
                     "orbolt": { "menu_name": "Orbolt",
                                  "menu_view": "hou_orbolt",
                                  "menu_options": OrderedDict([])
                                    }
                    }

top_menu_options_ordered = (top_menu_options["houdini"],
                            top_menu_options["licensing"],
                            top_menu_options["surveys"],
                            top_menu_options["sidefx.com"])

top_menu_options_nexts_prevs = {
                             "overview": {"next": "uptime", "prev": ""},
                             "uptime": {"next": "crashes", "prev": "overview"},
                             "crashes": {"next": "node_usage", "prev":"uptime"},
                             "node_usage": {"next": "versions_and_builds",
                                            "prev": "crashes"},
                             "versions_and_builds": {"next": "",
                                                     "prev": "node_usage"},   
                            
                            "downloads": {"next": "apprentice_activations", "prev": ""},
                            "apprentice_activations": {"next": "", "prev": "downloads"},
                            
                            "sidefx_labs": {"next": "apprentice_followup",
                                            "prev": ""},
                            "apprentice_followup": {"next": "",
                                                    "prev": "sidefx_labs"},
                                
                            "login_registration": {"next": "", "prev": ""},
                            
                                 
                      }