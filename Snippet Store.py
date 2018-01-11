#!/usr/bin/env python

"""Snippet Store

Add text snippets as md file in folder, search them, and copy to clipboard."""

from albertv0 import *
from shutil import which
import glob
import re
import os
import pyperclip
import subprocess
from send2trash import send2trash

__iid__ = 'PythonInterface/v0.1'
__prettyname__ = 'Snippet Store'
__version__ = '0.1'
__trigger__ = 'sn '
__author__ = 'dynobo'
__bin__ = 'sh'
__dependencies__ = [__bin__, 'send2trash', 'pyperclip']

PATH = '/home/holger/cumulus/Notes/snippets'

if which(__bin__) is None:
    raise Exception('" %s" is not in $PATH.' % __bin__)

iconPath = iconLookup('gedit')


class snippets():

    def __init__(self, *args, **kwargs):
        self.path = args[0]
        self.snippets_store = []
        self.update_store()

    def score(self, query, text):
        score = 0
        score += len(re.findall('\b{}\b'.format(query), text.lower()))
        score += len(re.findall('\b{}'.format(query), text.lower()))
        score += text.lower().count(query)
        return score

    def search(self, query):
        results = []
        for snippet in self.snippets_store:
            temp_snippet = snippet
            temp_snippet['score'] = self.score(query, snippet['title']) * 2
            temp_snippet['score'] += self.score(query, snippet['subtitle']) * 1.5
            temp_snippet['score'] += self.score(query, snippet['text'])
            temp_snippet['score'] += self.score(query, snippet['file']) * 0.5
            if temp_snippet['score'] > 0:
                results.append(temp_snippet)
        results = sorted(results, key=lambda k: k['score'], reverse=True)
        # print(results)
        return results

    def update_store(self):
        info('{} - Updating Index'.format(__prettyname__))
        temp_store = []
        # Find markdown files
        files = []
        for filename in glob.iglob(self.path + '**/*.md', recursive=True):
            files.append(filename)

        # Read markdown files
        for snippet_file in files:
            with open(snippet_file, 'r') as f:
                content = f.readlines()
                filepath = snippet_file.strip()
                title = content[0][1:].strip()
                if content[1][0] == '>':  # has subtitle
                    subtitle = content[1][1:].strip()
                    text = os.linesep.join(content[2:]).strip()
                else:
                    subtitle = content[1].strip()
                    text = os.linesep.join(content[1:]).strip()

                temp_store.append({
                    'file': filepath,
                    'title': title,
                    'subtitle': subtitle,
                    'text': text,
                })
        self.snippets_store = temp_store


snippets = snippets(PATH)


def handleQuery(query):
    results = []
    if query.isTriggered:
        try:
            if query.string.strip():
                for snippet in snippets.search(query.string.lower()):
                    results.append(
                        Item(id='%s%s' % (__prettyname__, snippet),
                             icon=iconPath,
                             text=str(snippet['score']) +
                             ' - ' + snippet['title'],
                             subtext=snippet['subtitle'][:80],
                             completion=query.rawString,
                             actions=[
                                 FuncAction('Copy to Clipboard',
                                            lambda snippet=snippet: pyperclip.copy(snippet['text'])),
                                 FuncAction('Open in Editor',
                                            lambda snippet=snippet: subprocess.Popen(['xdg-open', snippet['file']])),
                                 FuncAction('Move to Recycle Bin',
                                            lambda snippet=snippet: send2trash(snippet['file']))
                        ]))
            else:
                def openPath():
                    subprocess.Popen(['xdg-open', PATH])
                results.append(
                    Item(id='%s-create' % __prettyname__,
                         icon=iconPath,
                         text=__prettyname__,
                         subtext='Open Folder containing Snippets',
                         completion=query.rawString,
                         actions=[
                             FuncAction(
                                 'Create a new snippet', openPath), FuncAction(
                                 'Update Index', snippets.update_store)
                         ]
                         )
                )
        except Exception as e:
            critical(str(e))
    return results
