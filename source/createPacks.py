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

    for folder in base["paths"]:
        if not os.path.isdir(folder):
            os.makedirs(folder)

    path = base['paths']['packs']
    for platform in base['platforms']:
        if base['platforms'][platform]:
            if not os.path.isdir(path+'\\'+platform):
                os.makedirs(path+'\\'+platform)
            if not os.path.isdir('config\\overrides\\'+platform):
                os.makedirs('config\\overrides\\'+platform)
        
        for MCversion in base['minecraft']['versions']:
            if not os.path.isdir(path+'\\'+platform+'\\'+MCversion):
                os.makedirs(path+'\\'+platform+'\\'+MCversion)
                
                MakePack(MCversion, path+'\\'+platform+'\\'+MCversion)

                os.makedirs(path+'\\'+platform+'\\'+MCversion+'\\shaderpacks')
                os.makedirs(path+'\\'+platform+'\\'+MCversion+'\\resourcepacks')
                os.makedirs(path+'\\'+platform+'\\'+MCversion+'\\config')
                os.makedirs(path+'\\'+platform+'\\'+MCversion+'\\mods')

            if not os.path.isdir('config\\overrides\\'+platform+'\\'+MCversion):
                os.makedirs('config\\overrides\\'+platform+'\\'+MCversion)

                os.makedirs('config\\overrides\\'+platform+'\\'+MCversion+'\\shaderpacks')
                os.makedirs('config\\overrides\\'+platform+'\\'+MCversion+'\\resourcepacks')
                os.makedirs('config\\overrides\\'+platform+'\\'+MCversion+'\\config')
                os.makedirs('config\\overrides\\'+platform+'\\'+MCversion+'\\mods')


def MakePack(MCversion, path):
    if not MCversion in modpackVersions["versions"]:
        modpackVersions["versions"][MCversion] = MCversion+"-0.0" #will become 1.0 because of the next line
        modpackVersions['update'][MCversion] = 'major'

    opt = base["general"]
    test = subprocess.run(["packwiz","init",
                           "--author",opt["author"],
                           "--"+opt["loader"]+"-latest", #loader version selection
                           "--mc-version", MCversion,
                           "--modloader",opt["loader"],
                           "--name", opt["name"],
                           "--version", modpackVersions["versions"][MCversion]
                           ], cwd=path, shell=True, capture_output=False)

#check in with the parent modpack for updates
def GitLatestParent():
    repo_url = "https:\\\\github.com\\Fabulously-Optimized\\fabulously-optimized"
    parentPacksPath = base["paths"]["parent"]+"\\Packwiz"
    
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

        path = parentPacksPath+"\\"+MCversion
        
        #read in version strings of the parent modpack to detect updates
        regex = r"version = \"(\S+)\""
        with open(path+"\\pack.toml", "r") as f:
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
                updatetype = UpdatePackFromParent(platform, base['paths']['packs']+'\\'+platform+'\\'+MCversion, path)
                versionUpdate(updatetype, MCversion)
        parentConfig['refVersions'][MCversion] = testVers
        
    WriteConfig(parentConfig,'config\\parent.ini')

def UpdatePackFromParent(preferredPlatform, packPath, parentPath):

    #first check if the modlist changed
    #test = subprocess.run(["packwiz","init"], cwd=parentPath, shell=True, capture_output=False)
    parentRegex = r"(?: |,)\d+\ (.*?\.(?:pw\.toml|zip))"
    childRegex = r"(?: |,)\d+\ (.*?)\.(?:pw\.toml|zip)"
    updateType = 'none'
    for subfolder in ["mods","resourcepacks","shaderpacks"]:
        if not os.path.isdir(parentPath+'\\'+subfolder):
            continue

        parentListRaw = subprocess.run(['dir'], cwd=parentPath+'\\'+subfolder, shell=True, capture_output=True)
        parentList = re.findall(parentRegex,parentListRaw.stdout.decode())

        childListRaw = subprocess.run(['dir'], cwd=packPath+'\\'+subfolder, shell=True, capture_output=True)
        childList = re.findall(childRegex,childListRaw.stdout.decode())

        for item in parentList:
            if item.split('.')[1] != 'pw':
                #MANUAL OVERRIDE MOD ADDITIONS WILL NOT TRIGGER A MAJOR UPDATE
                subprocess.run(['copy', parentPath+'\\'+subfolder+'\\'+item,  packPath+'\\'+subfolder], shell=True, capture_output=False)
                continue
            item = item.split('.')[0]
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
            regex = item+r"\.(?:pw\.toml|zip|properties|json)"
            item = re.search(regex,parentListRaw.stdout.decode()).group()
            print(item)
            subprocess.run(['copy','.\\'+parentPath+'\\'+subfolder+'\\'+item,  '.\\'+packPath+'\\'+subfolder], shell=True, capture_output=False)
    #copy config
    subprocess.run(['xcopy','/E','/Y','.\\'+parentPath+'\\config',  '.\\'+packPath+'\\config'], shell=True, capture_output=True) #capture output prevents console flooding
    #cleanup
    delList = [packPath+'\\resourcepacks\\Mod Menu Helper.zip',
               packPath+'\\config\\isxander-main-menu-credits.json',
               packPath+'\\config\\yosbr\\config\\isxander-main-menu-credits.json',
               packPath+'\\mods\\capes.pw.toml']
    for delPath in delList:
        if os.path.exists(delPath):
            os.remove(delPath)
    if os.path.isdir(packPath+'\\config\\crash_assistant'):
        shutil.rmtree(packPath+'\\config\\crash_assistant')
    subprocess.run(['packwiz',"refresh"], cwd=packPath, shell=True, capture_output=True)
    
    with open(packPath+'\\config\\fabric_loader_dependencies.json', 'r') as file:
        filedata = file.read()
    regex = r'"Fabulously Optimized":"[^"]+"'
    filedata = re.sub(regex, '"IceCreamSundae":"*"', filedata)
    with open(packPath+'\\config\\fabric_loader_dependencies.json', 'w') as file:
        file.write(filedata)

    with open('config\\options.txt', 'r') as file:
        myoptions = file.read()
    with open(packPath+'\\config\\yosbr\\options.txt', 'r') as file:
        baseoptions = file.read()
    baseoptions = baseoptions +'\n'+myoptions
    with open(packPath+'\\config\\yosbr\\options.txt', 'w') as file:
        file.write(baseoptions)

    return updateType


def PackwizAdd(item, preferredPlatform, path):
    time.sleep(.5) #don't get rate limited
    regex = r"Failed|No projects found|Cancel"
    resultRaw = subprocess.run(['packwiz',preferredPlatform,'add',item,"-y"], cwd=path, shell=True, capture_output=True)
    result = re.findall(regex, resultRaw.stdout.decode())
    if len(result) == 0:
        return True
    for platform in base['platforms']:
        if not base['platforms'][platform] or platform == preferredPlatform:
            continue
        resultRaw = subprocess.run(['packwiz',platform,'add',item,"-y"], cwd=path, shell=True, capture_output=True)
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
        if os.path.isfile('.\\'+path+'\\missing.txt'):
            with open(path+'\\missing.txt', 'r') as file:
                filedata = file.read()
        filedata = filedata + item["mod"] + '\n'
        with open(path+'\\missing.txt', 'w') as file:
            file.write(filedata)
        continue
        #return False
    return AllAdded

def AddYmlModsToAll(data):
    childRegex = r"(?: |,)\d+\ (.*?)\.(?:pw\.toml|zip)"
    for MCversion in base['minecraft']['versions']:
        print(MCversion)
        for platform in base['platforms']:
            if not base['platforms'][platform]:
                continue
            path = base['paths']['packs']+'\\'+platform+'\\'+MCversion
            with open(path+'\\missing.txt', 'w') as file:
                file.write("")
            with open(path+'\\forceload.yml', 'w') as file:
                file.write("")
            
            #apply overrides
            subprocess.run(['xcopy','/E','/Y','.\\config\\overrides\\general',  '.\\'+path], shell=True, capture_output=True) #capture output prevents console flooding
            subprocess.run(['xcopy','/E','/Y','.\\config\\overrides\\'+platform+'\\'+MCversion,  '.\\'+path], shell=True, capture_output=True) #capture output prevents console flooding
            subprocess.run(['packwiz',"refresh"], cwd=path, shell=True, capture_output=True)

            currentMods = []
            for subfolder in ["mods","resourcepacks","shaderpacks"]:
                childListRaw = subprocess.run(['dir'], cwd=path+'\\'+subfolder, shell=True, capture_output=True)
                currentMods = currentMods + re.findall(childRegex,childListRaw.stdout.decode())
            
            ParseAddMods(data, platform, path, currentMods)

            #re-apply overrides, just in case
            subprocess.run(['xcopy','/E','/Y','.\\config\\overrides\\general',  '.\\'+path], shell=True, capture_output=True) #capture output prevents console flooding
            subprocess.run(['xcopy','/E','/Y','.\\config\\overrides\\'+platform+'\\'+MCversion,  '.\\'+path], shell=True, capture_output=True) #capture output prevents console flooding
            subprocess.run(['packwiz',"refresh"], cwd=path, shell=True, capture_output=True)

            with open(path+'\\forceload.yml', 'r') as f:
                forceloadList = yaml.load(f, Loader=yaml.FullLoader)
            
            if forceloadList:
                print("adding forceloads")
                with open(path+'\\config\\fabric_loader_dependencies.json', 'r') as file:
                    fabricLoaderConfig = file.read()
                for item in forceloadList:
                    if item in fabricLoaderConfig:
                        continue
                    fabricLoaderConfig = re.sub(r"}}}}","}},\n\""+item+"\":{\"-depends\":{\"minecraft\":\"IGNORED\"}}}}", fabricLoaderConfig)
                with open(path+'\\config\\fabric_loader_dependencies.json', 'w') as file:
                    file.write(fabricLoaderConfig)

def UpdatePackData():
    for MCversion in base['minecraft']['versions']:
        for platform in base['platforms']:
            if not base['platforms'][platform]:
                continue
            path = base['paths']['packs']+'\\'+platform+'\\'+MCversion

            with open(path+'\\pack.toml', 'r') as file:
                packData = file.read()
            packData = re.sub(r'author = "[^"]+"','author = "'+base['general']['author']+'"', packData)
            packData = re.sub(r'name = "[^"]+"','name = "'+base['general']['name']+'"', packData)
            packData = re.sub(r'version = "[^"]+"','version = "'+modpackVersions['versions'][MCversion]+'"', packData)
            with open(path+'\\pack.toml', 'w') as file:
                file.write(packData)

base = ReadConfig('config\\base.ini')
modpackVersions = ReadConfig('config\\versions.ini')
for MCversion in base['minecraft']['versions']:
    modpackVersions['update'][MCversion] = 'none'
parentConfig = ReadConfig('config\\parent.ini')

InitialDirSetup()

GitLatestParent()

with open('config\\mods.yml', 'r') as f:
    mods = yaml.load(f, Loader=yaml.FullLoader)
AddYmlModsToAll(mods)

UpdatePackData()

WriteConfig(modpackVersions,'config\\versions.ini')