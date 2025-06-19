
import pandas as pd
import spacy
from sortis.text import Text
import rdflib
from rdflib.namespace import Namespace
from sortis.classifier import SentenceClassifier

from sortis.mapping import extract_agents, add_agent, add_request, add_action, add_action_result, add_addressee, add_addresser, add_date 
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import os

from transformers import set_seed

# Set the seed for reproducibility
set_seed(42)

model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
)
    
def prompting(sentence: str, output_log_filename, error_log_filename):
    #1st approach to few shot promting , whereby system (instruction), user (user input) and llm response are combined

    messages = [
    {"role": "system", "content": """You are a virtual annotation. For each sentence, you annotate the addresser, addressee, actionResult, date. 
    The output should be in Json format.
    Adresser: Who performs the action.
    Action: What action is performed.
    ActionResult: What is done.
    Addressee: To whom the action is directed.
    Date: When the action occurs/deadline."""},
    
    {"role": "user", "content": """By 31 December 2010 and, thereafter, at least every three years, the Commission shall review the provisions concerning its implementing powers and present a report to the European Parliament and to the Council on the functioning of those powers. The report shall examine, in particular, the need for the Commission to propose amendments to this Directive in order to ensure the appropriate scope of the implementing powers conferred on the Commission. The conclusion as to whether or not an amendment is necessary shall be accompanied by a detailed statement of reasons. If necessary, the report shall be accompanied by a legislative proposal to amend the provisions conferring implementing powers on the Commission."""},
    {"role": "system", "content": """{
    "addresser": ["the commission"],
    "Action": ["present"],
    "ActionResult": ["a report on the functioning of those powers"],
    "addressee": ["the european parliament", "the council"],
    "Date": ["By 31 December 2010"]
    }"""},
    
     {"role": "user", "content": """Member States shall communicate to the Commission the texts of the main provisions of national law which they adopt in the field governed by this Directive."""},
    {"role": "system", "content": """{
    "addresser": ["member states"],
    "Action": ["communicate"],
    "ActionResult": ["the texts of the main provisions of national law"],
    "addressee": ["the Commission"],
    "Date": ["None"]
    }"""},
    
     {"role": "user", "content": """Upon reasoned request, Member States shall forthwith communicate the reports referred to in Article 111(3) to the competent authorities of another Member State."""},
    {"role": "system", "content": """{
    "addresser": ["Member States"],
    "Action": ["communicate"],
    "ActionResult": ["the reports referred to in Article 111(3)"],
    "addressee": ["the competent authorities of another Member State"],
    "Date": ["forthwith"]
    }"""},
    
    {"role": "user", "content": """Each year the sponsor shall submit to the Agency a report on the state of development of the designated medicinal product."""},
    {"role": "system", "content": """{
    "addresser": ["the sponsor"],
    "Action": ["submit"],
    "ActionResult": ["a report on the state of development of the designated medicinal product"],
    "addressee": ["the Agency"],
    "Date": ["Each year"]
    }"""},
    
    {"role": "user", "content": sentence},
]
    # inputs = tokenizer(llama_prompt_tempate, return_tensors="pt").input_ids.cuda()
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)
    # print("size of input: ", inputs[0].shape)
    # print('***Decode Input:\n', tokenizer.decode(inputs[0]))
    terminators = [
        tokenizer.eos_token_id,
        tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]
    
    model.eval()
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=512,
            eos_token_id=terminators,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False,
            temperature=0
            # do_sample=True,
            # temperature=0.6,
            # top_p=0.9,
        )
   
        response = outputs[0][inputs.shape[-1]:]
        response_str = tokenizer.decode(response, skip_special_tokens=True)
        
        return parseJson(response_str, sentence, output_log_filename, error_log_filename)

def parseJson(llm_response, sentence, output_filename, error_filename):
    
    
    try:
        parsed_json = json.loads(llm_response.strip().lower())
        saveToExcelFile(sentence, llm_response, output_filename)
        
    except json.JSONDecodeError as e:      
        
        saveToExcelFile(sentence, llm_response, error_filename)

        return None



def saveToFile(log, filename, mode = "w+"):

    with open(dir_home + "data/llm_output/" + filename + ".txt", mode) as f:
        f.write(log)
        f.close()
    
def saveToExcelFile(sentences, responses, save_dir, writing_mode = "w+"):
    df = pd.DataFrame({'Sentence': [sentences], 'Ouput': [responses]})
        # Check if the file exists
    filename = dir_home + "data/llm_output/" + save_dir + ".xlsx"
    if not os.path.exists(filename):
        print('file not existing')
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False)
    else:
        print('file exist')
        # Append to the existing file
        with pd.ExcelWriter(filename, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False, header=False, startrow=writer.sheets['Sheet1'].max_row if 'Sheet1' in writer.sheets else 0)
    

dir_home = '/gpfs/home/acad/ulg-quantom/pchuor/dev/sortis/'

def main():

    df = pd.read_excel(dir_home + "/data/manually_selection.xlsx", sheet_name = "Sheet1")
   
    
    output_log_filename = "llm_output_chattemplate_temperature_0_evaluation"
    error_log_filename = "error_prompt_chattemplate_temperature_0_evaluation"
   
   
    # Iterate over the dataframe
    for _, paragraph in df.iterrows():
        requirement = prompting(paragraph['Sentence'], output_log_filename, error_log_filename)
    print("### Finish ###")



if __name__ == '__main__':
    
    main()
