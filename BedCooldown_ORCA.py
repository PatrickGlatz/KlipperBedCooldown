#!/opt/homebrew/opt/python@3/libexec/bin/python
""" Simple script to enable automatic Bed Cooldown towards the end of the print

Assumptions:
  - Print time estimation is given in this exact format
    ; estimated printing time (normal mode) = 13m 45s

Prerequisites:
  - Have the following in your START GCODE
    ;ENABLE_BED_COOLDOWN
  - Configure this script in your "Post-processing Scripts" in OrcaSlicer

Config options:
    - SLICER_TIME_ESTIMATED  : Estimated print time by slicer (and even better after KlipperEstimator), either in [s] or in [xxd xxh xxm xxs]
    - ELAPSED_TIME_THRESHOLD : Elapsed time threshold in [s], greater than
    - REMAIN_TIME_THRESHOLD  : Remaining time threshold in [s], smaller than
    - PROGRESS_THRESHOLD     : Progress threshold in [%], greater than
    - PROGRESS_TYPE          : Type of progress to evaluate the trigger, i.e. one of [virtual_sdcard, display_status, time]
    - TARGET_TEMP            : Target temperature after the criterias are met in [°C]
    - DEBUG                  : Debug Mode, extended printing to console (M118), one of [true, false]

Syntax:
in SHELL: BedCooldown_ORCA.py [PARAMS=VALUE] PATH_TO_FILE
BedCooldown_ORCA.py REMAIN_TIME_THRESHOLD=300 DEBUG=true /path/to/file.gcode

in ORCA:  BedCooldown_ORCA.py [PARAMS=VALUE]
BedCooldown_ORCA.py REMAIN_TIME_THRESHOLD=300 


"""


# Import modules
import os            # to run the system build-in ping command
import sys           # to exit processes
import re            # to search and replace the specific lines


# Check if the passed file exists
passed_file_name = sys.argv[-1]
if not os.path.isfile(passed_file_name):
    sys.exit("Issue with passed_file_name: " + passed_file_name)


# Set defaults
PARAMS = {'SLICER_TIME_ESTIMATED': None,
          'ELAPSED_TIME_THRESHOLD': 900,
          'REMAIN_TIME_THRESHOLD': 900,
          'PROGRESS_THRESHOLD': 90,
          'PROGRESS_TYPE': 'time',
          'TARGET_TEMP': 60,
          'DEBUG': 'false'}

for PARAM in PARAMS.keys():
    for arg in sys.argv:
        if PARAM.lower() in arg.lower():
            PARAMS[PARAM] = re.sub(fr'-*{PARAM.lower()}=', '', arg, flags=re.IGNORECASE)
print(PARAMS)


# Die Zeitangabe als String, exemplarisch in ORCA und in CURA
time_orca = \
'''
; SOME GCODE 
; estimated printing time (normal mode) = 1d 15h 43m 23s
; SOME GCODE
'''
time_cura = \
'''
; SOME GCODE
;TIME:17677
; SOME GCODE
'''




# Öffne das übergebene GCODE File
with open(passed_file_name, 'r+') as gcode_file:

    # Hole den GCODE File Content
    content = gcode_file.read()
    
    # Definiere das Muster für Tage, Stunden, Minuten und Sekunden in ORCA
    #pattern = r"(?:(\d+)d)?\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?"
    pattern = r"^; estimated printing time \(normal mode\) = (?:(\d+)d)?\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?$"
    
    # Wende das Muster an und extrahiere die Komponenten
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        days = int(match.group(1) or 0)
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        seconds = int(match.group(4) or 0)

        # Konvertiere alle Komponenten in Sekunden
        PARAMS['SLICER_TIME_ESTIMATED'] = days * 86400 + hours * 3600 + minutes * 60 + seconds

        # Hole Zeit nochmals in formatierter Schreibweise
        formatted_time = ''
        if days != 0:
            formatted_time = f'{days}d'
        if formatted_time != '':
            formatted_time += f' {hours}h'
        elif hours != 0:
            formatted_time = f'{hours}h'
        if formatted_time != '':
            formatted_time += f' {minutes}m'
        elif minutes != 0:
            formatted_time = f'{minutes}m'
        if formatted_time != '':
            formatted_time += f' {seconds}s'
        elif seconds != 0:
            formatted_time = f'{seconds}'

        # Schreibe die Zeit in Sekunden in das FILE
        subst = fr';TIME:{PARAMS["SLICER_TIME_ESTIMATED"]}\n{match.group()}'
        new_content = re.sub(pattern, subst, content, 0, re.MULTILINE)

        # Move the cursor to the beginning and truncate to overwrite inplace
        gcode_file.seek(0)
        gcode_file.write(new_content)
        gcode_file.truncate()  # Remove any leftover text if new content is shorter

    else:

        # Definiere das Muster für die Zeit in CURA
        pattern = r"^;TIME:(\d+)$"
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            PARAMS['SLICER_TIME_ESTIMATED'] = int(match.group(1))
            
            # Umrechnung in Tage, Stunden, Minuten und Sekunden
            days = PARAMS['SLICER_TIME_ESTIMATED'] // 86400
            hours = (PARAMS['SLICER_TIME_ESTIMATED'] % 86400) // 3600
            minutes = (PARAMS['SLICER_TIME_ESTIMATED'] % 3600) // 60
            seconds = PARAMS['SLICER_TIME_ESTIMATED'] % 60

            # Formatieren der Ausgabe
            formatted_time = ''
            if days > 0:
                formatted_time = f"{days}d"
            if formatted_time != '':
                formatted_time += f" {hours}h"
            elif hours > 0:
                formatted_time = f"{hours}h"
            if formatted_time != '':
                formatted_time += f" {minutes}m"
            elif minutes > 0:
                formatted_time = f"{minutes}m"
            if formatted_time != '':
                formatted_time += f" {seconds}s"
            elif seconds > 0:
                formatted_time = f"{seconds}s"

            subst = fr'{match.group()}\n; estimated printing time (normal mode) = {formatted_time}'
            new_content = re.sub(pattern, subst, content, 0, re.MULTILINE)

            # Move the cursor to the beginning and truncate to overwrite inplace
            gcode_file.seek(0)
            gcode_file.write(new_content)
            gcode_file.truncate()  # Remove any leftover text if new content is shorter



        else:
            sys.exit("Ungültiges Format")
    
    # Ausgabe der erkannten SLICER TIME
    print(formatted_time)
    print(PARAMS['SLICER_TIME_ESTIMATED'])






# Validate PARAMS
if not isinstance(PARAMS['SLICER_TIME_ESTIMATED'], int):
    sys.exit("Fehler in der Ermittlung von SLICER_TIME_ESTIMATED")

try:
    PARAMS['SLICER_TIME_ESTIMATED'] = int(PARAMS['SLICER_TIME_ESTIMATED'])
    if not 0 <= PARAMS['SLICER_TIME_ESTIMATED']:
        raise UnallowedDictValues
    PARAMS['ELAPSED_TIME_THRESHOLD'] = int(PARAMS['ELAPSED_TIME_THRESHOLD'])
    if not 0 <= PARAMS['ELAPSED_TIME_THRESHOLD']:
        raise UnallowedDictValues
    PARAMS['REMAIN_TIME_THRESHOLD'] = int(PARAMS['REMAIN_TIME_THRESHOLD'])
    if not 0 <= PARAMS['REMAIN_TIME_THRESHOLD']:
        raise UnallowedDictValues
    PARAMS['PROGRESS_THRESHOLD'] = int(PARAMS['PROGRESS_THRESHOLD'])
    if not 0 <= PARAMS['PROGRESS_THRESHOLD'] <= 100:
        raise UnallowedDictValues
    if not PARAMS['PROGRESS_TYPE'].lower() in ['virtual_sdcard', 'display_status', 'time']:
        raise UnallowedDictValues
    else:
        PARAMS['PROGRESS_TYPE'] = PARAMS['PROGRESS_TYPE'].lower()
    PARAMS['TARGET_TEMP'] = int(PARAMS['TARGET_TEMP'])
    if not 0 <= PARAMS['TARGET_TEMP'] <= 85:
        raise UnallowedDictValues
    if not PARAMS['DEBUG'].lower() in ['true', 'false']:
        raise UnallowedDictValues
    else:
        PARAMS['DEBUG'] = PARAMS['DEBUG'].lower()

except:
    sys.exit(f'Fehler in den Parametern von ENABLE_BED_COOLDOWN:\n\n{PARAMS}')



# Enable Bed Cooldown schreiben
with open(passed_file_name, 'r+') as gcode_file:
    # Hole den aktuellen File Content nochmals
    content = gcode_file.read()

    # Definiere den Auszutauschenden Platzhalter
    pattern = fr'^;\s*?ENABLE_BED_COOLDOWN\s*?$'
    replace = f'ENABLE_BED_COOLDOWN SLICER_TIME_ESTIMATED={PARAMS["SLICER_TIME_ESTIMATED"]} ELAPSED_TIME_THRESHOLD={PARAMS["ELAPSED_TIME_THRESHOLD"]} REMAIN_TIME_THRESHOLD={PARAMS["REMAIN_TIME_THRESHOLD"]} PROGRESS_THRESHOLD={PARAMS["PROGRESS_THRESHOLD"]} PROGRESS_TYPE={PARAMS["PROGRESS_TYPE"]} TARGET_TEMP={PARAMS["TARGET_TEMP"]} DEBUG={PARAMS["DEBUG"]}'

    new_content = re.sub(pattern, replace, content, 0, re.MULTILINE)   # Replace regex pattern  with substitution
    
    # Move the cursor to the beginning and truncate to overwrite inplace
    gcode_file.seek(0)
    gcode_file.write(new_content)
    gcode_file.truncate()  # Remove any leftover text if new content is shorter


