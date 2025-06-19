
from enum import Enum

import spacy

spacy_model = spacy.load('en_core_web_sm')
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


class SentenceClassifier():
    """
    This class analyses the sentences and classifies them on whether they are reporting requirements
    """
    def __init__(self, sentence: str):
        self.sentence = sentence
        self.tree = spacy_model(sentence)
        self.verb_idx = None
        self.modal_idx = None
        # Finds the root of the sentence (main verb)
        self.root = self.find_root_verb()
        self.requirement = self.contains_reporting_requirement(self.root)

    def find_root_verb(self):
        root = self.tree[0]
        while root != root.head:
            root = root.head
        return root

    def contains_reporting_requirement(self, root: spacy.tokens.token.Token) -> bool:
        """ 
        Function that recursively checks the tree

        Args:
        -----
        - `root`:

        Returns:
        --------
        True if found a reporting verb + modal
        """
        # Analyse the root of the verb
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
                res = self.contains_reporting_requirement(child)

                # return True as soon as a recursive call is successful
                if res:
                    return res
                
        return False