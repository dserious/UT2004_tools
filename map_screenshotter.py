# This is absolute dumpsterfire-grade code, and I'm sorry in advance.
# Just wanted to get this working expeditiously

import os
import time
import pywinauto
import subprocess
from PIL import Image

from pywinauto.application import Application
from pywinauto import mouse

# GENERATE METADATA BY EXPORTING T3D FILES? (Needed for generating screenshots)
# This can be used to build a database of map weapon and vehicle count data.
get_metadata = False

# LAUNCH THE GAME AND GENERATE SCREENSHOTS (This might need to run a while. Screenshots will go in ./ScreenShots/)
get_screenshots = False

# HOW MANY SCREENSHOTS TO TAKE OF EACH MAP
number_of_screenshots = 3

# GENERATE UTX FILE?
make_utx = True

# UTX FILENAME
utx_filename = "WSVotingScreenshots"

# BASE DIRECTORY (the windows ut2004.exe binary is expected to be in ... ./system/ut2004.exe)
ut2004_directory = "E:/CO30_BACKUP-9-10-24/_/"

# SCREENSHOTS OUTPUT SUBDIRECTORY (Postprocessing directory for importable-bmps)
screenshot_output_directory = "/ScreenShots-output/"

# IGNORE MAPS THAT DONT START WITH DM-
process_dm_only = True

# NATIVE PACKAGES TO IGNORE
native_packages = ['None', 'False', 'Engine']


def main():
    for filename in os.listdir(ut2004_directory + "Maps"):
        # Make sure its a DM file or 
        if process_dm_only:
            if not "DM-" in filename and not "dm-" in filename:
                print('%s not a deathmatch map, skipping.' % filename)
                continue
    
        # check if t3d export path exists
        if not os.path.exists(ut2004_directory + "export"):
           # Create a new directory because it does not exist
           os.makedirs(ut2004_directory + "export")
    
        f = os.path.join(ut2004_directory + "Maps", filename)
        #t3d = os.path.join(ut2004_directory + "export", "myLevel.t3d")
        # checking if it is a file
        if os.path.isfile(f):
            print(f)
            if get_metadata:
                #export it to ASCII with UCC if map hasn't already been exported
                if not os.path.isfile(ut2004_directory + "export/" + filename + ".t3d"):
                    execute_string = '%sSystem/ucc.exe batchexport %s Level t3d ../export' % (ut2004_directory, f)
                    print(execute_string)
                    ucc = subprocess.run(execute_string.split(), capture_output=True)
                    print('Exporting actors')
                    try:
                        os.rename(ut2004_directory + "export/myLevel.t3d", ut2004_directory + "export/" + filename + ".t3d")
                    except FileNotFoundError:
                        print('ucc export failed')
                if os.path.isfile(ut2004_directory + "export/" + filename + ".t3d"):
                    t3d = ut2004_directory + "export/" + filename + ".t3d"
                else:
                    continue
            if get_screenshots:
                if "Success" in ucc.stdout.decode('UTF-8'):
                    # Export success means high probability that dependencies are in place
                    if check_if_all_screenshots_exist(filename):
                        print('Screenshot already exists')
                    else:
                        if not generate_screenshots(filename):
                            print('Couldnt capture screenshots, something crashed. Skipping map')
                            continue
                        try:
                            os.rename(ut2004_directory + "/export/myLevel.t3d", ut2004_directory + "/export/%s.t3d" % filename)
                        except FileExistsError:
                            print('file already exists')
                        except FileNotFoundError as e:
                            print('myLevel.t3d not generated for some reason..')
                            
            # actors = extract_text_between_actors(ut2004_directory + "/export/%s.t3d" % filename)
            if get_metadata:
                actors = extract_text_between_actors(t3d)
                level_info_actor = actor_search(actors, "LevelInfo")
                map_title = get_value_from_actor(level_info_actor, "Title")
                textures = find_all_textures_in_actors(actors)
                sounds = find_all_sounds_in_actors(actors)
                weapons = get_all_weapon_counts(actors)
                vehicles = get_all_vehicle_counts(actors)
                print(textures)
                print(sounds)
                print(weapons)
                print(vehicles)
    if make_utx:
        print('resizing screenshots...')
        crop_and_resize_images(ut2004_directory + "ScreenShots", ut2004_directory + screenshot_output_directory)
        generate_utx()
            
def check_if_all_screenshots_exist(map):
    # check if screnshoots already exists
    for n in range(0, number_of_screenshots):
        if not check_if_screenshot_number_exists(map, n+1):
            return False
    return True
    
def check_if_screenshot_number_exists(map, n):
    screenshot_file = os.path.join(ut2004_directory + "ScreenShots" + "/" + map + "-" + str(n) + ".bmp")
    if os.path.isfile(screenshot_file):
        return True
    else:
        return False

def generate_screenshots(map):
    client = Application().start(ut2004_directory + '/System/UT2004.exe %s?Name=Screenshotter?Class=Engine.Pawn?Character=Ophelia?team=255?Sex=F?Voice=XGame.MercMaleVoice?SpectatorOnly=1?BonusVehicles=false?Game=XGame.xDeathMatch?bAutoNumBots=False?NumBots=1' % map)

    # Wait for app to load then click window
    time.sleep(5)
    try:
        client.window(title='Unreal Tournament 2004').set_focus()
        client.window(title='Unreal Tournament 2004').click()
        # Wait for map to load then click to start game
        time.sleep(3)
        client.window(title='Unreal Tournament 2004').click()
        # after game starts click to spectate bot
        time.sleep(3)
        pywinauto.mouse.click(button='left', coords=(0,0))
        # Look from bot's first person view
        client.window(title='Unreal Tournament 2004').type_keys("{TAB 2}behindview 0{ENTER 2}",with_spaces=True)
        # Kill the display hud and weapon view so we get a clean screenshot
        client.window(title='Unreal Tournament 2004').type_keys("{TAB 2}killall hud{ENTER 2}",with_spaces=True)
        for n in range(0, number_of_screenshots):
            # Get screenshot
            time.sleep(10)
            client.window(title='Unreal Tournament 2004').type_keys("{TAB 2}shot %s-%s{ENTER 2}" % ("screenshot", str(n+1)),with_spaces=True)
            # Kill all bots, then re-add one, then click again. This should increase likelihood of the bot moving around the map from a different spawn point
            client.window(title='Unreal Tournament 2004').type_keys("{TAB 2}killall bot{ENTER 2}",with_spaces=True)
            client.window(title='Unreal Tournament 2004').type_keys("{TAB 2}addbots 1{ENTER 2}",with_spaces=True)
            pywinauto.mouse.click(button='left', coords=(0,0))
            client.window(title='Unreal Tournament 2004').type_keys("{TAB 2}behindview 0{ENTER 2}",with_spaces=True)
            print("screenshot %s %s" % (map, str(n+1)))
        time.sleep(1)
        client.window(title='Unreal Tournament 2004').type_keys("{TAB 2}exit{ENTER 2}",with_spaces=True)
        client.kill()
    except:
        # UT2004 didnt load (almost certainly because missing dependency)
        print('UT2004 couldnt open map')
        client.kill()
        return False
    print("renaming screenshots to match map name")
    for n in range(0, number_of_screenshots):
        if check_if_screenshot_number_exists(map, n+1):
            print("removing: " + ut2004_directory + "/ScreenShots/screenshot-" + str(n+1) + ".bmp")
            os.remove(ut2004_directory + "/ScreenShots/screenshot-" + str(n+1) + ".bmp")
        else:
            print("keeping: " + ut2004_directory + "/ScreenShots/screenshot-" + str(n+1) + ".bmp")
            os.rename(ut2004_directory + "/ScreenShots/screenshot-" + str(n+1) + ".bmp", ut2004_directory + "/ScreenShots/" + map + "-" + str(n+1) + ".bmp")
    return True


def actor_search(actor_list, search_text):
    for actor in actor_list:
        if search_text in actor:
            return actor
            
def get_all_entity_counts(actors, entities):
    entity_quantities = {}
    for entity in entities:
       entity_quantities[entity] = 0
    for actor in actors:
        for entity in entities:
            if entity in actor:
                entity_quantities[entity] += 1
    return entity_quantities
    
def get_all_vehicle_counts(actors):
    vehicles = ['ONSTankFactory', 'ONSHoverCraftFactory', 'ONSRVFactory','ONSAttackCraftFactory','ONSBomberFactory','ONSDualAttackCraftFactory','ONSHoverCraftFactory','ONSMASFactory','ONSShockTankFactory']
    return get_all_entity_counts(actors, vehicles)
    
def get_all_weapon_counts(actors):
    weapons = ['XWeapons.RocketLauncher', 'XWeapons.SniperRifle', 'XWeapons.FlakCannon', 'XWeapons.ShockRifle', 'XWeapons.Minigun', 'XWeapons.BioRifle', 'XWeapons.Painter', 'XWeapons.LinkGun', 'XWeapons.Redeemer']
    return get_all_entity_counts(actors, weapons)
            
def get_value_from_actor(actor, search_key):
    try:
        for line in iter(actor.splitlines()):
            if search_key in line:
                return line.split(search_key + "=",1)[1]
        return "None"
    except:
        print("ignoring bad actor")
        return "None"
    
def find_all_textures_in_actors(actors):
    texture_packages = []
    for actor in actors:
        # index all texture dependencies
        textures = find_all_textures_in_actor(actor)
        for texture in textures:
            texture_package = texture.split(".", 1)[0]
            if texture_package not in texture_packages and texture_package not in native_packages:
                texture_packages.append(texture_package)
    return texture_packages
    
def find_all_textures_in_actor(actor):
    textures = []
    for line in iter(actor.splitlines()):
        if "Texture=" in line:
            texture = line.split("Texture=",1)[1]
            # Remove 'shader' and 'finalblend' designations
            texture = texture.replace('Shader', '')
            texture = texture.replace('FinalBlend', '')
            if "Texture'" in texture:
                texture = line.split("Texture'",1)[1]
                texture = texture.split("'", 1)[0]
            else:
                texture = texture.split(" ",1)[0]
            if texture not in textures:
                textures.append(texture)
        if "Texture'" in line:
            texture=line.split("Texture'",1)[1]
            texture = texture.split("'", 1)[0]
    return textures
    
def find_all_sounds_in_actors(actors):
    sound_packages = []
    for actor in actors:
        # index all sound dependencies
        sounds = find_all_sounds_in_actor(actor)
        for sound in sounds:
            sound_package = sound.split(".", 1)[0]
            if sound_package not in sound_packages and sound_package not in native_packages:
                sound_packages.append(sound_package)
    return sound_packages    
    
def find_all_sounds_in_actor(actor):
    sounds = []
    for line in iter(actor.splitlines()):
        if "Sound=" in line:
            sound = line.split("Sound=",1)[1]
            # Remove 'shader' and 'finalblend' designations
            sound = sound.replace('Shader', '')
            sound = sound.replace('FinalBlend', '')
            if "Sound'" in sound:
                sound = line.split("Sound'",1)[1]
                sound = sound.split("'", 1)[0]
            else:
                sound = sound.split(" ",1)[0]
            if sound not in sounds:
                sounds.append(sound)
        if "Sound'" in line:
            sound = line.split("Sound'",1)[1]
            sound = sound.split("'", 1)[0]
    return sounds
    
def extract_text_between_actors(filename):
    """
    Extracts the text between "Begin Actor" and "End Actor" markers in a given string.

    Args:
        text: The string containing the text to be extracted.

    Returns:
        A list of strings, each representing the text between a pair of "Begin Actor" and "End Actor" markers.
    """
    with open(filename, 'r') as file:
        content = file.read()

    actor_data = []
    current_actor = ""
    in_actor_block = False
    for line in content.splitlines():
        if line.startswith("Begin Actor"):
            in_actor_block = True
            try:
                text_after_begin_actor=line.split("Begin Actor",1)[1]
                # remove extrenous whitespace
                text_after_begin_actor.join(text_after_begin_actor.split())
                # split into two lines
                text_after_begin_actor = text_after_begin_actor.replace(" ", "\n")
                current_actor = text_after_begin_actor + "\n"
            except:
                current_actor = ""
        elif line.startswith("End Actor"):
            in_actor_block = False
            if current_actor:
                actor_data.append(current_actor)
                current_actor = ""
        elif in_actor_block:
            current_actor += line + "\n"
            
    return actor_data
 
def crop_and_resize_images(directory, output_directory, size=(512, 512)):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Loop over all BMP files in the directory
    for filename in os.listdir(directory):
        # If process_dm_only is True, skip files that don't start with "DM-"
        if process_dm_only and not filename.startswith("DM-"):
            continue

        # Process only files that contain ".ut2-1" in the filename
        if ".ut2-1" not in filename:
            continue
            
        print(filename)

        if filename.endswith(".bmp"):
            img_path = os.path.join(directory, filename)
            
            # Open the image
            with Image.open(img_path) as img:
                # Crop the image to a square by selecting the center
                width, height = img.size
                min_dim = min(width, height)
                
                # Calculate cropping box
                left = (width - min_dim) / 2
                top = (height - min_dim) / 2
                right = (width + min_dim) / 2
                bottom = (height + min_dim) / 2
                
                # Crop and resize the image
                img_cropped = img.crop((left, top, right, bottom))
                img_resized = img_cropped.resize(size)

                # Reduce to 256 colors (Pillow uses P mode for palettes)
                img_reduced = img_resized.convert("P", palette=Image.ADAPTIVE, colors=256)

                # Modify the filename by removing ".ut2-1"
                output_filename = filename.replace(".ut2-1", "")
                output_path = os.path.join(output_directory, output_filename)

                # Save the image in the output directory
                img_reduced.save(output_path)

    print(f"Processed images saved to {output_directory}")
    
def generate_utx():
    print('Generating UTX...')
    execute_string = '%sSystem/ucc.exe editor.batchimport ..\%s.utx texture ..\%s\*.bmp' % (ut2004_directory, utx_filename, os.path.join(ut2004_directory, screenshot_output_directory))
    print(execute_string)
    ucc = subprocess.run(execute_string.split(), capture_output=True)
    print(ucc)


if __name__ == "__main__":
    main()
