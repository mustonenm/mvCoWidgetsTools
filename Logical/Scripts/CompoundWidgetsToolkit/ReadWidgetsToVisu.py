import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
import json
import sys

def extract_compound_widget_attributes(xml_file):
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

#This will open the found widgets file and convert it into stripped content string with only widgets data
def convertCompoundWidgetXMLToContentXML(original_file_path, WidgetName):

    #Extract ID, Width and Height for new content
    attributes = extract_compound_widget_attributes(original_file_path)

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

    # Create the new root for the simplified XML using string concatenation
    # simplified_xml = f'''<?xml version="1.0" encoding="utf-8"?>\n<Content id="{attributes["id"] + '_content'}" height="{attributes["height"]}" width="{attributes["width"]}" xmlns="http://www.br-automation.com/iat2015/contentDefinition/v2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    simplified_xml = f'''<?xml version="1.0" encoding="utf-8"?>\n<Content id="{WidgetName + '_content'}" height="{attributes["height"]}" width="{attributes["width"]}" xmlns="http://www.br-automation.com/iat2015/contentDefinition/v2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    {widgets_data}</Content>'''

    #Replace the last tab
    simplified_xml = simplified_xml.replace("\t</Content>", "</Content>")

    # Return the simplified XML
    return simplified_xml

# Parse the XML
def remove_objects_from_pkg_xml(root,namespace):

    # Find all Objects and remove them
    objects = root.find('ns:Objects', namespace)
    if objects is not None:
        for obj in list(objects):
            objects.remove(obj)

# Function to add an Object to element tree
def add_object_to_pkg_xml(root, namespace, new_object):
    objects = root.find('ns:Objects', namespace)

    if objects is not None:
        # Parse the new object
        new_obj_elem = ET.fromstring(new_object)
        
        # Check if the object already exists
        for obj in objects:
            if obj.text == new_obj_elem.text:
                return

        objects.append(new_obj_elem)

#mappView widgets page is mandatory for displaying the created content in mappView
def createMappViewWidgetPkg(file_path):

    pkgPath = file_path + 'Package.pkg'

    #Create XML content for "Empty package"
    new_object = f'''<?xml version="1.0" ?><Package xmlns="http://br-automation.co.at/AS/Package" SubType="PagePackage" PackageType="PagePackage"><Objects></Objects></Package>'''

    # Parse the XML data
    root = ET.fromstring(new_object)

    # Extract registered namespace
    namespaceExt = root.tag[1:root.tag.index('}')]
    # Register namespace 
    ET.register_namespace("", namespaceExt)
    # Define the namespaces
    namespace = {'ns': namespaceExt}

    # "Dummy" Page is always used --> so add that first to objects
    new_object = '<Object Type="File" Description="Page description">Page.page</Object>'
    add_object_to_pkg_xml(root, namespace, new_object)
    
    #Files to be listed to package, ending with file extension .content
    fileExtensions = ('.content')
    #Go trough files in the directory
    for rootDir, dirs, files in os.walk(file_path):
        for file in files:
            if file.endswith(fileExtensions):
                # Add found content to package
                new_object = f'''<Object Type="File" Description="{file} compound widget content">{file}</Object>'''
                add_object_to_pkg_xml(root, namespace, new_object)

    #Create xml
    pkg_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')

    #Make it shiny
    dom = xml.dom.minidom.parseString(pkg_xml)
    pkg_pretty_xml = dom.toprettyxml()

    # Write shiny XML to pkg file
    with open(pkgPath, 'w') as new_file:
        new_file.write(pkg_pretty_xml)

#mappView widgets package is mandatory for displaying the created content in mappView (Package.pkg)
def createMappViewWidgetPage(file_path,LayoutID):
    pkgPath = file_path + 'Page.page'

    page_xml = f'''<?xml version="1.0" encoding="utf-8"?><pdef:Page xmlns:pdef="http://www.br-automation.com/iat2015/pageDefinition/v2" id="CompoundWidgetsPage" layoutRefId="{LayoutID}"><Assignments><!--<Assignment type="" baseContentRefId="" areaRefId="" /> --></Assignments></pdef:Page>'''

    #Make it shiny
    dom = xml.dom.minidom.parseString(page_xml)
    page_pretty_xml = dom.toprettyxml()

    # Write shiny XML to pkg file
    with open(pkgPath, 'w') as new_file:
        new_file.write(page_pretty_xml)

#mappView widgets package is mandatory for displaying the created content in mappView (Package.pkg)
def createMappViewWidgetsFolder(file_path, LayoutID):
    pkgPath = file_path + '\\Package.pkg'
    FolderPath = file_path + '\\CompoundWidgetsPage\\'

    if not os.path.exists(FolderPath):
        os.makedirs(FolderPath)

    # Parse the XML data
    tree = ET.parse(pkgPath)
    root = tree.getroot()  # Get the root element of the XML file
    # Extract registered namespace
    namespaceExt = root.tag[1:root.tag.index('}')]
    # Register namespace 
    ET.register_namespace("", namespaceExt)
    # Define the namespaces
    namespace = {'ns': namespaceExt}
    # Add CompoundWidgetsPage to mappView package 
    new_object = f'''<Object Type="Package" Description="Compound widgets page">CompoundWidgetsPage</Object>'''
    add_object_to_pkg_xml(root, namespace, new_object)
    
    #Create xml string
    pkg_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')
    #Make it shiny
    dom = xml.dom.minidom.parseString(pkg_xml)
    pkg_pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove blank lines
    lines = [line for line in pkg_pretty_xml.splitlines() if line.strip()]
    pkg_pretty_xml = "\n".join(lines)

    # Write shiny XML to pkg file
    with open(pkgPath, 'w') as new_file:
        new_file.write(pkg_pretty_xml)

    #create content to new folder
    createMappViewWidgetPage(FolderPath, LayoutID)


def create_content_from_widgets(WidgetsDir, FindFilePrefix, VisuRootDir):
    """
    Lists all files with a specific prefix in the specified directory and creates new files for each match in a different directory.
    The new files are named using the subdirectory name and given prefix.

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
    
    #Visu Pages path
    pages_path = VisuRootDir + '\\Pages'
    #Compound widgets path
    new_content_output_path = pages_path + '\\CompoundWidgetsPage\\'
    #Fetch some sayout name for the mandatory "Dummy"-page
    layouts_path = VisuRootDir + '\\Layouts'
    for LayoutPath, LayoutPathDirs, LayoutFiles in os.walk(layouts_path):
        for LayoutFile in LayoutFiles:
            if LayoutFile.endswith('.layout'):
                attributes = extract_compound_widget_attributes(LayoutPath + '\\' + LayoutFile)
                LayoutID = attributes['id']
                break
                # if file.startswith(FindFilePrefix):

    createMappViewWidgetsFolder(pages_path,LayoutID)

    for WidgetPath, WidgetPathDirs, WidgetFiles in os.walk(WidgetsDir):
        for file in WidgetFiles:
            if file.startswith(FindFilePrefix):
                original_file_path = os.path.join(WidgetPath, file)
                # print(original_file_path)

                # Extract subdirectory name
                relative_path = os.path.relpath(WidgetPath, WidgetsDir)
                subdirectory_name = relative_path.replace(os.path.sep, "_") or "root"
                #extract the WidgetName --> it will be used for content naming for widget content
                WidgetName = WidgetPath.split('\\')[-1]
                compoundXMLContent = convertCompoundWidgetXMLToContentXML(original_file_path,WidgetName)
                # print(compoundXMLContent)

                # Create new file name with subdirectory name and new prefix
                # new_file_name = f"{new_prefix}{subdirectory_name}_{file}"
                new_file_name = f"{subdirectory_name}{'.content'}"
                new_file_path = os.path.join(new_content_output_path, new_file_name)

                # Write to the new file
                with open(new_file_path, 'w') as new_file:
                    new_file.write(f"{compoundXMLContent}\n")

                createMappViewWidgetPkg(new_content_output_path)

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
        print("Settings file not found. Creating default settings.")
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

    visu_path = trimmed_LogicalPath + '\\mappView'
    # Paths from settings
    visu_name = settings["visu_name"]
    widgets_library_name = settings["widgets_library_name"]

    # Get user input for the directory path
    WidgetsDir =  visu_path + '\\Widgets\\' + widgets_library_name
    
    # Get user input for the prefix
    FindFilePrefix = 'Widget.'

    # Get user input for the output directory
    VisuRootDir = visu_path + '\\'  +  visu_name

    # Call the function to list files and create new ones
    create_content_from_widgets(WidgetsDir, FindFilePrefix, VisuRootDir)
