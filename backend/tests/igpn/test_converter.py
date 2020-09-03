import sys, json

sys.path.append('./tools')

from converter import pdf2json, odt2json

def test_odt2json():
    directory = '/app/tests/igpn/data/test.odt'
    sections = ['SITE','DIRECTION', 'TITRE' , 'DOMAINE' , 'Mots clés' ,
                'Date' , 'Question' , 'Réponse' , 'Pièces jointes' ,
                 'Liens' , 'Références']

    name = 'doc name'
    Titre = 'doc titre'
    Date = 'doc date'
    Auteurs = 'doc auteur 1'
    data = odt2json(directory, sections)
    import pdb; pdb.set_trace()
    assert data == {'site': ['monsite.org'],
                'direction': ['Ma direction'],
                'titre': ['mon titre'],
                'domaine': ['mon domaine'],
                'mots-cles': ['- Test', '- Essai'], 
                'date': ['01/02/2018'],
                'question': ['Question teste ?'],
                'reponse': ['Réponse test.'],
                'pieces-jointes': ['test.pdf'],
                'liens': ['https://github.com/victorjourne/browser']}, data


if __name__ == '__main__':
    test_odt2json()
