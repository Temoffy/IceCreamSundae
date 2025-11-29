import subprocess
import os
import shutil
import configparser
import json
import yaml
import re

#duplicate functions, but I'm lazy about 2 tiny functions
def ReadConfig(path):
    temp = configparser.ConfigParser()
    temp.read(path)
    
    returnDict = {}
    for i in temp.sections():
        returnDict[i] = {}
        for k in temp[i]:
            returnDict[i][k] = json.loads(temp[i][k])
    return returnDict

def UpdatePackData():
    for MCversion in base['minecraft']['versions']:
        for platform in base['platforms']:
            if not base['platforms'][platform]:
                continue
            path = base['paths']['litepacks']+'\\'+platform+'\\'+MCversion

            with open(path+'\\pack.toml', 'r') as file:
                packData = file.read()
            packData = re.sub(r'author = "[^"]+"','author = "'+base['general']['author']+'"', packData)
            packData = re.sub(r'name = "[^"]+"','name = "'+base['general']['litename']+'"', packData)
            packData = re.sub(r'version = "[^"]+"','version = "'+modpackVersions['versions'][MCversion]+'"', packData)
            with open(path+'\\pack.toml', 'w') as file:
                file.write(packData)

            subprocess.run(['xcopy','/E','/Y','.\\config\\overrides\\litepack',  '.\\'+path], shell=True, capture_output=True) #capture output prevents console flooding

if os.path.isdir('litepacks'):
    shutil.rmtree("litepacks")
os.mkdir("litepacks")
subprocess.run(['xcopy','/E','/Y','.\\packs',  '.\\litepacks'], shell=True,)# capture_output=True) #capture output prevents console flooding

base = ReadConfig('config\\base.ini')
modpackVersions = ReadConfig('config\\versions.ini')

with open('config\\liteVersionRemoveMods.yml', 'r') as f:
    removeMods = yaml.load(f, Loader=yaml.FullLoader)
for MCversion in base['minecraft']['versions']:
    print(MCversion)
    for platform in base['platforms']:
        if not base['platforms'][platform]:
            continue
        path = base['paths']['litepacks']+'\\'+platform+'\\'+MCversion

        for item in removeMods:
            name = ''
            if 'mr' in item:
                name = item['mr']
            else:
                name = item['mod']
            subprocess.run(['packwiz','remove',name], cwd=path, shell=True, capture_output=True)
        
UpdatePackData()