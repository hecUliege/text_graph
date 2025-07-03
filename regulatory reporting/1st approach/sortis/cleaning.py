# Licensed under the EUPL, Version 1.2 or -- as soon they will be approved by the European Commission -- subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#  
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12/
#  
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the Licence for the specific language governing permissions and limitations under the Licence.

import xml.etree.ElementTree as ET
import os
import pandas as pd
import requests

def get_xml_files(folder_path):
    """
    Get all the files from a folder and return a list of them
    """
    xml_files = []
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for file in files:
            xml_files.append(file)
    
    return xml_files


def get_obligations(file):    
    # Load the XML file
    tree = ET.parse(file)
    root = tree.getroot()
    # Iterate over all ReportingObligation elements
    url = root.find(".//url").text
    texts = []
    for reporting_obligation in root.findall('.//ReportingObligation'):
        # Extract the text within the ReportingObligation element
        text = reporting_obligation.text
        texts.append(text)
    df = pd.DataFrame()
    df['text'] = texts
    df['url'] = url
    return df

def download_rdf_notice(url):
    """
    Parameters
        url (str): The URL of the RDF file to download.
    Returns
        response.content (bytes): The contents of the downloaded RDF file.
    """
    response = requests.get(url, headers={"Accept": "application/rdf+xml", "Accept-Language": "eng"})
    return response.content


def extract_celex(notice):
    RDF = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}
    OWL = {"owl": "http://www.w3.org/2002/07/owl#"}
    if b"celex/" in notice:
        # Parse the XML string into a tree            
        tree = ET.fromstring(notice)
        descriptions = tree.findall('.//rdf:Description', RDF)
        # Iterate over each Description element
        for description in descriptions:
            items = description.findall(".//owl:sameAs", OWL)
            for item in items:
                url = item.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                if "celex/" in url:
                    return url.split("/")[-1].split(".")[0]
                else:
                    continue
    else:
        return None


