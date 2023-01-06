from pathlib import Path
import os
import json
from utils.CRQM.CRQM import CRQMClient, get_xml_tree, BytesIO
from pprint import pprint

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


def get_testscript_template():
    template_path =  os.path.join(CURRENT_DIR, 'template.json')
    with open(template_path, encoding='utf-8') as f:
        content = f.readlines()
    return content


if __name__ == '__main__':
    # RQMclient = CRQMClient("ets1szh", "estbangbangde5",
    #                     "Zeekr", "https://rb-alm-20-p.de.bosch.com")
    # print("login", RQMclient.login())
    # print(get_script_from_testcase(RQMclient=RQMclient, id=168807))
    # RQMclient.disconnect()
    print(get_testscript_template())