# ABOUT THIS SCRIPT
# - This script translates a JSON object into multiple languages and saves the translations in their respective locale files.
# - It uses the Azure Chat OpenAI component from the Langchain library for generating translations.
# - The script substitutes the values in the JSON object with translations for each respective language.
# - You have the option to auto sorting the locale files alphabetically in the parameter `auto_sort`.
#
# **Pro Tip**: You don't need to input the entire object of existing text if it was too long.
# Just provide the text you wish to translate, and the script will locate the correct key in the JSON object and update the value with the translation.
# It won't delete any existing keys, even nested ones.

# SETUP
# -You must have Python installed on your machine.
# -install the dependencies below in your terminal
# ```bash
#   pip install python-dotenv langchain-openai langchain-core
# ```
# include AZURE_OPENAI_KEY in the .env file. You may request from from KDC Gateway team.

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
LOCALES = ["en", "es", "it", "de", "fr"]


llm = AzureChatOpenAI(
    azure_endpoint="https://kdcaigateway.intranet.cloudreference.basf.com/",
    azure_deployment="gpt-4o-mini",
    openai_api_version="2024-02-15-preview",
    api_key=os.getenv("AZURE_OPENAI_KEY"),
)


def deep_merge_dicts(original, updates):
    """
    Recursively merge two dictionaries. Child attributes in the original dictionary
    are preserved unless explicitly overridden by the updates dictionary.
    """
    for key, value in updates.items():
        if (
            isinstance(value, dict)
            and key in original
            and isinstance(original[key], dict)
        ):
            # If both original and updates have a dictionary for this key, merge them
            deep_merge_dicts(original[key], value)
        else:
            # Otherwise, override the original value with the new one
            original[key] = value


def deep_sort_dict(d):
    """
    Recursively sort a dictionary by its keys.
    """
    return {
        key: deep_sort_dict(value) if isinstance(value, dict) else value
        for key, value in sorted(d.items())
    }


def update_locales(translations: dict, locale_dir: str, auto_sort=True):
    for lang_code, translation in translations.items():
        file_path = os.path.join(locale_dir, f"{lang_code}.json")

        # Load existing content
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = {}

        # Deep merge with new translations
        deep_merge_dicts(data, translation)

        # Sort the data alphabetically
        if auto_sort:
            sorted_data = deep_sort_dict(data)
        else:
            sorted_data = data

        # Write the updated and sorted data back to the JSON file
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(sorted_data, file, ensure_ascii=False, indent=4)

        print(f"Updated {lang_code}.json")


# using prompt template
promptTemplate = ChatPromptTemplate.from_template(
    """
    You are an expert in multiple languages. Your task is to translate user-provided text except for the keys in a JSON object.

    Instructions:
    - Translate only the values, not the keys.
    - Retain keys even if they are acronyms or not real words.
    - Translate all Languages:- {locales} except for 'english' or 'en'

    JSON to Translate: {toTranslate}

    Example Format for Response

    ```json
    {{
      "en": {toTranslate},
      "de": {{}},
      "it": {{}}
    }}
    ```
    """
)


# Chain the components together
chain = promptTemplate | llm | SimpleJsonOutputParser()

# IMPORTANT: JSON object to translate
originalText: dict = {
    "modals": {
        "shareProjectAccess": {
            "title": "Share access of project to user",
        }
    }
}

# Invoke the chain with the locales and JSON object to translate
chainResult = chain.invoke({"locales": LOCALES, "toTranslate": originalText})

# preview the result
pprint.pprint(chainResult)

if chainResult:
    update_locales(chainResult, LOCALES_DIRECTORY, auto_sort=False)
