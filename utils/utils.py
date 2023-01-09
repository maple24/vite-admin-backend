from pathlib import Path
import os
from lxml import etree
from utils.CRQM.CRQM import CRQMClient, get_xml_tree, BytesIO

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