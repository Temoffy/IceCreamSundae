import subprocess
import re
import configparser
import json
import os
import time
import shutil

import yaml #pip install pyYAML
from git import Repo #pip install GitPython

base = {}
modpackVersions = {}
mods = {}

def ReadConfig(path):
    temp = configparser.ConfigParser()
    temp.read(path)
    
    returnDict = {}
    for i in temp.sections():
        returnDict[i] = {}
        for k in temp[i]:
            returnDict[i][k] = json.loads(temp[i][k])
    return returnDict

def WriteConfig(twoDDict, path):
    temp = configparser.ConfigParser()
    for i in twoDDict:
        temp.add_section(i)
        for k in twoDDict[i]:
            temp.set(i,k,json.dumps(twoDDict[i][k]))
    with open(path, 'w') as configfile:
        temp.write(configfile)
    
def InitialDirSetup():
    path = base['paths']['packs']
    for platform in base['platforms']:
        if base['platforms'][platform]:
            if not os.path.isdir(os.path.join(path, platform)):
                os.makedirs(os.path.join(path, platform))
            if not os.path.isdir(os.path.join('config', 'overrides', platform)):
                os.makedirs(os.path.join('config', 'overrides', platform))
        
        for MCversion in base['minecraft']['versions']:
            packDir = os.path.join(path, platform, MCversion)
            if not os.path.isdir(packDir):
                os.makedirs(packDir)
                
                MakePack(MCversion, packDir)

                os.makedirs(os.path.join(packDir, 'shaderpacks'))
                os.makedirs(os.path.join(packDir, 'resourcepacks'))
                os.makedirs(os.path.join(packDir, 'config'))
                os.makedirs(os.path.join(packDir, 'mods'))

            overrideDir = os.path.join('config', 'overrides', platform, MCversion)
            if not os.path.isdir(overrideDir):
                os.makedirs(overrideDir)

                os.makedirs(os.path.join(overrideDir, 'shaderpacks'))
                os.makedirs(os.path.join(overrideDir, 'resourcepacks'))
                os.makedirs(os.path.join(overrideDir, 'config'))
                os.makedirs(os.path.join(overrideDir, 'mods'))


def MakePack(MCversion, path):
    if not MCversion in modpackVersions["versions"]:
        modpackVersions["versions"][MCversion] = MCversion+"-0.0" #will become 1.0 because of the next line
        modpackVersions['update'][MCversion] = 'major'

    opt = base["general"]
    subprocess.run(["packwiz","init",
                           "--author",opt["author"],
                           "--"+opt["loader"]+"-latest", #loader version selection
                           "--mc-version", MCversion,
                           "--modloader",opt["loader"],
                           "--name", opt["name"],
                           "--version", modpackVersions["versions"][MCversion]
                           ], cwd=path, capture_output=False)

#check in with the parent modpack for updates
def GitLatestParent():
    repo_url = "https://github.com/Fabulously-Optimized/fabulously-optimized"
    parentPacksPath = os.path.join(base["paths"]["parent"], "Packwiz")
    
    #make sure we're up to date
    try:
        repo = Repo.clone_from(repo_url, base["paths"]["parent"])
    except:
        repo = Repo(base["paths"]["parent"])
        o = repo.remotes.origin
        o.pull()

    for MCversion in base['minecraft']['versions']:
        if not MCversion in parentConfig["refVersions"]:
            parentConfig["refVersions"][MCversion] = ""

        path = os.path.join(parentPacksPath, MCversion)
        
        #read in version strings of the parent modpack to detect updates
        regex = r"version = \"(\S+)\""
        with open(os.path.join(path, "pack.toml"), "r") as f:
            packtomlFile = f.readlines()
        # Put all the lines into a single string
        packtomlTxt = "".join(packtomlFile)
        testVers = re.search(regex, packtomlTxt).group(1)

        if testVers == parentConfig['refVersions'][MCversion]:
            print("skipping "+MCversion)
            continue
        versionUpdate('minor', MCversion)
        print(MCversion+" needs updating")
        for platform in base['platforms']:
            if base['platforms'][platform]:
                updatetype = UpdatePackFromParent(platform, os.path.join(base['paths']['packs'], platform, MCversion), path)
                versionUpdate(updatetype, MCversion)
        parentConfig['refVersions'][MCversion] = testVers
        
    WriteConfig(parentConfig, os.path.join('config', 'parent.ini'))

def ListDirSafe(path):
    """Directory listing that doesn't blow up if the folder doesn't exist yet."""
    if not os.path.isdir(path):
        return []
    return os.listdir(path)

def UpdatePackFromParent(preferredPlatform, packPath, parentPath):

    updateType = 'none'
    for subfolder in ["mods","resourcepacks","shaderpacks"]:
        parentSubPath = os.path.join(parentPath, subfolder)
        childSubPath = os.path.join(packPath, subfolder)
        if not os.path.isdir(parentSubPath):
            continue

        parentFiles = ListDirSafe(parentSubPath)
        parentList = [f for f in parentFiles if f.endswith('.pw.toml') or f.endswith('.zip')]

        childFiles = ListDirSafe(childSubPath)
        childList = []
        for f in childFiles:
            if f.endswith('.pw.toml'):
                childList.append(f[:-len('.pw.toml')])
            elif f.endswith('.zip'):
                childList.append(f[:-len('.zip')])

        for item in parentList:
            if item.endswith('.zip'):
                #MANUAL OVERRIDE MOD ADDITIONS WILL NOT TRIGGER A MAJOR UPDATE
                shutil.copy(os.path.join(parentSubPath, item), os.path.join(childSubPath, item))
                continue
            item = item[:-len('.pw.toml')]
            if item in childList:
                continue
            if item.lower() in parentConfig['overrides']:
                item = parentConfig['overrides'][item.lower()]
            if item in childList:
                continue
            updateType = 'major'
            result = PackwizAdd(item, preferredPlatform, packPath)
            if result:
                continue
            print("can't add "+item)
            #reverse substitution
            for refItem in parentConfig['overrides']:
                if parentConfig['overrides'][refItem] == item:
                    item = refItem
                    break
            regex = re.escape(item)+r"\.(?:pw\.toml|zip|properties|json)"
            matches = [f for f in parentFiles if re.match(regex, f)]
            if not matches:
                print("couldn't locate fallback file for "+item)
                continue
            item = matches[0]
            print(item)
            shutil.copy(os.path.join(parentSubPath, item), os.path.join(childSubPath, item))
    #copy config
    parentConfigPath = os.path.join(parentPath, 'config')
    if os.path.isdir(parentConfigPath):
        shutil.copytree(parentConfigPath, os.path.join(packPath, 'config'), dirs_exist_ok=True)
    #cleanup
    delList = [os.path.join(packPath, 'resourcepacks', 'Mod Menu Helper.zip'),
               os.path.join(packPath, 'config', 'isxander-main-menu-credits.json'),
               os.path.join(packPath, 'config', 'modpack_defaults', 'config', 'isxander-main-menu-credits.json'),
               os.path.join(packPath, 'mods', 'capes.pw.toml')]
    for delPath in delList:
        if os.path.exists(delPath):
            os.remove(delPath)
    if os.path.isdir(os.path.join(packPath, 'config', 'crash_assistant')):
        shutil.rmtree(os.path.join(packPath, 'config', 'crash_assistant'))
    subprocess.run(['packwiz',"refresh"], cwd=packPath, capture_output=True)
    
    depPath = os.path.join(packPath, 'config', 'fabric_loader_dependencies.json')
    with open(depPath, 'r') as file:
        filedata = file.read()
    regex = r'"Fabulously Optimized":"[^"]+"'
    filedata = re.sub(regex, '"IceCreamSundae":"*"', filedata)
    with open(depPath, 'w') as file:
        file.write(filedata)

    with open(os.path.join('config', 'options.txt'), 'r') as file:
        myoptions = file.read()
    yosbrOptionsPath = os.path.join(packPath, 'config', 'modpack_defaults', 'options.txt')
    with open(yosbrOptionsPath, 'r') as file:
        baseoptions = file.read()
    baseoptions = baseoptions +'\n'+myoptions
    with open(yosbrOptionsPath, 'w') as file:
        file.write(baseoptions)

    return updateType


def PackwizAdd(item, preferredPlatform, path):
    time.sleep(.5) #don't get rate limited
    regex = r"Failed|No projects found|Cancel"
    resultRaw = subprocess.run(['packwiz',preferredPlatform,'add',item,"-y"], cwd=path, capture_output=True)
    result = re.findall(regex, resultRaw.stdout.decode())
    if len(result) == 0:
        return True
    for platform in base['platforms']:
        if not base['platforms'][platform] or platform == preferredPlatform:
            continue
        resultRaw = subprocess.run(['packwiz',platform,'add',item,"-y"], cwd=path, capture_output=True)
        result = re.findall(regex, resultRaw.stdout.decode())
        if len(result) == 0:
            return True
    return False

def versionUpdate(update, version):
    refUpdate = modpackVersions['update'][version]
    if refUpdate == 'none':
        modpackVersions['update'][version] = update
        return
    if update == 'major':
        modpackVersions['update'][version] = update
    return
    
def ParseAddMods(data, preferredPlatform, path, currentMods):
    AllAdded = True
    for item in data:
        if item['mr'] in currentMods:
            continue
        mod = item["mod"]
        if preferredPlatform == 'modrinth' and 'mr' in item:
            mod = item['mr']
        added = PackwizAdd(mod, preferredPlatform, path)
        if added and 'dependant' in item:
            ParseAddMods(item['dependant'], preferredPlatform, path, currentMods)
        #if added and item['config']:
        fallbackAdded = False
        if not added and 'fallback' in item:
            fallbackAdded = ParseAddMods(item['fallback'], preferredPlatform, path, currentMods)
        if added or fallbackAdded:
            #return True
            continue
        AllAdded = False
        print("can't add "+item["mod"])
        filedata = ""
        missingPath = os.path.join(path, 'missing.txt')
        if os.path.isfile(missingPath):
            with open(missingPath, 'r') as file:
                filedata = file.read()
        filedata = filedata + item["mod"] + '\n'
        with open(missingPath, 'w') as file:
            file.write(filedata)
        continue
        #return False
    return AllAdded

def AddYmlModsToAll(data):
    for MCversion in base['minecraft']['versions']:
        print(MCversion)
        for platform in base['platforms']:
            if not base['platforms'][platform]:
                continue
            path = os.path.join(base['paths']['packs'], platform, MCversion)
            with open(os.path.join(path, 'missing.txt'), 'w') as file:
                file.write("")
            with open(os.path.join(path, 'forceload.yml'), 'w') as file:
                file.write("")
            
            #apply overrides
            generalOverridePath = os.path.join('config', 'overrides', 'general')
            platformOverridePath = os.path.join('config', 'overrides', platform, MCversion)
            if os.path.isdir(generalOverridePath):
                shutil.copytree(generalOverridePath, path, dirs_exist_ok=True)
            if os.path.isdir(platformOverridePath):
                shutil.copytree(platformOverridePath, path, dirs_exist_ok=True)
            subprocess.run(['packwiz',"refresh"], cwd=path, capture_output=True)

            currentMods = []
            for subfolder in ["mods","resourcepacks","shaderpacks"]:
                subfolderPath = os.path.join(path, subfolder)
                for f in ListDirSafe(subfolderPath):
                    if f.endswith('.pw.toml'):
                        currentMods.append(f[:-len('.pw.toml')])
                    elif f.endswith('.zip'):
                        currentMods.append(f[:-len('.zip')])
            
            ParseAddMods(data, platform, path, currentMods)

            #re-apply overrides, just in case
            if os.path.isdir(generalOverridePath):
                shutil.copytree(generalOverridePath, path, dirs_exist_ok=True)
            if os.path.isdir(platformOverridePath):
                shutil.copytree(platformOverridePath, path, dirs_exist_ok=True)
            subprocess.run(['packwiz',"refresh"], cwd=path, capture_output=True)

            with open(os.path.join(path, 'forceload.yml'), 'r') as f:
                forceloadList = yaml.load(f, Loader=yaml.FullLoader)
            
            if forceloadList:
                print("adding forceloads")
                depPath = os.path.join(path, 'config', 'fabric_loader_dependencies.json')
                with open(depPath, 'r') as file:
                    fabricLoaderConfig = file.read()
                for item in forceloadList:
                    if item in fabricLoaderConfig:
                        continue
                    fabricLoaderConfig = re.sub(r"}}}}","}},\n\""+item+"\":{\"-depends\":{\"minecraft\":\"IGNORED\"}}}}", fabricLoaderConfig)
                with open(depPath, 'w') as file:
                    file.write(fabricLoaderConfig)

def UpdatePackData():
    for MCversion in base['minecraft']['versions']:
        for platform in base['platforms']:
            if not base['platforms'][platform]:
                continue
            path = os.path.join(base['paths']['packs'], platform, MCversion)

            packTomlPath = os.path.join(path, 'pack.toml')
            with open(packTomlPath, 'r') as file:
                packData = file.read()
            packData = re.sub(r'author = "[^"]+"','author = "'+base['general']['author']+'"', packData)
            packData = re.sub(r'name = "[^"]+"','name = "'+base['general']['name']+'"', packData)
            packData = re.sub(r'version = "[^"]+"','version = "'+modpackVersions['versions'][MCversion]+'"', packData)
            with open(packTomlPath, 'w') as file:
                file.write(packData)

base = ReadConfig(os.path.join('config', 'base.ini'))
modpackVersions = ReadConfig(os.path.join('config', 'versions.ini'))
for MCversion in base['minecraft']['versions']:
    modpackVersions['update'][MCversion] = 'none'
parentConfig = ReadConfig(os.path.join('config', 'parent.ini'))

InitialDirSetup()

GitLatestParent()

with open(os.path.join('config', 'mods.yml'), 'r') as f:
    mods = yaml.load(f, Loader=yaml.FullLoader)
AddYmlModsToAll(mods)

UpdatePackData()

WriteConfig(modpackVersions, os.path.join('config', 'versions.ini'))
