from pathlib import Path
import os
from lxml import etree
import json
import datetime
from concurrent.futures import ThreadPoolExecutor
from utils.core.CRQM.CRQM import CRQMClient, get_xml_tree, BytesIO

CURRENT_DIR = Path(__file__).resolve().parent
SOURCE = os.path.join(CURRENT_DIR, 'source')

def _extractText(field):
    results = []
    if field.getchildren():
        if field.text:
            results.append(field.text)
        for p in field.getchildren():
            results.append(_extractText(p))
    else:
        if field.text:
            results.append(field.text)
        elif field.tail:
            results.append(field.tail)
        else:
            print("No text found!")
            
    return '\n'.join(results)


def _check_charset(file_path):
    import chardet
    with open(file_path, "rb") as f:
        data = f.read(4)
        charset = chardet.detect(data)['encoding']
    return charset


def util_generate_rdp_file(ip):
    file = os.path.join(SOURCE, 'template.rdp')
    with open(file, 'r', encoding=_check_charset(file)) as f:
        content = f.read()
        return content.format(ip)
    

def validateJsonTemplate(data):
    DEFAULTKEYS = {'title', 'scripts'}
    OPTIONALKEYS = {'category'}
    STEPKEYS = {'description', 'expectedResult'}
    CATEGORYKEYS = {
        'Field Against',
        'ASIL relevant',
        'Test Type',
        'Planned For',
        'Carline',
        'Execution Type',
        'Testable',
        'BRT Level',
        'Test Level'
    }
    if set(data.keys()) == DEFAULTKEYS:
        scripts = data['scripts']
        if isinstance(scripts, list):
            for step in scripts:
                if not set(step.keys()) == STEPKEYS:
                    return {'error': 'Invalid scripts keys!'}
        else:
            return {'error': 'Invalid scripts type, should be a list!'}
    elif set(data.keys()) == DEFAULTKEYS.union(OPTIONALKEYS):
        scripts = data['scripts']
        category = data['category']
        if isinstance(scripts, list):
            for step in scripts:
                if not set(step.keys()) == STEPKEYS:
                    return {'error': 'Invalid scripts keys!'}
        else:
            return {'error': 'Invalid scripts type!'}
        if isinstance(category, dict):
            keys = set(category.keys())
            for key in keys:
                if key not in CATEGORYKEYS:
                    return {'error': 'Invalid category keys!'}
        else:
            return {'error': 'Invalid category type, should be a dictionary!'}
    else:
        return {'error': 'Invalid keys!'}
    
    return True


def validateFile(file_path):
    extension = os.path.splitext(file_path)[1]
    if extension == '.json':
        try:
            with open(file_path) as f:
                data = json.load(f)
        except FileNotFoundError:
            raise Exception('File not found!')
        except json.JSONDecodeError:
            raise Exception('Invalid Json format!')
        except:
            raise Exception('Fail to load file!')
    else:
        raise Exception('Invalid file extension!')

    return data


def get_script_from_testcase(RQMclient, id: str):
    results = {}
    scripts = []
    RQMclient.login()

    # get testscript id and title
    res = RQMclient.getResourceByID('testcase', id).text
    oTree = get_xml_tree(BytesIO(str(res).encode()), bdtd_validation=False)
    nsmap = oTree.getroot().nsmap
    title = oTree.find('ns4:title', nsmap).text
    results['title'] = title

    testscript = oTree.find('ns2:testscript', nsmap)
    script_id = testscript.attrib['href'].split(':')[-1]
    testscriptURL = testscript.attrib['href']
    if len(testscriptURL.split(':')) < 3:
        script_id = testscriptURL.split('/')[-1]
    else:
        script_id = testscriptURL.split(':')[-1]
    # get descriptions and results from scripts
    res = RQMclient.getResourceByID('testscript', script_id).text
    oTree = get_xml_tree(BytesIO(str(res).encode()), bdtd_validation=False)
    steps = oTree.find(
        f'{{{CRQMClient.NAMESPACES["ns2"]}}}steps').getchildren()

    for step in steps:
        stepScript = {}
        stepScript['description'] = ''
        stepScript['expectedResult'] = ''

        description_field = step.find(
            f'{{{CRQMClient.NAMESPACES["ns8"]}}}description')
        if description_field is not None:
            stepScript['description'] = _extractText(description_field)

        expectedresults_field = step.find(
            f'{{{CRQMClient.NAMESPACES["ns8"]}}}expectedResult')
        if expectedresults_field is not None:
            stepScript['expectedResult'] = _extractText(expectedresults_field)

        scripts.append(stepScript)

    results['scripts'] = scripts
    RQMclient.disconnect()
    return results


def update_script_from_testcase(RQMclient: object, id: str, data: dict):
    RQMclient.login()
    
    try:
        res = RQMclient.getResourceByID('testcase', id).text
        oTree = get_xml_tree(BytesIO(str(res).encode()), bdtd_validation=False)
        nsmap = oTree.getroot().nsmap
        # change testcase title
        title = oTree.find('ns4:title', nsmap)
        title.text = data['title']
        testcaseTemplate = etree.tostring(oTree)

        # find testscript id
        testscript = oTree.find('ns2:testscript', nsmap)
        testscriptURL = testscript.attrib['href']
        if len(testscriptURL.split(':')) < 3:
            script_id = testscriptURL.split('/')[-1]
        else:
            script_id = testscriptURL.split(':')[-1]
    except:
        raise Exception('Unable to get testscript id!')

    try:
        testscriptTemplate = RQMclient.createTestscriptTemplate(
            testscriptName=f"{data['title']}_script", scripts=data['scripts'])
    except:
        raise Exception('Data is not valid!')

    response = RQMclient.updateResourceByID(
        'testcase', id, testcaseTemplate)
    response = RQMclient.updateResourceByID(
        'testscript', script_id, testscriptTemplate)
    
    RQMclient.disconnect()
    return response


def create_testcases(RQMclient: object, data: list):
    RQMclients = [RQMclient]*len(data)
    with ThreadPoolExecutor() as executor:
        response = executor.map(create_one_testcase, RQMclients, data)
    results = []
    for res in response:
        results.append(res)
        
    return results


def create_one_testcase(RQMclient: object, data: dict):
    RQMclient.login()
    # create testscript
    testscriptTemplate = RQMclient.createTestscriptTemplate(
            testscriptName=f"{data['title']} script", scripts=data['scripts'])
    result = RQMclient.createResource('testscript', testscriptTemplate)
    if result['success']:
        # create testcase and link testscript to testcase
        # there has to be a whitespace right after functional in Test Type
        testscriptID = result['id']
        if 'category' not in data:
            data['category'] = None

        testcaseTemplate = RQMclient.createTestcaseTemplate(
                testcaseName=data['title'], sTestscriptID=testscriptID, dCategory=data['category'])
        response = RQMclient.createResource('testcase', testcaseTemplate)
    else:
        return result
    
    RQMclient.disconnect()
    return response


def get_file_content(filename):
    file_path =  os.path.join(SOURCE, filename)
    if not os.path.exists(file_path):
        return
    with open(file_path, encoding='utf-8') as f:
        content = f.readlines()
    return content


def delete_file(filename):
    file_path =  os.path.join(SOURCE, filename)
    if not os.path.exists(file_path):
        return
    os.remove(file_path)
    return filename


def create_directory_if_not_exist(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)


def get_timezone() -> str:
    return str(datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)

class MyObject:
    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)

if __name__ == '__main__':
    # RQMclient = CRQMClient("ets1szh", "estbangbangde5",
    #                     "Zeekr", "https://rb-alm-20-p.de.bosch.com")
    # print("login", RQMclient.login())
    # print(get_script_from_testcase(RQMclient=RQMclient, id=168807))
    # RQMclient.disconnect()
    print(get_file_content('template.json'))