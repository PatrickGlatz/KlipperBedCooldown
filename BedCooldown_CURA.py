""" Simple re-coding of the OctoPrint Bed Cooldown Plugin.
CURA plugin is needed to simply pass the slicer estimated time (after klipper estimator) """
# Copyright (c) 2017 Ghostkeeper
# The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.

import re #To perform the search and replace.

from ..Script import Script
from UM.Logger import Logger


class BedCooldown(Script):
    """Performs a search-and-replace on all g-code.

    Due to technical limitations, the search can't cross the border between
    layers.
    """

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        """ Open Settings """
        return """{
            "name": "Bed Cooldown",
            "key": "BedCooldown",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "elapsed":
                {
                    "label": "Time elapsed threshold >",
                    "description": "Time [s] which has to be elapsed to activate cooldown",
                    "unit": "s",
                    "type": "int",
                    "default_value": "901",
                    "minimum_value": "0",
                    "maximum_value": "604800"
                },
                "remain":
                {
                    "label": "Time remain threshold <",
                    "description": "Time [s] ]remain until end of print to activate cooldown",
                    "unit": "s",
                    "type": "int",
                    "default_value": "901",
                    "minimum_value": "0",
                    "maximum_value": "604800",
                    "maximum_value_warning": "1801"
                },
                "progress":
                {
                    "label": "Progress threshold >",
                    "description": "Progress [%] threshold to activate cooldown",
                    "unit": "%",
                    "type": "int",
                    "default_value": "75",
                    "minimum_value": "0",
                    "minimum_value_warning": "49",
                    "maximum_value": "100"
                },
                "progresstype":
                {
                    "label": "Progress type",
                    "description": "Progress type [virtual_sdcard, display_status, time].  virtual_sdcard = The progress value of the last M73 G-Code command (or virtual_sdcard.progress if no recent M73 received). display_status = An estimate of the current print progress (based of file size and file position).   time = Elapsed time / Slicer Estimated Time * 100",
                    "type": "enum",
                    "options": {
                        "virtual_sdcard": "virtual_sdcard", 
                        "display_status": "display_status", 
                        "time": "time"
                    },
                    "default_value": "time"
                },
                "temperature":
                {
                    "label": "Target temperature",
                    "description": "Target temperature [°C] to cooldown to",
                    "unit": "°C",
                    "type": "int",
                    "default_value": "0",
                    "minimum_value": "0",
                    "maximum_value": "95",
                    "maximum_value_warning": "20"
                },
                "debug":
                {
                    "label": "Debug Mode",
                    "description": "Extended printing to console (M118)",
                    "type": "bool",
                    "default_value": false
                }
            }
        }"""

    def execute(self, data):
        """ Execute script 
        The script iterates through each 'LAYER', which is either a block of settings or really one print layer

        There, it searches for ';TIME:XXXX' and grabs that number 
        
        """

        # For CURA SLICER
        search_time = r'(^;\s*TIME:\s*)(.*)'
        time_regex = re.compile(search_time, re.IGNORECASE)
        layer0_search = r'(^;\s*LAYER:\s*0)'
        layer0_regex = re.compile(layer0_search, re.IGNORECASE)


        # Search for estimated slicer time
        slicer_time = None
        for layer_number, layer in enumerate(data):
            for line_number, line in enumerate(layer.splitlines()):
                # Search for estimated slicer time
                if match := time_regex.search(line):
                    Logger.log("d", f'slicer_time:            {slicer_time}')
                    Logger.log("d",  'Found slicer_time')
                    Logger.log("d", f'Layer {layer_number}, Line {line_number}: {line}')
                    slicer_time = match.group(2)
                    break


        # Assemble BedCooldown Command and insert text
        bed_cooldown_command = f'INIT_BED_COOLDOWN SLICER_TIME_ESTIMATED={slicer_time} ELAPSED_TIME_THRESHOLD={int(self.getSettingValueByKey("elapsed"))} REMAIN_TIME_THRESHOLD={int(self.getSettingValueByKey("remain"))} PROGRESS_THRESHOLD={int(self.getSettingValueByKey("progress"))} PROGRESS_TYPE={self.getSettingValueByKey("progresstype")} TARGET_TEMP={int(self.getSettingValueByKey("temperature"))} DEBUG={self.getSettingValueByKey("debug")}'
        insert_string = f';LAYER:0\n{bed_cooldown_command}'


        # Insert BedCooldown Command at layer 0
        for layer_number, layer in enumerate(data):
            data[layer_number] = re.sub(layer0_regex, insert_string, layer) #Replace all.


        # Log infos to /Users/${USERNAME}/Library/Application Support/cura/${VERSION}/cura.log

        Logger.log("d", '')
        Logger.log("d", '')
        Logger.log("d", 'BedCooldown')
        Logger.log("d", '')
        Logger.log("d", f'slicer_time:            {slicer_time}')
        Logger.log("d", f'ELAPSED_TIME_THRESHOLD: {int(self.getSettingValueByKey("elapsed"))}')
        Logger.log("d", f'REMAIN_TIME_THRESHOLD:  {int(self.getSettingValueByKey("remain"))}')
        Logger.log("d", f'PROGRESS_THRESHOLD:     {int(self.getSettingValueByKey("progress"))}')
        Logger.log("d", f'TARGET_TEMP:            {int(self.getSettingValueByKey("temperature"))}')
        Logger.log("d", '')
        Logger.log("d", f'bed_cooldown_command:   {bed_cooldown_command}')
        Logger.log("d", '')
        Logger.log("d", '')


        # Return data to CURA
        return data
