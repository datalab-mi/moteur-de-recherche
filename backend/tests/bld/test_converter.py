import sys, json
from pathlib import Path
sys.path.append('./tools')

from converter import odt2json, odt2html

def test_odt2json(sections):
    directory = '/app/tests/bld/data/test.odt'

    name = 'doc name'
    Titre = 'doc titre'
    Date = 'doc date'
    Auteurs = 'doc auteur 1'
    data = odt2json(directory, sections)
    #import pdb; pdb.set_trace()

    assert data == {'site': 'monsite.org',
                    'direction': 'Ma direction',
                    'titre': 'Mon Titre',
                    'domaine': 'Mon domaine',
                    'mots cles': ['Test', 'Essai'],
                    'date': '01/02/2018',
                    'question': 'Question teste ?',
                    'reponse': 'Réponse test. On peut vérifier que les retours à la ligne sont transformés correctement. Ceux la aussi.',
                    'pieces jointes': ['test.pdf'],
                    'liens': 'https://github.com/victorjourne/browser'}, data


def test_odt2html():
    path = '/app/tests/bld/data/test.odt'
    result = odt2html(path)
    with Path(path).with_suffix('.html').open() as f:
        #import pdb; pdb.set_trace()
        assert result == f.readline().replace('\n','')

if __name__ == '__main__':
    test_odt2json()
