# ACH 2 m3/s-m2
#
# Honeybee: A Plugin for Environmental Analysis (GPL) started by Mostapha Sadeghipour Roudsari
# 
# This file is part of Honeybee.
# 
# Copyright (c) 2013-2020, Abraham Yezioro <ayez@ar.technion.ac.il> 
# Honeybee is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation; either version 3 of the License, 
# or (at your option) any later version. 
# 
# Honeybee is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Honeybee; If not, see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>


"""
Use this component to transform ACH or inifitration per area of facade to m3/s-m2.
Plug the result to the Honeybee setEPZoneLoads component, infiltrationRatePerArea_ or  infiltrationRatePerArea_ inputs
For the blowerPressue input, the component assumes a natural pressure differential between indoors and outdoors at 4 Pascals.  However, the passive house standard sets this at a low 0.4303.
-
Provided by Honeybee 0.0.66
    
    Args:
        _HBZones: Honeybee zones for which you want to calculate the infiltration or ventilation rates.
        _airFlowRate: A number representing the air flow rate into the HBZone in Air Changes per Hour (ACH).  Alternatively this number can be in m3/s per m2 of exposed envelope area if the input below is set to "False."  The latter is useful for infiltration, which is typically specified as a unit per area of exposed envelope.
        _ACHorM3sM2_: Set to "True" to have the airFlowRate above interpreted as ACH. Set to "False" to have itinterpreted as m3/s per m2 of outdoor-exposed zone surface area.  This latter is useful for infiltration rates, which are usually defined as an intensity of flow per unit outdoor exposure.  The default is set to True for ACH.
        _blowerPressure_: A number representing the pressure differential in Pascals (Pa) between indoors/outdoors at which the specified flow rate above occurs.  When set to 0 or left untouched, the specified input flow rate to this component will be the same as that output from the component (only the units will be converted and no translation from one pressure to another will occur).  However, many blower door tests for infiltration occur at higher pressure differentials of 50 Pa or 75 Pa.  You can input this pressure differential here in order to convert the flow rate of this blower door test to typical building pressure flow rates of 4 Pa.
    Returns:
        readMe!: Report of the calculations
        infPerAreaFacade: infiltrationRatePerArea_Facade in m3/s-m2 (Cubic meters per second per square meter of exterior facade area) that can be plugged into the "Set EnergyPlus Zone Loads" component.
        ventPerAreaFloor: ventilationPerArea in m3/s-m2 (Cubic meters per second per square meter of floor area) that can be plugged into the "Set EnergyPlus Zone Loads" component.
        allExposed: The geometry of the zone that is interpreted as exposed surface area.
        allFloors: The geometry of the zone that is interpreted as floor area.
"""
ghenv.Component.Name = "Honeybee_infORventPerArea Calculator"
ghenv.Component.NickName = 'ACH2m3/s-m2 Calculator'
ghenv.Component.Message = 'VER 0.0.66\nJUL_07_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "HB-Legacy"
ghenv.Component.SubCategory = "08 | Energy | Set Zone Properties"
#compatibleHBVersion = VER 0.0.56\nMAY_05_2016
#compatibleLBVersion = VER 0.0.59\nFEB_01_2015
try: ghenv.Component.AdditionalHelpFromDocStrings = "0"
except: pass

import Grasshopper.Kernel as gh
import scriptcontext as sc
import Rhino as rc
import math

w = gh.GH_RuntimeMessageLevel.Warning
tol = sc.doc.ModelAbsoluteTolerance

def checkInputs():
    checkData = True
    if _airFlowRate < 0:
        checkData = False
        msg = 'Give a value for airChangeHour bigger than 0.'
        print msg
        ghenv.Component.AddRuntimeMessage(w, msg)
    
    if _HBZones[0]==None:
        checkData = False
    
    if _ACHorM3sM2_ == None: unit = True
    else: unit = _ACHorM3sM2_
    
    return checkData, unit

def main(hb_hive, HBZones, airFlowRate, unit):
    infPerAreaFacade = []
    ventPerAreaFloor = []
    allExposed = []
    allFloors  = []
    
    # call the objects from the hive
    zones = hb_hive.visualizeFromHoneybeeHive(HBZones)
    
    for count, HZone in enumerate(zones):
        zoneSrfArea = HZone.getExposedArea()
        flrArea = HZone.getFloorArea()
        
        # Get the flow rate in m3/s
        if unit == True:
            zoneVolume = HZone.getZoneVolume()
            standardFlowRate = (airFlowRate * zoneVolume) / 3600  # m3/s
        else:
            standardFlowRate = airFlowRate * zoneSrfArea  # m3/s
        
        # Check the pressure differential and convert if necessary.
        if _blowerPressure_ != None and _blowerPressure_ != 0:
            standardFlowRate = standardFlowRate/(math.pow((_blowerPressure_/4),0.63))
        
        # print the total standard flow rate in m3/s
        print 'Zone "{}" has a total flow rate of {} m3/s'.format(
            HZone.name, '%.4f' % standardFlowRate)
        
        # Calculate infiltration per area of exposed envelope (m3/s-m2).
        try:
            infPerAreaFacade.append(standardFlowRate / zoneSrfArea)  # m3/s per m2 exposed
        except:
            warning = 'One of the HBZones did not have any esposed surface area.\n' \
                'A value of 0 will be output for infPerAreaFacade.'
            print warning
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, warning)
            infPerAreaFacade.append(0)
        
        # Calculate ventilation per area of the floor (m3/s-m2).
        try:
            ventPerAreaFloor.append(standardFlowRate / flrArea)  # m3/s per m2 floor
        except:
            warning = 'One of the HBZones did not have any floor area.\n' \
                'A value of 0 will be output for ventPerAreaFloor.'
            print warning
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, warning)
            ventPerAreaFloor.append(0)
        
        # Get the geometry used to perform the various conversions
        for srf in HZone.surfaces:
            #srf.type == 2 (floors), == 2.5 (groundFloors), == 2.75 (exposedFloors)
            if int(srf.type) == 2:
                allFloors.append(srf.geometry)
        for HBSrf in HZone.surfaces:
            if HBSrf.BC.lower() == "outdoors":
                allExposed.append(HBSrf.geometry)
    
    return infPerAreaFacade, ventPerAreaFloor, allExposed, allFloors


#Honeybee check.
initCheck = True
if not sc.sticky.has_key('honeybee_release') == True:
    initCheck = False
    print "You should first let Honeybee fly..."
    ghenv.Component.AddRuntimeMessage(w, "You should first let Honeybee fly...")
else:
    try:
        if not sc.sticky['honeybee_release'].isCompatible(ghenv.Component): initCheck = False
        if sc.sticky['honeybee_release'].isInputMissing(ghenv.Component): initCheck = False
        hb_hive = sc.sticky["honeybee_Hive"]()
    except:
        initCheck = False
        warning = "You need a newer version of Honeybee to use this compoent." + \
        "Use updateHoneybee component to update userObjects.\n" + \
        "If you have already updated userObjects drag Honeybee_Honeybee component " + \
        "into canvas and try again."
        ghenv.Component.AddRuntimeMessage(w, warning)




if _HBZones != [] and _airFlowRate and initCheck == True:
    checkData, unit = checkInputs()
    if checkData == True:
        result = main(hb_hive, _HBZones, _airFlowRate, unit)
        if result != -1:
            infPerAreaFacade, ventPerAreaFloor, allExposed, allFloors = result
