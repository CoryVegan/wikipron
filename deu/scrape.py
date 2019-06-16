#!/usr/bin/env python

import re
import requests
import requests_html
import string

# Queries for the MediaWiki backend.
# Documentation here: https://www.mediawiki.org/wiki/API:Categorymembers
CATEGORY = "Category:German_terms_with_IPA_pronunciation"
LIMIT = 500
INITIAL_QUERY = f"https://en.wiktionary.org/w/api.php?action=query&format=json&list=categorymembers&cmtitle={CATEGORY}&cmlimit={LIMIT}"
CONTINUE_TEMPLATE = string.Template(INITIAL_QUERY + "&cmcontinue=$cmcontinue")

# Selects the content on the page.
PAGE_TEMPLATE = string.Template("https://en.wiktionary.org/wiki/$word")
LI_SELECTOR = '//li[sup[a[@title = "Appendix:German pronunciation"]] and span[@class = "IPA"]]'
SPAN_SELECTOR = '//span[@class = "IPA"]'
PHONEMES = r"/(.+?)/"


def _yield_phn(request):
    for li in request.html.xpath(LI_SELECTOR):
        for span in li.xpath(SPAN_SELECTOR):
            m = re.search(PHONEMES, span.text)
            if m:
                yield m


def _print_data(data):
    session = requests_html.HTMLSession()
    for member in data["query"]["categorymembers"]:
        word = member["title"]
        # Skips multiword examples.
        if " " in word:
            continue
        query = PAGE_TEMPLATE.substitute(word=word)
        request = session.get(query)
        for m in _yield_phn(request):
            pron = m.group(1)
            print(f"{word}\t{pron}")


def main():
    data = requests.get(INITIAL_QUERY).json()
    _print_data(data)
    code = data["continue"]["cmcontinue"]
    next_query = CONTINUE_TEMPLATE.substitute(cmcontinue=code)
    while True:
        data = requests.get(next_query).json()
        _print_data(data)
        # Then this is the last one.
        if not "continue" in data:
            break
        code = data["continue"]["cmcontinue"]
        next_query = CONTINUE_TEMPLATE.substitute(cmcontinue=code)


if __name__ == "__main__":
    main()
