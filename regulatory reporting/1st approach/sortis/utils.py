# Licensed under the EUPL, Version 1.2 or -- as soon they will be approved by the European Commission -- subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#  
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12/
#  
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the Licence for the specific language governing permissions and limitations under the Licence.

from SPARQLWrapper import SPARQLWrapper, JSON, POST


def create_sparql_query(celex):
    """
    Generate the SPARQL query for retrieving the ELI associated with a given CELEX number.

    Parameters
    ----------
    celex : str
        The CELEX number for which to retrieve the ELI.

    Returns
    -------
    sparql_query : str
        The generated SPARQL query.
    """

    prefixes = """
    PREFIX cdm:<http://publications.europa.eu/ontology/cdm#>
    PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    """

    query_template = """
    SELECT 
    DISTINCT ?workId_ ?eli
    WHERE
    {
        ?work rdf:type ?resType .
        ?work cdm:work_date_document ?date .
        ?work cdm:work_id_document ?workId_.
       ?work cdm:resource_legal_eli ?eli .

        FILTER(str(?workId_) = "celex:""" + celex + """" ) 
    }
    LIMIT 1
    OFFSET 0
    """

    sparql_query = prefixes + query_template
    return sparql_query

def execute_sparql_query(sparql_query, endpoint):
    """
    Execute a given SPARQL query on a specified endpoint and retrieve the results.

    Parameters
    ----------
    sparql_query : str
        The SPARQL query to execute.
    endpoint : str
        The URL of the SPARQL endpoint.

    Returns
    -------
    results : dict
        The JSON representation of the query results.
    """


    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(sparql_query)
    sparql.setMethod(POST)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results


def get_eli(celex):
    """
    Retrieve the ELI (European Legislation Identifier) associated with a given CELEX number.

    Parameters
    ----------
    celex : str
        The CELEX number for which to retrieve the ELI.

    Returns
    -------
    eli : str
        The European Legislation Identifier (ELI) associated with the provided CELEX number.
    """

    # Generate the SPARQL query
    sparql_query = create_sparql_query(celex)

    # Set the SPARQL endpoint URL
    endpoint = "http://publications.europa.eu/webapi/rdf/sparql"

    # Execute the SPARQL query and retrieve the results
    results = execute_sparql_query(sparql_query, endpoint)
    # Extract the ELI from the results and return it
    eli = results['results']['bindings'][0]['eli']['value']

    return eli