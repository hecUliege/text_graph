# Licensed under the EUPL, Version 1.2 or -- as soon they will be approved by the European Commission -- subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#  
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12/
#  
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the Licence for the specific language governing permissions and limitations under the Licence.


import spacy
import numpy as np

from rdflib.namespace import RDF, OWL, DCTERMS, XSD, Namespace, SKOS, URIRef, RDFS
import rdflib

RRMV = Namespace("http://www.semanticweb.org/monica.palmirani/ontologies/2024/rrmv/", )
CCCEV = Namespace("https://semiceu.github.io/CCCEV#")
ELI = Namespace("http://data.europa.eu/eli/ontology#")

def instantiating_roles(g):    
    g.add((RRMV.bearer, RRMV.subClassOf, RRMV.RoleType))
    g.add((RRMV.addresser, RDFS.subClassOf, RRMV.RoleType))
    g.add((RRMV.addressee, RDFS.subClassOf, RRMV.RoleType))        
    g.add((RRMV.Role, RRMV.hasType, RRMV.RoleType))

    return g


def add_action(g, sentence, request_uri, action_uri):        
    # Create the Request Action individual @todo here we are considering cases where there is only one action involved        
    # Populate the Action
    g.add((request_uri, RRMV.produces, action_uri))
    g.add((action_uri, RDF.type, RRMV.Action))
    g.add((action_uri, RRMV.hasAnnotation, rdflib.Literal(sentence.verb)))

    return g

def add_request(g, request_uri, paragraph, eli, eId):

    # Populate the request
    g.add((request_uri, RDF.type, RRMV.Request))
    g.add((request_uri, DCTERMS.isPartOf, rdflib.Literal(eli, datatype=XSD.anyURI)))
    g.add((request_uri, RRMV.hasAnnotation, rdflib.Literal(paragraph)))
    g.add((request_uri, RRMV.hasUri, rdflib.Literal(f'{eli}/{eId}', datatype=XSD.anyURI)))

    return g

def add_action_result(g, sentence, action_result_uri, action_uri): # Create ActionResult individual if dobj is present
    g.add((action_result_uri, RDF.type, RRMV.ActionResult))
    g.add((action_result_uri, RRMV.hasAnnotation, rdflib.Literal(sentence.dobj)))
    g.add((action_uri, RRMV.hasActionResult, action_result_uri))

    return g

def check_agents(agents, list):
    for agent in list:
        if agent.lower() not in agents:
            agents.append(agent)
    return agents

def extract_agents(agents, sentence) -> list:
    agents = check_agents(agents, sentence.subj_list)
    agents = check_agents(agents, sentence.pobj_list)
    return agents

def add_agent(g, agent_uri, agent):
    g.add((agent_uri, RDF.type, ELI.Agent))
    g.add((agent_uri, ELI.hasAnnotation, rdflib.Literal(agent)))

    return g

def look_agent_uri(agent, agent_dict):
    for agent_dict_entry in agent_dict:
        if agent_dict_entry["agent"] == agent:
            return agent_dict_entry['agent_uri']                        

def add_agent_role(g, agent, role_type_uri, role_type, action_uri, agent_dict):
    g.add((role_type_uri, RDF.type, RRMV.AgentRole))
    g.add((action_uri, RRMV.hasAgentRole, role_type_uri))
    if role_type == 'addresser':
        g.add((role_type_uri, RRMV.withRole, RRMV.addresser))
    elif role_type == 'addressee':
        g.add((role_type_uri, RRMV.withRole, RRMV.addressee))
    agent_uri = look_agent_uri(agent, agent_dict)
    g.add((role_type_uri, RRMV.forAgent, agent_uri))

    return g

def add_date(g, sentence, period_uri, action_uri):    
    g.add((period_uri, RDF.type, CCCEV.PeriodOfTime))
    g.add((action_uri, RRMV.atTime, period_uri))
    #g.add((period_uri, RRMV.hasFunction, RRMV.deadline))
    g.add((period_uri, RRMV.hasAnnotation, rdflib.Literal(sentence.date))) # Not all dates are identified
    #g.add((period_uri, CCCEV.endtime, rdflib.Literal(concept.date))) # ENDTIME does not compute

    return g

# Previous functions to be discarded
def highlight2(spacy_model, idx) -> str:
    """
    Function to highlight the words which are indexed in idx
    """

    sentence = [t.text for t in spacy_model]
    
    for id in idx:
        sentence[id] = f'\033[92m{sentence[id]}\033[0m' # Highlights using a color when printed

    text = " ".join(sentence)
    text = text.replace(' .', '.')
    text = text.replace(' ,', ',')
    text = text.replace(' ;', ';')
    text = text.replace(' \xa0 ', '\xa0')
    text = text.replace('( ', '(').replace(' )', ')')

    return text

def detectVerbs(s_model):
    """ 
    Function to find all the verbs
    """

    idx = []
    for i in range(len(s_model)):
        if s_model[i].pos_ == 'VERB':
            v = s_model[i]
            idx.append(v.i)

            for child in s_model[i].children:
                if child.dep_ in ['acomp']:
                    idx.append(child.i)

    return idx

def subtree_str( node: spacy.tokens.token.Token, tree) -> str:
    """
    Returns a string representation of the entire subtree of a given node, including the node itself.
    Args:
        node (Token): The node whose subtree is to be represented.
    Returns:
        str: The string representation of the node's subtree.
    """
    subtree = list(node.subtree)
    list_indices = np.arange(subtree[0].i,subtree[-1].i+1)
    return tree[subtree[0].i : subtree[-1].i+1].text, list_indices


# try to go to the nearest ADP and consider that it is the root of the subtree
ADP_indications = ["january", "february", "march", "april",
                    "may", "june", "july", "august",
                    "september", "october", "november", "december"
                    "monday", "tuesday", "wednesday", "thursday", 
                    "friday", "saturday", "sunday",
                    "period", "year", "month", "day",
                    "annual", "monthly", 'daily', "thereafter", "days", "years", "months"]

# when used, can be found in a noun. The structure of the syntactic tree can greatly vary from there so it is directly selected (might be better to only detect the adjective instead of the associated noun ...)
nouns_check = ['annual', 'monthly']

# when facing such expression, the following subtree is often the time indication
directCheck = ['following', 'within', 'before', 'after', 'during', 'later', 'earlier', 'than']  # at ? + check for not before in this case

# afterwards ?, beforehand

# following might be bad actually
def findTime(sentence, spacy_model):
    """ 
    Function to find the time indications in the sentence 
    (also display it for now, debug purposes)
    """
    indices = []

    # check if there is an interesting word
    for word in sentence.lower().split(' '):

        if word in directCheck:
            # find corresponding scpacy token
            for token in spacy_model:
                if word in token.text.lower():
                    _, timeIndication = subtree_str(token, spacy_model)
                    indices.extend(timeIndication)

        if word in ADP_indications:
            
            # find corresponding scpacy token
            for token in spacy_model:
                if word in token.text.lower() and token.pos_ != 'AUX': # filter word may with AUX, eg: I may ...
                    root = token

                    # goes back to the nearest ADP or ADV

                    while(root.pos_ not in ['ADP', 'ADV']):
                        root = root.head

                        if root.head == root:
                            break

                        if root.pos_ in ['VERB', 'AUX']:
                            break

                    # if found an interesting root, take the subtree
                    if root.pos_ in ['ADP', 'ADV']:
                        _, timeIndication = subtree_str(root, spacy_model)
                        indices.extend(timeIndication)
                    
                    # otherwise, only take the current token (might mean it is a noun)
                    # take the subtree because it might be the root (ie: not before Janurary, here Januray will be the root)
                    else:
                        #_, timeIndication = subtree_str(token, spacy_model)
                        #indices.extend(timeIndication)
                        indices.extend([token.i])

                        # might miss neaby numbers though
                        for child in token.children:
                            if child.dep_ == 'nummod':
                                indices.extend([child.i])

    
    indices = np.unique(indices)


    words = [t.text for t in spacy_model]

    for idx in indices:
        words[idx] = f'\033[91m{words[idx]}\033[0m'

    text = " ".join(words)
    text = text.replace(' .', '.')
    text = text.replace(' ,', ',')
    text = text.replace(' ;', ';')
    text = text.replace(' \xa0 ', '\xa0')
    text = text.replace('( ', '(').replace(' )', ')')

    date = ""
    date = " ".join([spacy_model[date_idx].text for date_idx in indices])
    
    return date


def findOrgs(spacy_model):
    """ 
    Function that checks if the names are organizations
    """
    ents = spacy_model.ents
    indices = []

    for e in ents:
        if e.label_ in[ 'ORG', 'GPE']:
            begin_idx = e.start
            end_idx = e.end
            inds = np.arange(begin_idx, end_idx)

            indices.extend(inds)

    indices = np.unique(indices)

    words = [t.text for t in spacy_model]

    for idx in indices:
        words[idx] = f'\033[92m{words[idx]}\033[0m'

    text = " ".join(words)
    text = text.replace(' .', '.')
    text = text.replace(' ,', ',')
    text = text.replace(' ;', ';')
    text = text.replace(' \xa0 ', '\xa0')
    text = text.replace('( ', '(').replace(' )', ')')

    print(text)
    
    return indices

def findElements(s_mod):
    indices = []

    idx = detectVerbs(s_mod)

    for i in idx:
        v = s_mod[i]

        for child in v.children:

            if child.dep_ in ['dobj', 'pobj']:
                _, inds = subtree_str(child, s_mod)
                indices.extend(inds)

            elif child.dep_ in ['prep']:
                if child.lemma_ in ['to']:
                    _, inds = subtree_str(child, s_mod)
                    indices.extend(inds)

    indices = np.unique(indices)

    words = [t.text for t in s_mod]


    for idx in indices:
        words[idx] = f'\033[93m{words[idx]}\033[0m'

    text = " ".join(words)
    text = text.replace(' .', '.')
    text = text.replace(' ,', ',')
    text = text.replace(' ;', ';')
    text = text.replace(' \xa0 ', '\xa0')
    text = text.replace('( ', '(').replace(' )', ')')
    
    return indices