# Licensed under the EUPL, Version 1.2 or -- as soon they will be approved by the European Commission -- subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#  
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12/
#  
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the Licence for the specific language governing permissions and limitations under the Licence.

from enum import Enum

import re
import spacy
import numpy as np
from sortis.mapping import findTime
from timexy import Timexy

spacy_model = spacy.load('en_core_web_lg')
spacy_model.add_pipe("merge_noun_chunks")

# A series of linguistic hints that could indicate the presence of an obligation
MODALS = ['shall', 'must', 'will']

# reporting verbs
REPORTING_VERBS = [
    'disclose', 'communicate', 'submit', 'publish', 'transmit', 'send', 'collect', 'publishes', 'notify', 'gather', 'declare',
    'survey', 'fill', 'report', 'inform', 'convey', 'relay', 'share', 'communicate', 'announce', 'describe',
    'chronicle', 'detail', 'broadcast', 'document', 'present', 'express', 'disclose', 'brief', 'record', 'pass on', 'transmit',
    'presented', 'inform',
    # These verbs result in a lot of false positives # 'provide', 
    ]

class SentenceType(Enum):
    """
    Class representing the type of text that may be encountered 

    Attributes:
        OBLIGATION: Represents sentences that imply an obligation.
        TO_INSPECT: Represents sentences that need further inspection.
        OTHER: Represents all other types of sentences.
    """
    OBLIGATION = 1
    TO_INSPECT = 2
    OTHER = 3

class TextInfo():
    """
    Represents the information about a text document.

    Attributes:
        celex (str): The CELEX number of the document.
        doc_number (str): The document number.
        metadata (dict): Additional metadata extracted from the eId.
    """       
    def __init__(self, celex: str, doc_number: str, e_id: str):
        self.celex = celex
        self.doc_number = doc_number
        self.metadata = self._parse_metadata(e_id)
    
    @staticmethod
    def _parse_metadata(e_id: str) -> list:
        """
        Parses metadata from the eId string.
        Args:
            e_id (str): The eId string to parse.
        Returns:
            List: A list of tuples containing eId information
        """
        metadata = []
        for data in e_id.split('__'):
            if data:
                key, value = data.split('_', 1)
                metadata.append((key, value))
        return metadata
    
class Text():
    # Regular expression pattern to match dates in the format "[number] [Month] [optional text]" 
    # Example: "1 March of the following financial year"
    DATE_REGEX = r"\d{1,2} ((January)|(February)|(March)|(April)|(May)|(June)|(July)|(August)|(September)|(October)|(November)|(December)).*"
    
    def __init__(self, text: str):
        """
        Initializes the Text class with a sentence, its full text, and associated text information.

        Args:
            sentence (str): The sentence to be analyzed.
            text (str): The full text that the sentence is a part of.
            info (TextInfo): An object containing metadata about the text.
        """
        self.text = text
        self.modal_idx = None
        self.verb_idx = None
        self.subj_idx = None
        self.dobj_idx = None
        self.pobj_idx = None
        self.sentence_type = None

        self.tree = spacy_model(text)
        self.passive = False
        self.subj = None
        self.subj_list = []
        self.pobj = None
        self.dobj = None
        self.date = None
        self.date_annotated = None
        self.pobj_list = []
        self.hasnext = None
        
        
        self.init_text()
        
        self.date = [self.date]
        self.dobj = [self.dobj]
        

        
    def init_text(self):
        '''
        Analyzes the sentence and uses a syntactic tree to initialize attributes
        (type, position of the modal and reporting verb, ...).
        '''

        # Finds the root of the sentence (main verb)
        root = self.find_root_verb()
        
        # if sentence has two verbs and first verb is not the main verb and second verb is the main verb (reporting verb) we use second verb as root
        second_verb = self.find_secondary_verb(root)
        
        # Check for reporting verbs
        if self.check_modal_node(root):
            # look for subparts of the sentences
            self.decompose_sentence(root, second_verb)
            # look for the date
            self.date = findTime(self.text.lower(), self.tree)            
            # Post Processing
            self.post_processing()

        self.find_date_old()


    def find_root_verb(self):
        root = self.tree[0]
        while root != root.head:
            root = root.head
        return root

    def find_secondary_verb(self, root):
        has_second_verb = False
        for child in root.rights:
            if child.pos_ == "CCONJ":
                has_second_verb = True
            if has_second_verb and child.pos_ == "VERB" and child.text in REPORTING_VERBS and root.text not in REPORTING_VERBS:
                return child
        return None


    def check_modal_node(self, root: spacy.tokens.token.Token) -> bool:
        """ 
        Function that recursively checks the tree

        Args:
        -----
        - `root`:

        Returns:
        --------
        True if found a reporting verb + modal
        """

        # analyze the root
        if root.lemma_ in REPORTING_VERBS:
            self.verb_idx = root.i


        for child in root.children:
            if child.dep_ == "aux" and child.lemma_ in MODALS:
                self.modal_idx = child.i       

            # A negative sentence is not considered to be a reporting obligation (e.g., "shall not submit")
            elif child.dep_ == "neg": 
                self.verb_idx = None
                self.modal_idx = None
                break

        # if found an obligation ==> return True
        if self.modal_idx is not None and self.verb_idx is not None:
            return True

        # loop through the children of the local root and look for conj
        for child in root.children:
            if child.dep_ == "conj" or child.dep_ == "pcomp":
                res = self.check_modal_node(child)

                # return True as soon as a recursive call is successful
                if res:
                    return res
                
        return False

    def decompose_sentence(self,root: spacy.tokens.token.Token, root2: spacy.tokens.token.Token) -> None:
        """ 
        Function to find the different parts (subject, direct object
        pobj) of the sentence

        The function updates related attributes in the class

        Args:
        -----
        - `root` (Token): root of the spacy tree

        Returns:
        --------
        None
        """
        # Look for the subject or the dobj (if passive) in the left side of the tree
        for child in root.lefts:
            if child.dep_ == "nsubj":
                self.subj, self.subj_idx = self.subtree_str(child)
                self.passive = False
            elif child.dep_ == "nsubjpass":
                self.passive = True
                self.dobj, self.dobj_idx = self.subtree_str(child)

        # If the subject is not found previously, it might be attached to the modal instead of the verb
        if self.subj is None and self.modal_idx is not None:
            for child in self.tree[self.modal_idx].lefts:
                if child.dep_ == "nsubj":
                    self.subj, self.subj_idx = self.subtree_str(child)
                    break
        # print('active or passive: ', str(self.passive))
        # Passive Form  (new code )  
        
        # If sentence has two verbs and second verb is a main verb and first verb is not a main verb, we change root to second verb        
        if root2 is not None:
            root = root2
                
        if self.passive == True:   
            for child in root.rights:
                # Action did By WHO (self.subj)
                if child.text == "by" and child.pos_ == "ADP":
                    for ch in child.rights:
                        self.subj = ch.text
                ## Result to WHOM (self.pobj)
                elif child.text == "to" and child.pos_ == "ADP":
                    for ch in child.rights:
                        # to WHOM
                        self.pobj = ch.text
                        # print('ch: ', ch.text)
                        ##Verb_reported to WHOM (addressee), by  WHO (addresser) ex: reported to EU by member.
                        for c in ch.subtree:
                            if self.subj is None and c.dep_ == "pobj" and c.head.text == 'by':
                                # print('self.subj', c.text)
                                self.subj = c.text
        # Active Form
        elif self.passive == False:
            # Look for the pobj and the dobj or the subject (if passive) in the right side of the tree
            for child in root.rights:
                if child.dep_ == "dobj":
                    # print('child.dep dobj: ', child.text)
                    try:
                        subtree = list(child.subtree)
                        # print('try: ', subtree)
                        pobj = next(filter(lambda x: x.dep_ == "prep" and x.text == "to", subtree))
                        self.dobj = self.tree[child.i : pobj.i].text
                        
                        # Find part of pobj that compose with prep. on about. e.g report a result to EU about report , -> pobj is a result about report.
                        stop_pobj = None
                        # print("stop_pobj: ", stop_pobj.text, str(stop_pobj), str(stop_pobj.i), subtree[-1].i+1)
                        for x in subtree:
                            if x.dep_ == "prep" and (x.text == "on" or x.text == "about"):
                                stop_pobj = x
                                break
                        
                        # if no stop_pobj
                        if stop_pobj is None:
                            self.pobj = self.tree[pobj.i : subtree[-1].i+1].text
                        else: # if sentence have stop_pobj
                            self.pobj = self.tree[pobj.i : stop_pobj.i].text
                            self.dobj = self.dobj + ' ' + self.tree[stop_pobj.i: subtree[-1].i+1].text

                    except StopIteration:
                        self.dobj, self.dobj_idx = self.subtree_str(child)
                        # print('StopIteration')
                elif self.passive and child.dep_ == "agent":
                    self.subj, self.subj_idx = self.subtree_str(child)
                elif child.dep_ == "pobj" or (child.dep_ == "prep" and child.text == "to"):
                    self.pobj, self.pobj_idx = self.subtree_str(child) # maybe has a problem with subtree_str
                elif child.dep_ == "prep" and (child.text == "on" or child.text == "about"):
                    self.dobj, self.dobj_idx = self.subtree_str(child)
                elif child.dep_ == "advcl":
                    for c in child.rights:
                        if c.dep_ == "pobj" or (c.dep_ == "prep" and c.text == "to"):
                            self.pobj, self.pobj_idx = self.subtree_str(c)
    
        return None

    
    def find_date(self):
        # It detects date element ex: no later than <Date>, <Date>. Currently it could not detects "before <Date>" maybe LLM could solve this problem
        # For example:
        # No later than 10 Octorber 2020-> output: date (10 September 2010), annotated (No later than)
        # Before 10 September 2010 -> output: date (10 September 2010), annotated (10 September 2010). The acutal output should be date (10 September 2010), annotated (Before)
        
        date_model = spacy.load('en_core_web_sm')
        config = {
            "kb_id_type": "timex3",  # possible values: 'timex3'(default), 'timestamp'
            "label": "timexy",       # default: 'timexy'
            "overwrite": False       # default: False
        }
        date_model.add_pipe("timexy", config=config, before="ner")
        
        doc = date_model(self.text)
      
        for e in doc.ents:
            
            # it detects element such as no later than <Date>
            if e.label_ == 'DATE':
                self.date_annotated = e.text
                
            # it detects date's element ex:10 september 2000, 5/09/2011
            elif e.label_ == 'timexy':
                self.date = e.text
        
        # if the input sentence doesn't have date_annotated (ex: no later than ....) and has date, we assume date_annotated is date (use in Ontology)
        if self.date_annotated is None and self.date is not None:
            self.date_annotated = self.date
            
        for e in doc.ents:
            print(f"{e.text}\t{e.label_}\t{e.kb_id_}")   
        
            

    def find_date_old(self):
        """ 
        Function to find the dates within the text

        Note: Hummm could be improved I guess
        """
        for ent in self.tree.ents:
            if ent.label_ == "DATE" and re.match(Text.DATE_REGEX, ent.text):
                self.date = ent.text
                break

    def subtree_str(self, node: spacy.tokens.token.Token) -> str:
        """
        Returns a string representation of the entire subtree of a given node, including the node itself.
        Args:
            node (Token): The node whose subtree is to be represented.
        Returns:
            str: The string representation of the node's subtree.
        """
        subtree = list(node.subtree)
        list_indices = np.arange(subtree[0].i,subtree[-1].i+1)
        return self.tree[subtree[0].i : subtree[-1].i+1].text, list_indices

    @property
    def modal(self):
        """
        Retrieves the modal verb from the sentence as a string, if present.
        """
        if self.modal_idx is None:
            return ''
        return self.tree[self.modal_idx].text

    @property
    def verb(self):
        """
        Retrieves the main verb from the sentence as a string, if present.
        """
        if self.verb_idx is None:
            return ''
        return [self.tree[self.verb_idx].text] # case to array for evaluation

    @property
    def summary(self):
        '''
        Returns a summary of the sentence in the format
        [SUBJECT] [MODAL] [VERB] [DOBJ] to [POBJ] by [DATE]
        '''
        return f"(subj) {self.subj} (verb) {self.modal}{' be' if self.passive else ''} {self.verb} (dobj) {self.dobj} (pobj) {self.pobj} (date) by {self.date}"
    
    def post_processing(self) -> None:
        # split addressee into list if there are many addressees
        if self.pobj is not None:
            pobj_tmp = spacy_model(self.pobj)
            for i in pobj_tmp:
                # print(i.text, ':', i.pos_)
                if i.pos_ == "NOUN" or i.pos_ == "PROPN":
                    # replace space with _ , because we will use them as url in ontology.
                    # self.pobj_list.append(i.text.replace(' ', '_').lower())
                    self.pobj_list.append(i.text.lower())
        
        # Perform the same operation for addressers
        if self.subj is not None:
            subj_tmp = spacy_model(self.subj)
            for i in subj_tmp:
                # print(i.text, ':', i.pos_)
                if i.pos_ == "NOUN" or i.pos_ == "PROPN":
                    # replace space with _ , because we will use them as url in ontology.
                    # self.subj_list.append(i.text.replace(' ', '_').lower())
                    self.subj_list.append(i.text.lower())
        
        return None

    def date_postprocessing(self) -> str:
        """
        This function extract only date from this string 'no later than 09-10-2010' -> 09-10-2010
        """
        # Regular expression pattern to match dates
        date_pattern = re.compile(r"\b\d{1,2}-\d{1,2}-\d{4}\b")
        # Find the date in the string using the regular expression
        match = date_pattern.search(self.date)
        return match.group() if match else self.date
    
    def post_processing_llm(self):
        self.subj_list = [item.replace(' ', '_') for item in self.subj_list]
        self.pobj_list = [item.replace(' ', '_') for item in self.pobj_list]
        