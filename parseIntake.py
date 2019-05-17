import csv
import xml.etree.ElementTree as ET
import os
import sys

class LabelsAndHelpText:
    def __init__(self, labels, helpText):
        self.labels = labels
        self.helpText = helpText

# parses through the SKUID XML to pull all of the models, the SF objects they're based on, and their field names and 
# labels (if the default labels are overridden in SKUID)
def parseXML(xmlfile):
    if xmlfile.endswith('.xml'):
        print('file: ' + xmlfile)
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
        
        labelsAndHelpText = getLabelsAndHelpText(root)
        labels = labelsAndHelpText.labels
        helpText = labelsAndHelpText.helpText

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
    else:
        sys.exit("the file type must be .xml")

# get all field labels that overwrite the SF standard
def getLabelsAndHelpText(root):
    labels = []
    helpText = []
    fieldEditors = list(root.iter('basicfieldeditor'))
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
            for label in field.iter('label'):
                labelData = {
                    "name" : label.text,
                    "model" : fieldEditor.get('model'),
                    "field" : field.get('id')
                }
                labels.append(labelData)
    return LabelsAndHelpText(labels, helpText)

# write all of the captured data into a csv file
def writeCSV(input):
    output = [['Field Name', 'Field Label', 'Model', 'Object', "UI-Only", "UI-Only Formula", "Show Inline Help"]]
    for item in input:
        for field in item['fields']:
            label = field["label"] if 'label' in field.keys() else ''
            uiOnly = field["uiOnly"] if 'uiOnly' in field.keys() else ''
            formula = field["formula"] if 'formula' in field.keys() else ''
            helpText = field["helpText"] if 'helpText' in field.keys() else ''
            csvData = [field["apiName"], label, item['name'], item['object'], uiOnly, formula, helpText]
            output.append(csvData)   
    filename = 'intakeXMLResults.csv'
    #remove file if it already exists
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(output)
    csvFile.close()

# main method
if (__name__ == '__main__'):
    if sys.argv[1:] is None:
        parseXML('intake.xml')
    else:
        parseXML(sys.argv[1])