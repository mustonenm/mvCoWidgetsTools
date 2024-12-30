import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
from lxml import etree
import json
import sys

def extract_compound_widget_attributes_from_content(xml_file):
    """
    Extracts the 'id', 'width', and 'height' attributes from the CompoundWidget element in the XML file.

    :param xml_file: Path to the XML file.
    :return: A dictionary with the attributes 'id', 'width', and 'height'.
    """
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    if root.tag is None:
        print("Error: <CompoundWidget> element not found. File: " + xml_file)
        return None

    # Extract the attributes
    attributes = {
        "id": root.attrib["id"],
        "width": root.attrib["width"],
        "height": root.attrib["height"]
    }

    return attributes

def write_compound_widget_data(compoundWidgetFile,attributes,widgetsData):
    """
    Set the 'id', 'width', and 'height' attributes to given XML file.

    :param xml_file: Path to the XML file.
    :param attributes: attributes id,width and height.

    """
    # Open and read the XML file
    with open(compoundWidgetFile, "rb") as file:
        xml_content = file.read()

    # Parse the XML content by using lxml --> to preserve the formatting of the XML data!
    tree = etree.XML(xml_content)

    # Modify attributes
    if widgetID_rename_allowed:
        # root.attrib["id"] = attributes["id"]
        tree.set("id", attributes["id"])  # Change id attribute
    
    tree.set("width", attributes["width"])           # Change width attribute
    tree.set("height", attributes["height"])          # Change height attribute

    nsmap = {'ns': 'http://www.br-automation.com/iat2015/contentDefinition/v2'}

    # Locate the <Widgets> tag
    widgets = tree.find(".//ns:Widgets", namespaces=nsmap)

    # Remove the <Widgets> element completely
    if widgets is not None:
        parent = widgets.getparent()  # Get the parent element
        if parent is not None:
            parent.remove(widgets)  # Remove <Widgets> from its parent
    
    # Parse the new Widgets XML content
    new_widgets = etree.XML(widgetsData.encode('utf-8'))

    # Insert the new Widgets element at the beginning of the CompoundWidget
    compound_widget = tree  # The root element is <CompoundWidget>
    compound_widget.insert(0, new_widgets)  # Insert as the first child
    # Add a newline after the Widgets element
    new_widgets.tail = "\n\t"  # Add a newline after the closing </Widgets>

    # Serialize back to XML with formatting
    modified_xml = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="utf-8")

    # Write shiny XML to pkg file
    with open(compoundWidgetFile, 'wb') as new_file:
        new_file.write(modified_xml)

#This will open the found widgets file and convert it into stripped content string with only widgets data
def CopyWidgetsDataFromContent(original_file_path, widget_path):

    #Extract ID, Width and Height for new content
    attributes = extract_compound_widget_attributes_from_content(original_file_path)

    # Parse the XML data
    tree = ET.parse(original_file_path)
    root = tree.getroot()  # Get the root element of the XML file

    # Define the namespaces
    namespace = {'ns': 'http://www.br-automation.com/iat2015/contentDefinition/v2'}

    # Extract the "widgets" data
    widgets = root.findall('.//ns:Widgets', namespace)
    widgets_data = ''

    # Extract registered namespace 
    namespace = root.tag[1:root.tag.index('}')]
    # Register namespace 
    ET.register_namespace("", namespace)

    widgets_data = ET.tostring(widgets[0], encoding='unicode')
    # print(widgets_data)

    #Create xml string
    # widget_xml = ET.tostring(widgets[0], encoding='unicode').decode('utf-8')
    #Make it shiny
    dom = xml.dom.minidom.parseString(widgets_data)
    widget_pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove blank lines
    lines = [line for line in widget_pretty_xml.splitlines() if line.strip()]
    widget_pretty_xml = "\n".join(lines)

    #extract the WidgetName (=directory name) --> it will be used for bonding widget elements to content
    WidgetID = widget_path.split('\\')[-1]
    #Overwrite ID
    attributes["id"] = WidgetID

    write_compound_widget_data(widget_path + '\\Widget.compoundwidget',attributes, widgets_data)

    # print(widget_pretty_xml)

    # Write shiny XML to pkg file
    # with open(original_file_path + '.widget', 'w') as new_file:
    #     new_file.write(widget_pretty_xml)

    return widget_pretty_xml

def extract_widgets_data_from_content(WidgetsDir, FindFilePrefix, ContentDir):
    """
    List all files from content directory and export data to widgets files

    :param WidgetsDir: The compound widgets directory 
    :param FindFilePrefix: The prefix to searching widget files
    :param ContentDir: The directory where new content files for editing compound widgets is created
    """

    if not os.path.exists(WidgetsDir):
        print(f"Error: The specified path '{WidgetsDir}' does not exist.")
        return

    if not os.path.isdir(WidgetsDir):
        print(f"Error: The specified path '{WidgetsDir}' is not a directory.")
        return
    
    if not os.path.exists(ContentDir):
        print(f"Error: The specified path '{ContentDir}' does not exist.")
        return

    if not os.path.isdir(ContentDir):
        print(f"Error: The specified path '{ContentDir}' is not a directory.")
        return

    # if not os.path.exists(output_path):
    #     os.makedirs(output_path)

    print(f"Listing files with prefix '{FindFilePrefix}' in '{WidgetsDir}':")

    PathToCompoundWidgetsSourceContent = ContentDir + '\\CompoundWidgetsPage\\'

    for WidgetPath, WidgetPathDirs, WidgetFiles in os.walk(WidgetsDir):
        for Widgetfile in WidgetFiles:
            if Widgetfile.startswith(FindFilePrefix):
                # print(WidgetPath)
                #extract the WidgetName (=directory name) --> it will be used for bonding widget elements to content
                WidgetName = WidgetPath.split('\\')[-1]
                # print(WidgetName)
                # print(Widgetfile)

                WidgetContent = PathToCompoundWidgetsSourceContent + WidgetName + '.content'
                CopyWidgetsDataFromContent(WidgetContent,WidgetPath)


def load_settings(settings_file):
    """Load settings from a JSON file."""
    with open(settings_file, 'r') as file:
        return json.load(file)

def save_settings(settings_file, settings):
    """Save settings to a JSON file."""
    with open(settings_file, 'w') as file:
        json.dump(settings, file, indent=4)

if __name__ == "__main__":

    # try to load settings
    try:
        settings = load_settings(os.path.dirname(os.path.abspath(__file__)) + '\\Settings.json')
    except FileNotFoundError:
        print("Settings file not found")
        sys.exit(1)

    # Folder to stop at
    stop_folder = "Logical"
    original_path = os.path.dirname(os.path.abspath(__file__))

    # Find the position of the stop folder
    if stop_folder in original_path:
        # Trim everything after the stop folder
        trimmed_LogicalPath = original_path.split(stop_folder, 1)[0] + stop_folder
    else:
        # Handle cases where stop folder is not found
        print("Locigal directory not found from project path. Check script is locating inside of the AS project tree. Cannot continue.. Sorry")
        sys.exit(1)

    # Paths from settings
    visu_path = trimmed_LogicalPath + '\\mappView'
    visu_name = settings["visu_name"]
    widgetID_rename_allowed = settings["widgetID_rename_allowed"]
    widgets_library_name = settings["widgets_library_name"]

    # Get user input for the directory path
    WidgetsDir =  visu_path + '\\Widgets\\' + widgets_library_name
    
    # Get user input for the prefix
    FindFilePrefix = 'Widget.'

    # Get user input for the output directory
    ContentDir = visu_path + '\\'  +  visu_name + '\\Pages'

    # Call the function to list files and create new ones
    extract_widgets_data_from_content(WidgetsDir, FindFilePrefix, ContentDir)
