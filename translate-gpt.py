# MINI README
# install the dependencies below
# pip install python-dotenv langchain-openai langchain-core
# include AZURE_OPENAI_KEY in the .env file

import json
import os
import pprint
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import SimpleJsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables from the .env file
load_dotenv()

# CONFIGURATION
# Directory where the locale files are located
LOCALES_DIRECTORY = "locales"
LOCALES_TO_TRANSLATE = ["es", "it", "de", "fr"]


llm = AzureChatOpenAI(
    azure_endpoint="https://kdcaigateway.intranet.cloudreference.basf.com/",
    azure_deployment="gpt-4o",
    openai_api_version="2024-02-15-preview",
    api_key=os.getenv("AZURE_OPENAI_KEY"),
)


# Utility function to deep sort a dictionary
def deep_sort_dict(d):
    sorted_dict = {}
    for key in sorted(d.keys()):
        if isinstance(d[key], dict):
            sorted_dict[key] = deep_sort_dict(d[key])
        else:
            sorted_dict[key] = d[key]
    return sorted_dict


# Function to update locale files with translations
def update_locales(translations, locale_dir):
    for lang_code, translation in translations.items():
        file_path = os.path.join(locale_dir, f"{lang_code}.json")

        # Load existing content
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = {}

        # Update with new translations
        data.update(translation)

        # Sort the data alphabetically
        # sorted_data = deep_sort_dict(data)
        sorted_data = data

        # Write the updated and sorted data back to the JSON file
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(sorted_data, file, ensure_ascii=False, indent=4)
        print(f"Update {lang_code}.json")


# IMPORTANT: JSON object to translate
toTranslateJSON = {"eatAgriculture": {"calculated": "Calculated", "closed": "Closed"}}

# using prompt template
prompt_template = ChatPromptTemplate.from_template(
    """
    You are an expert in multiple languages. Your task is to translate user-provided text except for the keys in a JSON object.

    Instructions:
    - Translate only the values, not the keys.
    - Retain keys even if they are acronyms or not real words.
    - Return both the original JSON object and the translated version.

    Translation Target Languages: {locales}

    JSON Object to Translate: {toTranslate}

    Format for Response:

    ```json
    {{
      "original":
      "translations":
    }}
    ```
    """
)


# Chain the components together
chain = prompt_template | llm | SimpleJsonOutputParser()

llm_result = chain.invoke(
    {"locales": LOCALES_TO_TRANSLATE, "toTranslate": toTranslateJSON}
)

# preview the result
pprint.pp(llm_result)

# update the locale files with the translations
if llm_result.get("translations"):
    update_locales(llm_result["translations"], LOCALES_DIRECTORY)
