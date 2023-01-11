from pathlib import Path
import os
from lxml import etree
from utils.CRQM.CRQM import CRQMClient, get_xml_tree, BytesIO
import json

CURRENT_DIR = Path(__file__).resolve().parent

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


def _validateJsonTemplate(data):
    DEFAULTKEYS = {'title', 'scripts'}
    OPTIONALKEYS = {'category'}
    STEPKEYS = {'descriptions', 'expectedResults'}
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
                    raise Exception('Invalid scripts keys!')
        else:
            raise Exception('Invalid scripts type!')
    elif set(data.keys()) == DEFAULTKEYS.union(OPTIONALKEYS):
        scripts = data['scripts']
        category = data['category']
        if isinstance(scripts, list):
            for step in scripts:
                if not set(step.keys()) == STEPKEYS:
                    raise Exception('Invalid scripts keys!')
        else:
            raise Exception('Invalid script type!')
        if isinstance(category, dict):
            keys = set(category.keys())
            for key in keys:
                if key not in CATEGORYKEYS:
                    raise Exception('Invalid category keys')
        else:
            raise Exception('Invalid category type!')
    else:
        raise Exception('Invalid keys!')


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

    if isinstance(data, list):
        for case in data:
            _validateJsonTemplate(case)
    elif isinstance(data, dict):
        _validateJsonTemplate(data)
    else:
        raise Exception('Invalid data format!')

    return data


def get_script_from_testcase(RQMclient, id: str):
    results = {}
    scripts = []

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
    return results


def update_script_from_testcase(RQMclient: object, id: str, data: dict):
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

    return response


def create_testcase_with_testscript(RQMclient: object, data: dict):
    # create testscript
    try:
        testscriptTemplate = RQMclient.createTestscriptTemplate(
            testscriptName=f"{data['title']}_script", scripts=data['scripts'])
    except:
        raise Exception('Data is not valid!')
    result = RQMclient.createResource('testscript', testscriptTemplate)

    # create testcase and link testscript to testcase
    # there has to be a whitespace right after functional in Test Type
    testscriptID = result['id']
    if 'category' not in data:
        data['category'] = None
    try:
        testcaseTemplate = RQMclient.createTestcaseTemplate(
            testcaseName=data['title'], sTestscriptID=testscriptID, dCategory=data['category'])
    except:
        raise Exception('Data is not valid!')
    response = RQMclient.createResource('testcase', testcaseTemplate)

    return response


def get_file_content(filename):
    file_path =  os.path.join(CURRENT_DIR, 'source', filename)
    with open(file_path, encoding='utf-8') as f:
        content = f.readlines()
    return content


def create_directory_if_not_exist(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)


if __name__ == '__main__':
    # RQMclient = CRQMClient("ets1szh", "estbangbangde5",
    #                     "Zeekr", "https://rb-alm-20-p.de.bosch.com")
    # print("login", RQMclient.login())
    # print(get_script_from_testcase(RQMclient=RQMclient, id=168807))
    # RQMclient.disconnect()
    print(get_file_content('template.json'))