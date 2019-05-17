import csv
import xml.etree.ElementTree as ET
import os

# parses through the SKUID XML to pull all of the models, the SF objects they're based on, and their field names and 
# labels (if the default labels are overridden in SKUID)
def parseXML(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    data = []
    """ The following is the format of the data list
    data = [
        model = {
            "object": String,           the SF object that the model is based on
            "name": String,             the name of the model in SKUID
            "fields":[{                 the fields within the model
                "apiName": String,      the field API name
                "label": String,        the custom field label (if overridden in SKUID)
                "uiOnly": Boolean,      marks if the field is a UI-Only field
                "formula": String       the formula if the field is a UI-Only formula field
                "helpText: Boolean      marks if the field has "Show Inline Help" checked or not
            }]
        }
    ]
    """
    #grab all models and their objects and field api names
    for model in root.find('models'):
        modelData = {}
        fields = []
        modelData["name"] = model.get('id')
        modelData["object"] = model.get('sobject')
        for field in model.iter('field'):
            fieldData = {}
            name = field.get('id')
            uiOnly = field.get('uionly')
            if uiOnly is not None:
                fieldData["uiOnly"] = uiOnly
                if field.get('displaytype') == 'FORMULA':
                    formula = field.find('formula')
                    fieldData["formula"] = formula.text
            if name is not None:
                fieldData["apiName"] = name
                fields.append(fieldData)
        modelData["fields"] = fields
        data.append(modelData)
    
    labels = getLabels(root)
    helpText = getHelpText(root)

    #match labels and helptext with their respective fields
    for item in data:
        for field in item["fields"]:
            for help in helpText:
                if help["field"] == field["apiName"] and help["model"] == item["name"]:
                    field["helpText"] = help["value"]
            for label in labels:
                if label["field"] == field["apiName"] and label["model"] == item["name"]:
                    field["label"] = label["name"]

    writeCSV(data)

#get all field help text booleans
def getHelpText(root):
    helpText = []
    fieldEditors =list(root.iter('basicfieldeditor'))
    for fieldEditor in fieldEditors:
        for field in fieldEditor.iter('field'):
            helpTextValue = field.get('showhelp')
            if helpTextValue is not None:
                helpTextData = {
                    "value": helpTextValue,
                    "model": fieldEditor.get("model"),
                    "field": field.get('id')
                }
                helpText.append(helpTextData)
    return helpText


# get all field labels that overwrite the SF standard
def getLabels(root):
    labels = []
    fieldEditors = list(root.iter('basicfieldeditor'))
    for fieldEditor in fieldEditors:
        for field in fieldEditor.iter('field'):
            for label in field.iter('label'):
                labelData = {
                    "name" : label.text,
                    "model" : fieldEditor.get('model'),
                    "field" : field.get('id')
                }
                labels.append(labelData)
    return labels

# write all of the captured data into a csv file
def writeCSV(input):
    output = [['Field Name', 'Field Label', 'Model', 'Object', "UI-Only", "UI-Only Formula", "Show Inline Help"]]
    for item in input:
        for field in item['fields']:
            label = ''
            uiOnly = ''
            formula = ''
            helpText = ''
            # if the field has a SKUID overridden label
            if 'label' in field.keys():
                label = field["label"]
            # if the field is UI only
            if 'uiOnly' in field.keys():
                uiOnly = field["uiOnly"]
            # if the field is a UI Only formula field
            if 'formula' in field.keys():
                formula = field["formula"]
            # if the field has "Show Inline Help" checked
            if 'helpText' in field.keys():
                helpText = field["helpText"]
            csvData = [field["apiName"], label, item['name'], item['object'], uiOnly, formula, helpText]
            output.append(csvData)   

    filename = 'intakeXMLResults.csv'

    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(output)
    csvFile.close()

# main method
if (__name__ == '__main__'):
    parseXML('intake.xml')