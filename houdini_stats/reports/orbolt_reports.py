from houdini_stats.genericreportclasses import *
from orbolt.models import *

from decimal import *
from datetime import datetime
from django.db.models import Avg, Sum, Count
from collections import defaultdict
import httpagentparser

import houdini_stats.utils             
import houdini_stats.time_series 

#===============================================================================

@cacheable
def get_user(username):
    return AuthUser.objects.get(username=username)

#-------------------------------------------------------------------------------
@cacheable
def get_right(right_name):
    return StoreRight.get(right_name)

#===============================================================================

# Orbolt Overview Reports
    
class RevenueOverTime(ChartReport):
    """
    Revenue from Asset sells. Wide Area Chart.
    """
    
    def name(self):
        return "revenue_from_sales"

    def title(self):
        return "Revenue from Houdini Assets Sales"

    def get_data(self, series_range, aggregation):
        return get_orm_data_for_report(StoreLicense.objects.filter(
                                       invoice__isnull=False), 'created', 
                                       series_range, aggregation,
                                       func=Sum('asset_price__price'))
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Total Revenue $" %}{{ val }}{% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_area_wide"'      
    
#-------------------------------------------------------------------------------
class PurchasesOverTime(ChartReport):
    """
    Asset purchases overtime. Wide Area Chart.
    """
    
    def name(self):
        return "purchases_overtime"

    def title(self):
        return "Houdini Assets Sales"

    def get_data(self, series_range, aggregation):
        return get_orm_data_for_report(StoreLicense.objects.exclude(
                   asset_price__price=Decimal(0)), 'created', series_range,
                                                                   aggregation)
        
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Purchases" %}{{ val }}{% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_area_wide"'
    
#-------------------------------------------------------------------------------

class NewUploadsOverTime(ChartReport):
    """
    New asset uploads overtime. Wide Area Chart.
    """
        
    def name(self):
        return "new_uploads_overtime"

    def title(self):
        return "New Asset Uploads"

    def get_data(self, series_range, aggregation):
        
        return get_orm_data_for_report(StoreAssetversion.objects.filter(
                      sequence_number=0), 'created', series_range, aggregation)
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Uploads" %}{{ val }}{% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_area_wide"'    
    
#-------------------------------------------------------------------------------
    
class NewVersionsOfExistingAssets(ChartReport):
    """
    New versions of existing assets. Wide Area Chart.
    """
    
    def name(self):
        return "new_versions_existing_assets"

    def title(self):
        return "New Versions of Existing Assets"

    def get_data(self, series_range, aggregation):
        return get_orm_data_for_report(StoreAssetversion.objects.filter(
                    sequence_number__gt=0), 'created',series_range, aggregation)
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "new versions" %}{{ val }}{% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_area_wide"'    

#-------------------------------------------------------------------------------
   
class NewUsersOverTime(ChartReport):
    """
    New Orbolt users overtime. Wide Area Chart.
    """
        
    def name(self):
        return "new_users_overtime"

    def title(self):
        return "New Users Subscribed"

    def get_data(self, series_range, aggregation):
        return get_orm_data_for_report(AuthUser.objects.all(), 'date_joined', 
                                                     series_range, aggregation)
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Users" %}{{ val }}{% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_area_wide"'
            

#-------------------------------------------------------------------------------
   
class OSAndBrowserCombinations(ChartReport):
    """
    OS and browser combinations used in Orbolt. Pie Charts.
    """  
    def name(self):
        return "os_and_browser_combinations"

    def title(self):
        return "Operating Systems and Browsers Combinations for Orbolt users"
    
    def get_data(self, series_range, aggregation):
        """
        Data to build 2 Pie Charts:
        
        1. With the % of the licenses by Operating System.
        2. With the % of the licenses by Operating System and Browser 
        combinations.
        """
        
        licenses_with_user_agent =  StoreLicense.objects.exclude(user_agent="")
        lic_count = licenses_with_user_agent.count()
         
        dict_os_brow_values, dict_os_values = self._get_dict_os_and_browsers(
                                                       licenses_with_user_agent)
        
        
        return [self._get_os_browser_combinations_trans(dict_os_brow_values, 
                                                                    lic_count),
                     self._get_os_combinations_trans(dict_os_values, lic_count)] 
    
    def _get_dict_os_and_browsers(self, licenses):
        """
        Get the dictionaries with os and os and values combinations to be used 
        in the Pie Charts.
        """
        dict_os_brow_values = defaultdict(int)
        dict_os_values = defaultdict(int)
       
        for license in licenses:
            user_agent = license.user_agent
            info = httpagentparser.detect(user_agent)
            
            if 'browser' in info.keys() and 'os' in info.keys():
                browser = info['browser']['name']
                os = info["os"]["name"]
                
                combination =  os + ", " + browser
                dict_os_values[os] += 1
                dict_os_brow_values[combination] += 1
    
        return dict_os_brow_values, dict_os_values
        
    def _get_os_browser_combinations_trans(self, dict_os_brow_values, lic_count): 
        """ 
        OS and browsers combinations
        """
        os_browsers_values = [[platform, count] for platform, count in
                                         dict_os_brow_values.iteritems()]
    
        total_agents = sum(v[1] for v in os_browsers_values)
        other = lic_count - total_agents
        os_browsers_values.append(["Other", other])
        
        return os_browsers_values   
    
    def _get_os_combinations_trans(self, dict_os_values, lic_count):
        """ 
        OS combinations
        """
        os_values = [[platform, count] for platform, count in 
                                             dict_os_values.iteritems()]
        os_total = sum(v[1] for v in os_values)
        os_other = lic_count - os_total
        os_values.append(["Other", os_other])
        
        return os_values
            
    def chart_columns(self):
        return """
        {% col "string" "Name" %}"{{ val }}"{% endcol %}
        {% col "number" "Value" %}{{ val }}{% endcol %}
       """
    
    def chart_options(self):
        return '"out_options"'
    
    def chart_count(self):
        return 2    

#-------------------------------------------------------------------------------
   
class PercentageLicensesByCommercialAndApprentice(ChartReport):
    """
    Orbolt licenses by Houdini version, for Commercial or
    Apprentice. Pie Charts.
    """  
    def name(self):
        return "percentage_lic_by_hou_version_combinations"

    def title(self):
        return '''Percentage of Orbolt licenses for Houdini Commercial and
        Apprentice'''
    
    def get_data(self, series_range, aggregation):
        dict_values_app = defaultdict(int)
        for license in StoreLicense.objects.all():
            houdini_version = license.houdini_version
    
            try:
                if license.is_apprentice == True:
                    combination = "Apprentice, Houdini " + houdini_version
                else:
                    combination = "Commercial, Houdini " + houdini_version
    
                dict_values_app[combination] += 1
            except TypeError:
                pass    
        
        return [[houdini, count] for houdini, count in dict_values_app.iteritems()] 
    
    def chart_columns(self):
        return """
        {% col "string" "Name" %}"{{ val }}"{% endcol %}
        {% col "number" "Value" %}{{ val }}{% endcol %}
       """
    
    def chart_options(self):
        return '"out_options"'

#===============================================================================
# Licenses related reports

@cacheable
def _get_licenses(downloaded=None, os_name=None):
    """
    Get all the licenses, and take into account the downloaded field if a value
    is passed.
    """
    queryset = (StoreLicense.objects
        .exclude(right__abbrev="creator", owner=get_user("admin"))
        .exclude(owner=get_user("SideFX")))

    if downloaded is not None and os_name is not None:
        # Both filters are not None
        return queryset.filter(
            downloaded=downloaded, user_agent__contains=os_name)
    elif downloaded is not None:
        # Assumed then os_name is none otherwise will be case above 
        return queryset.filter(downloaded=downloaded)
    elif os_name is not None:
        # Assumed then downloaded is none otherwise will be first case 
        return queryset.filter(user_agent__contains=os_name)
    
    return queryset

#-------------------------------------------------------------------------------

def _get_queryset_sequences_for_licenses(os_name):
    """
    This function give us the queryset sequences with all the licenses 
    combinations we need, ready to pass to the function
    _get_time_series_sequences and build the sequence of time series needed for
    the reports. 
    """
    return [_get_licenses(os_name=os_name), 
            _get_licenses(downloaded=True, os_name=os_name),
            _get_licenses(downloaded=False, os_name=os_name)
       ]
#------------------------------------------------------------------------------- 

class LicensesOverTime(ChartReport):
    """
    Orbolt Asset Licenses Overtime. Line Chart.
    """
    
    def os_name(self):
        return None
    
    def name(self):
        return "licenses_over_time" 

    def title(self):
        return "Licenses Over time "

    def get_data(self, series_range, aggregation):
        """
        Get Orbolt licenses over time (All licenses, and licenses where the
        user successfully downloaded the asset, and licenses where the user never
        downloaded the asset inside Houdini for several reasons). An OS name can
        be passed as parameter. Line Chart.
        """
        return time_series.merge_time_series(
                   time_series.get_time_series_sequences(
                   _get_queryset_sequences_for_licenses(self.os_name()), 
                   series_range, aggregation))
    
    def chart_columns(self):
        return """
        {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
        {% col "number" "Total Licenses" %}{{ val }}{% endcol %}
        {% col "number" "Licenses and Asset succesfully downloaded" %}
            {{ val }}
        {% endcol %}
        {% col "number" "Licenses and asset not succesfully downloaded" %}
            {{ val }}
        {% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_with_legend_Red"' 
    
#-------------------------------------------------------------------------------

class PercentagesLicensesAssetNotDownloaded(ChartReport):
    """
    Get which percentage are the licenses with "downloaded" field in False from 
    the total amount of licenses generated over time. Column Chart.
    """
    
    def os_name(self):
        return None
    
    def name(self):
        return "percentages_licenses_not_asset_downloaded"

    def title(self):
        return '''Percentage of Licenses where the Asset wasn't 
               Succesfully Downloaded'''

    def get_data(self, series_range, aggregation):
        """
        Get which percentage are the licenses with "downloaded" field in False
        from the total amount of licenses generated over time. An OS name can be 
        passed as parameter. Column Chart.
        """  
        # time_series_sequences is a list that will have in the first position  
        # all the licenses, in the second one the licenses with downloaded field 
        # in True and the third one the list with download field in false.
        # For this reports we just need 1st and 3rd. 
        ts_all_lic, ts_lic_downloaded, ts_lic_not_downloaded = (
                               time_series.get_time_series_sequences(
                               _get_queryset_sequences_for_licenses(
                               self.os_name()), series_range, aggregation))
            
        return time_series.compute_time_series( [ts_lic_not_downloaded, 
                   ts_all_lic], houdini_stats.utils.get_percent)
    
    def chart_columns(self):
        return """
         {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
         {% col "number" "Percentage %" %} {{ val }}{% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_wide_columnRed"' 


#------------------------------------------------------------------------------- 

class LicensesOverTimeMacOs(LicensesOverTime):
    def os_name(self):
        return 'Macintosh'
    
    def name(self):
        return "licenses_over_time_mac_os" 

    def title(self):
        return "Licenses Over time (Mac OS) "
    
#-------------------------------------------------------------------------------

class PercentagesLicensesAssetNotDownloadedMacOs(
                                         PercentagesLicensesAssetNotDownloaded):
    def os_name(self):
        return 'Macintosh'
    
    def name(self):
        return "percentages_licenses_not_asset_downloaded_mac_os"

    def title(self):
        return '''Percentage of Licenses where the Asset wasn't 
               Succesfully Downloaded (Mac OS)'''

#------------------------------------------------------------------------------- 

class LicensesOverTimeWindows(LicensesOverTime):
    def os_name(self):
        return 'Windows'
    
    def name(self):
        return "licenses_over_time_windows" 

    def title(self):
        return "Licenses Over time (Windows) "
    
#-------------------------------------------------------------------------------

class PercentagesLicensesAssetNotDownloadedWindows(
                                         PercentagesLicensesAssetNotDownloaded):
    def os_name(self):
        return 'Windows'
    
    def name(self):
        return "percentages_licenses_not_asset_downloaded_windows"

    def title(self):
        return '''Percentage of Licenses where the Asset wasn't 
               Succesfully Downloaded (Windows)'''

#------------------------------------------------------------------------------- 

class LicensesOverTimeLinux(LicensesOverTime):
    def os_name(self):
        return 'Linux'
    
    def name(self):
        return "licenses_over_time_linux" 

    def title(self):
        return "Licenses Over time (Linux) "
    
#-------------------------------------------------------------------------------

class PercentagesLicensesAssetNotDownloadedLinux(
                                         PercentagesLicensesAssetNotDownloaded):
    def os_name(self):
        return 'Linux'
    
    def name(self):
        return "percentages_licenses_not_asset_downloaded_Linux"

    def title(self):
        return '''Percentage of Licenses where the Asset wasn't 
               Succesfully Downloaded (Linux)'''

#-------------------------------------------------------------------------------

class LicensesOverTimeByOs(ChartReport):
    """
    Orbolt Asset Licenses Overtime by Operating System. Line Chart.
    """
    
    def os_names(self):
        return ["Macintosh", "Windows", "Linux"]
    
    def name(self):
        return "licenses_over_time_by_os" 

    def title(self):
        return "Licenses Over time by OS"

    def get_data(self, series_range, aggregation):
        
        return time_series.merge_time_series(
                   time_series.get_time_series_sequences(
                   self.get_queryset_sequences_for_licenses_by_os(), 
                   series_range, aggregation))
    
    def get_queryset_sequences_for_licenses_by_os(self): 
        """
        This function give us the queryset sequences with all the licenses 
        by different os, ready to pass them to the function
        _get_time_series_sequences. 
        """
        return [_get_licenses(os_name=os_name) for os_name in self.os_names()]     
              
    def chart_columns(self):
        return """
         {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
            {% col "number" "Total Licenses on MAC" %}{{ val }}{% endcol %}
            {% col "number" "Total Licenses on Windows" %}{{ val }}{% endcol %}
            {% col "number" "Total Licenses on Linux" %}{{ val }}{% endcol %}
        """
    def chart_options(self):
        return '"opt_count_with_legend"' 
    
#-------------------------------------------------------------------------------

class PercentagesLicensesAssetNotDownloadedByOs(ChartReport):
    """
    Get which percentage are the licenses with "downloaded" field in False from 
    the total amount of licenses generated over time, by Operating System.
    Column Chart.
    """
    
    def os_name(self):
        return None
    
    def name(self):
        return "percentages_licenses_not_asset_downloaded_by_os"

    def title(self):
        return '''Percentage of Licenses where the Asset wasn't 
               Succesfully Downloaded (By OS)'''

    def get_data(self, series_range, aggregation):
        
        mac_os_percentages = PercentagesLicensesAssetNotDownloadedMacOs()
        windows_percentages = PercentagesLicensesAssetNotDownloadedWindows()
        linux_percentages = PercentagesLicensesAssetNotDownloadedLinux()
        
        return time_series.merge_time_series(
                        [mac_os_percentages.get_data(series_range, aggregation),
                        windows_percentages.get_data(series_range, aggregation),
                        linux_percentages.get_data(series_range, aggregation)
                        ])
    
    def chart_columns(self):
        return """
          {% col "string" "Date" %}"{{ val|date:date_format }}"{% endcol %}
          {% col "number" "% on Mac OS" %}{{ val }}{% endcol %}
          {% col "number" "% on Windows" %}{{ val }}{% endcol %}
          {% col "number" "% on Linux" %}{{ val }}{% endcol %}
        """
    
    def chart_options(self):
        return '"opt_count_with_legend"' 

#-------------------------------------------------------------------------------
# Licenses Heatmap

class AssetLicensesHeatmap(HeatMapReport):
    """
    Houdini Asset licenses in Orbolt. Heatmap.
    """  
    def name(self):
        return "orbolt_licenses_heatmap"

    def title(self):
        return "Orbolt Asset Licenses Locations"

    def get_data(self, series_range, aggregation):
                
        return [(license.lat, license.lon) for license in
                              StoreLicense.objects.exclude(lat=None, lon=None)]


#===============================================================================
# Tops Assets Reports

class TopAssets(ChartReport):
    """
    Orbolt Tops Assets. Column Chart.
    """
    def supports_aggregation(self):
        return False

    def show_date_picker(self):
        return False
    
    def max_num(self):
        '''
        Max num of elements to show on the chart
        '''
        return 20
    
    def chart_column2(self):
        return ""    
    
    def chart_columns(self):
        return '''
        {% col "string" "Asset" %}"{{ val.display_name}}"{% endcol %}
        {% col "number" "''' + self.chart_column2() + '''" %}{{ val }}
        {% endcol %}
        '''
#-------------------------------------------------------------------------------

class TopDownloadedAssets(TopAssets):
    """
    Top Downloaded Assets. Column Chart.
    """
    def name(self):
        return "top_downloaded_assets"

    def title(self):
        return "Top Downloaded Assets"
    
    def get_data(self, series_range, aggregation):
        
        return StoreAsset.get_most_downloaded_assets(num=self.max_num(), 
                                                     include_count=True)                
    def chart_column2(self):
        return "# of downloads"    
    
    def chart_options(self):
        return '"opt_count_wide_column"' 
    
#-------------------------------------------------------------------------------

class TopViewedAssets(TopAssets):
    """
    Top Viewed Assets. Column Chart.
    """
    def name(self):
        return "top_viewed_assets"

    def title(self):
        return "Top Viewed Assets"
    
    def get_data(self, series_range, aggregation):
        assets_by_views = StoreAsset.active_objects.all().order_by(
                                                      "-views")[:self.max_num()]
        return [[x, x.views] for x in assets_by_views]
                        
    def chart_column2(self):
        return "# of views"    
    
    def chart_options(self):
        return '"opt_count_wide_columnGreen"'     
    
#-------------------------------------------------------------------------------

class TopPaidAssets(TopAssets):
    """
    Top Paid Assets. Column Chart.
    """
    def name(self):
        return "top_paid_assets"

    def title(self):
        return "Top Paid Assets"
    
    def get_data(self, series_range, aggregation):
        return StoreAsset.get_most_downloaded_assets(num=self.max_num(), 
                                                include_count=True,
                                                include_free=False)
    def chart_column2(self):
        return "# of downloads"
        
    def chart_options(self):
        return '"opt_count_wide_columnYellow"'  
    
#-------------------------------------------------------------------------------

class TopGrossingAssets(TopAssets):
    """
    Top Grossing Assets. Column Chart.
    """
    def name(self):
        return "top_grossing_assets"

    def title(self):
        return "Top Grossing Assets"
    
    def get_data(self, series_range, aggregation):
        gross = defaultdict(int)
        for license in StoreLicense.objects.filter(invoice__isnull=False)\
                                       .exclude(asset_price__price=Decimal(0)):
            gross[license.asset] += license.asset_price.price

        return sorted(gross.iteritems(), key=lambda x:x[1], 
                      reverse=True)[:self.max_num()]
    
    def chart_column2(self):
        return "total revenue $"    
    
    def chart_options(self):
        return '"opt_count_wide_columnPurple"'            
    

#===============================================================================
# Pie Charts for Trial Licenses reports

@cacheable
def get_licenses_count(exclude_owner, filter_right=None, exclude_right=None):
    """
    This function is the equivalent of doing:
    
    trial_right = Right.get("trial")
    creator_right = Right.get("creator")
    apprentice_right = Right.get("apprentice")
    regular_right = Right.get("regular")

    licenses = License.objects.exclude(right=creator_right)\
                              .exclude(owner=admin)\
                              .count()

    trials = License.objects.exclude(owner=admin)\
                            .filter(right=trial_right)\
                            .count()

    app_only = License.objects.exclude(owner=admin)\
                               .filter(right=apprentice_right)\
                               .exclude(right=creator_right)\
                               .count()

    reg_only = License.objects.exclude(owner=admin)\
                               .filter(right=regular_right)\
                               .exclude(right=creator_right)\
                               .count()
    
    Depending on the parameters passed.
    
    """
    
    if exclude_right is not None and filter_right is None:
        # All licences where the user is different from exclude_owner and right
        # different from exclude_right
        return (StoreLicense.objects
                .exclude(right=exclude_right)
                .exclude(owner=exclude_owner)
                .count())
    elif filter_right is not None and exclude_right is None:
        # All licenses where the user is different from exclude_owner and right
        # is filter_right
        return (StoreLicense.objects
                .exclude(owner=exclude_owner)
                .filter(right=filter_right)
                .count())

    # All licenses where the user is different from exclude_owner and right
    # is filter_right but excluding exclude_right  
    return StoreLicense.objects.exclude(owner=exclude_owner)\
                               .filter(right=filter_right)\
                               .exclude(right=exclude_right)\
                               .count()

#-------------------------------------------------------------------------------

class Trials(ChartReport):
    """
    Trial Licesnes Reports. Pie Charts.
    """
    
    def supports_aggregation(self):
        return False

    def show_date_picker(self):
        return False
        
    def chart_columns(self):
        return """
         {% col "string" "Name" %}"{{ val }}"{% endcol %}
         {% col "number" "Value" %}{{ val }}{% endcol %}
        """
    
    def chart_options(self):
        
        return '"out_options_smaller"'   
    
#-------------------------------------------------------------------------------

class TrialLicensesOverview(Trials):
    """
    Trial Lisences Overview. Pie Charts.
    """ 
    
    admin = get_user("admin")
     
    def name(self):
        return "trial_licenses_overview"

    def title(self):
        return "Trial Licenses Overview (including exprired trials)"
    
    def get_data(self, series_range, aggregation):
        
        creator_r = get_right("creator")
    
        return [["Trials", get_licenses_count(self.admin, get_right("trial"))], 
           ["Apprentice", 
           get_licenses_count(self.admin, get_right("apprentice"), creator_r)],
           ["Regular", 
           get_licenses_count(self.admin, get_right("regular"), creator_r)]]
    
    def get_extra_data(self):
        """
        Function to add some extra data for the chart aditional information.
        """
        
        all_licenses_count = get_licenses_count(self.admin, filter_right=None, 
                                  exclude_right=get_right("creator"))
        trial_licenses_count = get_licenses_count(self.admin, 
                                        filter_right=get_right("trial"))        
        return all_licenses_count, trial_licenses_count
    
    def chart_aditional_information_above(self):
        all, trials = self.get_extra_data()
        num_active = StoreLicense.objects.exclude(owner=self.admin)\
                                .filter(right=StoreRight.get("trial"))\
                                .exclude(expires__lte=datetime.now()
                                         ).count()
        
        return '''<p>&nbsp; &nbsp;* Trials make up ''' +\
             str(houdini_stats.utils.get_percent(trials, all)) +\
              '''% of all licenses (''' +  str(trials)+ ''' of ''' + str(all) +\
              ''') <br> &nbsp; &nbsp;* ''' +\
              str(num_active) + " trials are currently active </p>" 
    
#-------------------------------------------------------------------------------

class TrialLicensesForPaidAssets(Trials):
    """
    Trial Licences for paid assets. Pie Charts.
    """ 
    
    def name(self):
        return "trial_licenses_paid_assets"

    def title(self):
        return "Trial Licenses for Paid Assets"
    
    def get_data(self, series_range, aggregation):
        # First, we get all paid assets
        paid_assets = []
        for asset in StoreAsset.active_objects.all():
            prices = asset.get_total_prices()
            for x in prices:
                price = x["price"]
                right = x["right"]
                if price is not None:
                    if price != Decimal(0) and right != "Trial":
                        paid_assets.append(asset)
                        break
    
        # Garther all the licenses of these paid assets
        relevant_licenses = []
        for asset in paid_assets:
            license_set = StoreLicense.objects.filter(asset=asset)
            for x in license_set:
                relevant_licenses.append(x)
                
        counts = defaultdict(int)
        for license in relevant_licenses:
            counts[license.right.abbrev] += 1
    
        return [["Trials", counts["trial"]],
                ["Apprentice", counts["apprentice"]],
                ["Regular", counts["regular"]]]

#-------------------------------------------------------------------------------

class TrialLicensesUpgrades(Trials):
    """
    Houdini versions and builds. Pie Charts.
    """  
    num_trials_only = 0
    num_upgraded_trials = 0
    num_paid_no_trial = 0
      
    def name(self):
        return "trial_licenses_upgrades"

    def title(self):
        return "Trial Licenses Upgrades"
        
    def get_data(self, series_range, aggregation):
        
        self.get_num_trials() 
        
        trials_upgrade = [["Trying then buying", self.num_upgraded_trials],
                          ["Trying and not buying", self.num_trials_only]]
        
        trials_purchase = [["Just buying", self.num_paid_no_trial],
                           ["Buying after trial", self.num_upgraded_trials]]                                                
                                                         
        return trials_upgrade, trials_purchase
    
    def get_num_trials(self):
        """
        This function will return the number of:
        - Number of licenses that were just trials
        - Number of licenses that were trials first but then were purchased
        - Number of lic that were just purchased but never a trial before. 
        """
        
        admin = get_user("admin")
        trials = get_licenses_count(admin, get_right("trial"))
        
        num_upgraded_trials = 0
        num_paid_no_trial = 0
        
        # Loop over the paid licenses to determine how many
        # were first purchased as trials.
        for paid_license in StoreLicense.objects.exclude(owner=admin)\
                                           .filter(invoice__isnull=False)\
                                           .exclude(asset_price__price=Decimal(0)):
    
            try:
                # Attempt to get a trial license
                l = StoreLicense.objects.get(right= get_right("trial"),
                                        owner=paid_license.owner,
                                        asset=paid_license.asset)
    
                # A trial exists, but since we do not want to count
                # users who have all three (trial,apprentice,regular)
                # more than once, we will only increment our counter
                # for apprentice licenses if a regular license does not exist
                if paid_license.right == get_right("apprentice"):
                    try:
                        StoreLicense.objects.get(right=get_right("regular"),
                                            owner=paid_license.owner,
                                            asset=paid_license.asset)
                    except StoreLicense.DoesNotExist:
                        num_upgraded_trials += 1
    
                else:
                    num_upgraded_trials += 1
    
            except StoreLicense.DoesNotExist:
                # No trial was found
                num_paid_no_trial += 1
    
        self.num_trials_only = trials - num_upgraded_trials
        self.num_upgraded_trials = num_upgraded_trials
        self.num_paid_no_trial = num_paid_no_trial
        
    def chart_aditional_information_above(self):
        return '''<p> 
               &nbsp; &nbsp;* '''+ str(self.num_upgraded_trials) +\
               ''' trial licenses have later been upgraded to paid versions <br>
               &nbsp; &nbsp;* ''' + str(self.num_paid_no_trial) +\
               ''' paid licenses have been purchased without downloading a trial 
               first <br> &nbsp; &nbsp;* ''' + str(self.num_trials_only)+\
               ''' trials have not been upgraded to paid versions </p>''' 
    
    def chart_count(self):
        return 2    
    