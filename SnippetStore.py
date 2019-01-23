#!/usr/bin/env python

"""SnippetStore

Add text snippets as md file in folder, search them, and copy to clipboard."""

from albertv0 import *
import glob
import re
import os
from send2trash import send2trash
from subprocess import call

__iid__ = 'PythonInterface/v0.1'
__prettyname__ = 'SnippetStore'
__version__ = '0.1'
__trigger__ = 'sn '
__author__ = 'dynobo'
__bin__ = 'sh'
__dependencies__ = ['send2trash','xdotool']

SNIPPET_PATH = '/home/holger/cirrus/notes'
RECURSIVE = True
SNIPPET_EXT = 'md'
iconPath = iconLookup('gedit')


class snippets():

    def __init__(self, *args, **kwargs):
        self.path = args[0].rstrip('/')
        self.snippets_store = []

    def score(self, query, text):
        score = 0
        score += len(re.findall('\b{}\b'.format(query), text.lower()))
        score += len(re.findall('\b{}'.format(query), text.lower()))
        score += text.lower().count(query)
        return score

    def search(self, query):
        results = []
        # Calculate scores
        for snippet in self.snippets_store:
            temp = snippet.copy()
            temp['score'] = self.score(query, snippet['title']) * 2
            temp['score'] += self.score(query, snippet['subtitle']) * 1.5
            temp['score'] += self.score(query, snippet['text'])
            temp['score'] += self.score(query, snippet['file']) * 0.5
            if temp['score'] > 0:
                results.append(temp)
        # Sort by scores
        results = sorted(results, key=lambda k: k['score'], reverse=True)
        return results

    def update_store(self):
        # Clear snippets
        self.snippets_store = []

        # Find markdown files
        files = []
        for filename in glob.iglob(self.path + '**/*.{}'.format(SNIPPET_EXT), recursive=RECURSIVE):
            files.append(filename)

        # Read markdown files
        for snippet_file in files:
            with open(snippet_file, 'r') as f:
                # Parse snippet
                content = f.readlines()
                filepath = snippet_file.strip()
                title = content[0].strip('>').strip()
                if content[1][0] == '>':  # has subtitle
                    subtitle = content[1][1:].strip()
                    text = os.linesep.join(content[2:]).strip()
                else:
                    subtitle = content[1].strip()
                    text = os.linesep.join(content[1:]).strip()

                # Append to snippet store
                self.snippets_store.append({
                    'file': filepath,
                    'title': title,
                    'subtitle': subtitle,
                    'text': text,
                })

        info('[{}] Indexed {} snippet files.'.format(__prettyname__, len(self.snippets_store)))

snippets = snippets(SNIPPET_PATH)


def paste_directly(text):
    text = text.replace('\n\n','\r')
    os.system('sleep 0.02 && xdotool type "'+ text + '" &')
    return


def initialize():
    try:
        snippets.update_store()
    except Exception as e:
        critical(str(e))


def handleQuery(query):
    results = []
    if query.isTriggered:
        try:
            if query.string.strip():
                def copyToClipboard(text):
                    p = subprocess.Popen(
                        ['xclip', '-selection', 'c'], stdin=subprocess.PIPE)
                    p.communicate(input=bytes(text, 'utf-8'))

                for snippet in snippets.search(query.string.lower()):
                    results.append(
                        Item(id='%s%s' % (__prettyname__, snippet),
                             icon=iconPath,
                             #text=str(snippet['score']) + ' - ' + snippet['title'],
                             text=snippet['title'],
                             subtext=snippet['subtitle'][:120],
                             completion=query.rawString,
                             actions=[
                                 FuncAction('Paste directly',
                                            lambda snippet=snippet: paste_directly(snippet['text'])),
                                 ClipAction(text='Copy to Clipboard',
                                            clipboardText=snippet['text']),
                                 UrlAction(
                                     'Open in Editor', 'file://{}'.format(snippet['file'])),
                                 FuncAction('Move to Recycle Bin',
                                            lambda snippet=snippet: send2trash(snippet['file']))
                        ]))
            else:
                results.append(Item(id='%s-create' % __prettyname__,
                                    icon=iconPath,
                                    text=__prettyname__,
                                    subtext='Open Folder containing Snippets',
                                    completion=query.rawString,
                                    actions=[
                                        UrlAction(
                                            'Open', 'file://{}'.format(SNIPPET_PATH)),
                                        FuncAction(
                                            'Update Index', snippets.update_store)
                                    ]
                                    )
                               )
        except Exception as e:
            critical(str(e))
    return results
