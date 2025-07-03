from xml.dom.minidom  import  parse
from xml.dom import minidom, Node
from tqdm.notebook import tqdm
from nltk.tokenize import sent_tokenize
import re


class AkomaNtosoParser():
    """
    A parser for Akoma Ntoso files, which extracts and processes the contents of these files.
    """
    def __init__(self):
        """
        Initializes the parser, preparing it for use.
        """
        pass
    
    def get_body(self, file: str) -> None:
        """
        Extracts the body element of the Akoma Ntoso file specified by the provided file path.
        
        Args:
            file (str): The path to the Akoma Ntoso file to be parsed.
        """
        # Parse Akoma Ntoso document 
        document = parse(file)
        # Extracting the body element in the document tree 
        self.body = document.getElementsByTagName('body')[0]

    def get_p_tags(self) -> None:
        """
        Extracts the top-level paragraph elements from the body element of the Akoma Ntoso file.
        """
        # Body is a node element. Identify the branch that has a leaf with a p element  
        text_elements = self.body.getElementsByTagName('p')

        # Manage nested p tags by discarding those at a lower level.
        top_level_p_nodes = []
        for text_element in text_elements:
            # If it is a top-level p node, append the item to the list 
            if self.is_top_level(text_element):
                top_level_p_nodes.append(text_element)

        # Here I also need to get rid of those having a qstr eId, as not relevant
        
        self.p_elements = top_level_p_nodes

    def is_top_level(self, node: minidom.Element) -> bool:
        """
        Determines whether a paragraph element is a top-level element in the XML tree.
        
        Args:
            node (minidom.Element): The element to be checked.
        
        Returns:
            bool: True if the element is a top-level element, False otherwise.
        """
        if node.parentNode.nodeType != Node.DOCUMENT_NODE:
            if node.parentNode.tagName =='content':
                return True
            elif node.parentNode is not None:
                if node.parentNode.tagName == 'p':
                    return False
                elif node.parentNode.tagName != 'p':
                    return self.is_top_level(node.parentNode)
            elif node.parentNode is None: # This is the root document node
                return True
            else:
                return False
        return True
    
    def extract_provisions(self) -> list[dict]:
        """
        Extracts individual sentences from the paragraph elements and returns a list of dictionaries containing the CELEX ID, the sentence text, and the corresponding eId.
        
        Returns:
            list[dict]: A list of dictionaries, each representing a provision with its CELEX ID, sentence text, and eId.
        """
        provisions = []
        # Process the elements 
        for p_element in tqdm(self.p_elements, desc='Processing elements' , leave=False):
            eId, sentences = self.process_element(p_element)        
            
            for sentence in sentences:
                provision = {
                    "celex": self.celex,
                    "eId": eId,
                    "sentence": sentence,
                }
                provisions.append(provision)
    
        return provisions
            
    
    def process_element(self, element: minidom.Element):
        """
        Processes a given XML element to extract its address within the document (eId) and the text.
        
        Args:
            element (minidom.Element): The element to be processed.
        
        Returns:
            tuple[str, list[str]]: A tuple containing the eId and a list of sentences extracted from the element.
        """
        eId = self.get_eId(element)

        element, refs, dates = self.mask_references_and_dates(element)

        text = self.merge_dom_children(element)        
        if text is None:
            return []
        sentences = self.process_text(text)

        sentences = self.unmask_element(sentences, refs, dates)
            
        return eId, sentences

    def unmask_element(self, sentences: list[str], refs: list[str], dates: list[str]) -> list[str]:
        """
        Replaces masked references and dates in the extracted sentences with their original values.
        
        Args:
            sentences (list[str]): The list of sentences to be unmasked.
            refs (list[str]): The list of masked references.
            dates (list[str]): The list of masked dates.
        
        Returns:
            list[str]: The list of unmasked sentences.
        """
        # I guess this could be improved @todo
        for sentence in sentences:
            replaced_sentence = sentence
            for ref in refs:
                key = ref.split(":")[0]
                content = ref.split(":")[1]                
                if key in sentence:
                    replaced_sentence = re.sub(key, content, replaced_sentence)
            
            for date in dates:
                key = date.split(":")[0]
                content = date.split(":")[1]                
                if key in sentence:
                    replaced_sentence = re.sub(key, content, replaced_sentence)

            replaced_sentence = re.sub(r'\s{2}\s*', ' ', replaced_sentence)            
            sentences[sentences.index(sentence)] = replaced_sentence
            
        
        return sentences
    
    def merge_dom_children(self, element: minidom.Element) -> str:
        """
        Recursively concatenates the node values of an XML element and its children.
        
        Args:
            element (minidom.Element): The element to be processed.
        
        Returns:
            str: The concatenated text of the element and its children.
        """
        if element.nodeValue != None:
            return element.nodeValue
        else:
            value = ""
            for child in element.childNodes:
                value += self.merge_dom_children(child)
            return value.strip()
    
    def process_text(self, text: str) -> list[str]:
        '''
        Tokenizes the provided text into individual sentences.
        
        Args:
            text (str): The text to be tokenized.
        
        Returns:
            list[str]: A list of individual sentences.
        '''
        text = re.sub(r'\s{2}\s*', ' ', text) # Replace multiple whitespaces with a single whitespace (e.g., linebreaks followed by whitespaces)
        return sent_tokenize(text)

    def get_eId(self, element: minidom.Element) -> str:
        '''
        Extracts the eId attribute from an element or its parents, or empty if none is found
        
        Args:
            element (minidom.Element): The element to be processed.
        
        Returns:
            str: The eId attribute of the element or its parents, or an empty string if none is found.
        '''
        node = element
        eId = None
        while node is not None and eId is None:
            if hasattr(node, 'hasAttribute') and node.hasAttribute('eId'):
                eId = node.getAttribute('eId')
                return eId
            node = node.parentNode
        return ''
    
    def get_celex(self, celex: str) -> None:
        """
        Sets the CELEX identifier for the parser.
        
        Args:
            celex (str): The CELEX identifier to be set.
        """
        self.celex = celex

    # Mask date and ref into key : value
    def mask_element_by_tag(self, doc, tag_name, celex):
        """
        Masks references and dates in the XML document by replacing them with temporary placeholders.
        
        Args:
            doc (xml.dom.minidom.Document): The XML document to process.
            tag_name (str): The name of the XML tag to mask (e.g. 'ref' or 'date').
            celex (str): A unique identifier for the document, used to create temporary placeholders.
        
        Returns:
            tuple: A tuple containing the modified XML document and a list of masked elements.
                - doc (xml.dom.minidom.Document): The modified XML document with references and dates replaced with placeholders.
                - tmp (list): A list of strings, where each string represents a masked element in the format "placeholder: original_value".
        """
        tmp = []
        for index, element in enumerate(doc.getElementsByTagName(tag_name)):
            tag = celex + '_' + tag_name + str(index).zfill(2)            
            tmp.append(tag + ': ' + element.firstChild.data)
            element.firstChild.data = str(' ' + tag + ' ')
        return doc, tmp
    
    def mask_references_and_dates(self, element):
        """
        Masks references and dates in the given XML element.

        Parameters:
            element (xml.dom.minidom.Element): The XML element to process.

        Returns:
            tuple: A tuple containing the modified XML element and two lists of masked elements.
                - element (xml.dom.minidom.Element): The modified XML element with references and dates replaced with placeholders.
                - refs (list): A list of strings, where each string represents a masked reference in the format "placeholder: original_value".
                - dates (list): A list of strings, where each string represents a masked date in the format "placeholder: original_value".
        """
        
        element, refs = self.mask_element_by_tag(element, 'ref', self.celex)
        element, dates = self.mask_element_by_tag(element, 'date', self.celex)
        
        return element, refs, dates
