import pathlib
import typing
import requests
import json
import bs4
import re

def scrape_functions() -> typing.Dict:
    # First, see if we can serve our keywords without scraping...
    functions_file = pathlib.Path(__file__).parent / 'install/sqlpp-functions.json'
    if functions_file.exists():
        with functions_file.open('r') as fp:
            return json.load(fp)

    # ...otherwise, we need to scrape.
    _URL = 'https://nightlies.apache.org/asterixdb/sqlpp/builtins.html'
    page = requests.get(_URL)
    soup = bs4.BeautifulSoup(page.content, 'html.parser')

    functions_dict = dict()
    for func_element in soup.findAll('h3'):
        # noinspection PyBroadException
        try:
            function_names = func_element.text
            function_next = func_element.findNextSibling()
            function_class = func_element.parent.parent.next_element.next_element.findNext('a')['name']
            function_text = re.sub(r'\n\n+', '\n\n', function_next.text).strip()
            function_description = re.sub(
                r'\s+',
                ' ',
                function_next.findAll('li')[1].text.replace('Return Value:', '')
            ).strip()

            for function_name in function_names.split('/'):
                functions_dict[function_name] = {
                    'functionName': function_name,
                    'functionClass': function_class,
                    'functionText': function_text,
                    'functionDescription': function_description
                }
                print(f'{function_name} [{function_class}]: {function_description}')

        except Exception:
            pass

    # Save our results.
    with functions_file.open(mode='w') as fp:
        json.dump(functions_dict, fp)
    return functions_dict

def scrape_keywords() -> typing.List[str]:
    # First, see if we can serve our keywords without scraping...
    keywords_file = pathlib.Path(__file__).parent / 'install/gsqlpp-tokens.json'
    if keywords_file.exists():
        with keywords_file.open(mode='r') as fp:
            return json.load(fp)

    # ...otherwise, we need to scrape.
    _URL = 'https://graphix.ics.uci.edu/docs/language-reference/reserved.html'
    page = requests.get(_URL)
    soup = bs4.BeautifulSoup(page.content, 'html.parser')

    keywords_list = list()
    for keyword in soup.findAll('td'):
        if not re.match(r'\w+', keyword.text):
            continue
        keywords_list.append(keyword.text.strip())

    # Save our results.
    with keywords_file.open(mode='w') as fp:
        json.dump(keywords_list, fp)
    return keywords_list
