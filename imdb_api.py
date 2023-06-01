import threading
import time
import sys
from itertools import zip_longest
import itertools
import typer
from typing_extensions import Annotated
from typing import Optional
from rich import *
from rich.console import Console
from rich.tree import Tree
from rich.live import Live
from rich.table import Table
from imdb import Cinemagoer
import matplotlib.pyplot as plt
import json
from tinydb import TinyDB, Query

# création appli avec typer
imdb = typer.Typer(name='IMDB', add_completion=False, help='Recherche IMDB')
ia = Cinemagoer()
lst_persons = []
lst_movies = []
dico = {}
dico_th = {}

def create_tree_persons(dico): 
    console = Console(record=True, width=100)
   
    console.print("")
    console.print("") # création de l'arbre
    tree = Tree("Collaborations", guide_style="bold bright_black")
    
    for p, movies in dico.items(): # à chaque combinaison de personnes sa branche
        movies_tree = tree.add(f'[green]{p}', guide_style="bright_black")
        # pour chaque film, création d'une sous-branche
        for movie in movies:
            movies_tree.add( f"[orange1]{movie['title']} - [bold link={create_link_movie(movie.movieID)}][dodger_blue1]Movie Link[/]")
    # liste des acteurs recherchés et de leur lien IMDB
    persons_tree = tree.add('[white]Liste des acteurs')
    for p in lst_persons:
        persons_tree.add(f"[chartreuse4]{p['name']}[/] - [bold link={create_link_person(p.personID)}][dodger_blue1]Person Link[/]")

    console.print(tree)
    console.print("")

def create_tree_cast(dico, func):
    console = Console(record=True, width=100)

    console.print("")
    console.print("")
    tree = Tree("Castings", guide_style="bold bright_black")
    for m, cast in dico.items(): 
        casting_tree = tree.add(f'[green]{m}', guide_style="bright_black")
        for i in cast: # chaque personne et son rôle dans une nouvelle branche
            casting_tree.add( f"[yellow4]{i['name']} [orange1]{func(i)}[/] -  [bold link={create_link_person(i.personID)}][dodger_blue1]Person Link[/]")  

    console.print(tree)
    console.print("")  

def generate_table() -> Table:
    # table d'affichage des recherches
    table = Table()
    table.add_column('Personne')
    table.add_column('Recherche')

    for th, p in dico_th.items():
        nom = p
        # si c'est un objet Person, on récupère le nom
        if not isinstance(nom, str):
            nom = p['title']
        table.add_row(nom, "[red]En cours" if th.is_alive() else "[green]Terminée")
    return table

def live_table():
    # gestion de l'affichage des table de recherche
    with Live(generate_table()) as live:
        for _ in range(1000): # compteur empêchant l'update de cesser
            live.update(generate_table())
            time.sleep(0.5)
            while threading.active_count() == 5:
                time.sleep(0.5)
            if threading.active_count() == 2:
                # quand les threads sont terminés
                # (seuls le main et la boucle sont actifs)
                live.update(generate_table())
                time.sleep(0.5)
                break

def run_in_thread(f):
    # thread decorator    
    def run(*args, **kwargs):
        thread = threading.Thread(target=f, args=args, kwargs=kwargs)     
        thread.start()
        # ajout dans un dico pour connaitre le status
        # et l'associer à une recherche
        dico_th[thread] = args[0]
        return thread
    return run

@imdb.command()
def search_actors(name: Annotated[list[str], typer.Argument(..., help="Nom d'un acteur")]):
    """Recherche les correspondances entre plusieurs personne\n
    ex : python imdb_api.py search-actors keanu reeves laurence fishburne
    """
    global lst_persons
    # pas de doublons avec le set
    set_noms = set()
    # permet la saisie directe des noms
    noms = [iter(name)] * 2
    zip_noms = zip_longest(*noms, fillvalue='')
    # création prenom:nom
    [set_noms.add(f'{i[0]} {i[1]}') for i in zip_noms]
    lst_persons = list(set_noms)
    # recherches
    search_lst_persons()
    find_shared_movies_actors()

@run_in_thread
def search_person(pers):
    # fonction de recherche pour chaque personne
    try:
        persons = ia.search_person(pers)
        person = ia.get_person(persons[0].personID)
        # on utilise la même liste en remplaçant les str
        # par les objets Person
        lst_persons.remove(pers) 
        lst_persons.insert(0, person)
    except:
        print(f'search_person, {pers} not found.')

def search_lst_persons():
    # recherche de la liste de personnes via api
    for p in lst_persons:
        search_person(p)    
    live_table()
    # vérification de la recherche
    [lst_persons.pop(i) for i in lst_persons if i is None]
    if isinstance(lst_persons[0], str) or isinstance(lst_persons[0], int):
        print('Nobody found.')
        sys.exit()

def create_link_movie(id):
    return f'http://www.imdb.com/title/tt{id}'

def create_link_person(id):
    return f'http://www.imdb.com/name/nm{id}'

def find_shared_movies_actors():
    # on cherche les films en communs de différents acteurs
    resultats = {}
    resultats_dir = {}

    for x in range(2, len(lst_persons)+1):
        # création des combinaisons possibles de noms
        for p in itertools.combinations(lst_persons, x):
            lst_movies = set(get_filmo(p[0]))
            noms = p[0].get('name')
            # comparaison des sets de filmos
            for pers in p[1:]:               
                lst_movies &= set(get_filmo(pers))
                noms += f" - {pers.get('name')}"
            resultats[noms] = lst_movies
            resultats_dir.update(find_shared_movies_directors(p))
           
    create_tree_persons(resultats)
    create_tree_persons(resultats_dir)

def find_shared_movies_directors(persons):
    # on cherche les films en communs de différents acteurs
    resultats = {}
    
    lst_movies = set(get_filmo(persons[0], True))
    noms = f"{persons[0].get('name')} (réalisateur)"
    # comparaison des sets de filmos
    for pers in persons[1:]:       
        lst_movies &= set(get_filmo(pers))
        # concaténation des noms communs
        noms += f" - {pers.get('name')}"
    resultats[noms] = lst_movies

    lst_movies = set(get_filmo(persons[-1], True))
    noms = f"{persons[-1].get('name')} (réalisateur)"
    # comparaison des sets de filmos
    for pers in persons[:-1]:       
        lst_movies &= set(get_filmo(pers))
        # concaténation des noms communs
        noms += f" - {pers.get('name')}"
        resultats[noms] = lst_movies

    return resultats
    
@run_in_thread
def search_movie(film):
    # fonction de recherche pour chaque film
    if isinstance(film, str): # vérifie si str ou obj Movie
        movie = ia.search_movie(film)[0]
    movie = ia.get_movie(film.movieID)
    lst_movies.append(movie)

def search_lst_movies():
    # recherche de la liste de films via api
    lst_temp = []
    [lst_temp.append(i) for i in lst_movies]
    lst_movies.clear()

    for m in lst_temp:
        search_movie(m)

    live_table()
    [lst_movies.remove(i) for i in lst_movies if i is None]

def get_genre_person(person):
    # cherche si c'est un acteur et détermine le genre   
    if 'actress' in person['filmography']:
        return 'actress'
    return 'actor'
       
def get_filmo(person, isdir=False):
    # renvoie la filmo grâce au genre : actor/actress
    try:
        if isinstance(person, str):
            lst_persons.append(person)
            search_lst_persons()
            person = lst_persons[0]
        
        if isdir and 'director' in person.get('filmography'):
            liste = []
            # on retourne uniquement les films d'un réal 
            [liste.append(i) for i in person.get('director') if i.get('kind') == 'movie']
            return liste
        
        genre = get_genre_person(person)
        return  person.get(genre)
    except:
        return []
 
@imdb.command()
def filmo_actor(name: str = typer.Option(..., prompt='Acteur ', help="Un seul acteur à entrer")):
    """Retourne la filmographie d'un acteur"""    
    lst_persons.append(name)
    search_lst_persons()
    dico[lst_persons[0]] = get_filmo(lst_persons[0])
    create_tree_persons(dico)

@imdb.command()
def filmo_dir(name: str = typer.Option(..., '-d', help="Un seul réalisateur à entrer")):
    """Retourne la filmographie d'un réalisateur"""    
    lst_persons.append(name)
    search_lst_persons()
    dico[lst_persons[0]] = get_filmo(lst_persons[0], True)
    create_tree_persons(dico)

@imdb.command()
def cast(title: str = typer.Option(..., prompt="Film ", help="Un seul titre à entrer")):
    """Retourne le casting d'un seul film.\n
    A utiliser avec le prompt."""
    lst_movies.append(title)
    search_lst_movies()
    movie = lst_movies[0]
    dico[movie] = movie['cast']
    create_tree_cast(dico, lambda i: f'({i.currentRole}) ')

@imdb.command()
def compare_casts(movies: Annotated[list[str], typer.Option(..., '-m', help="Un titre par argument")]):
    """Compare le casting de plusieurs films"""
    [lst_movies.append(m) for m in movies]
    search_lst_movies()
    resultats = {}

    for x in range(2, len(lst_movies)+1):
        # combinaison et comparaison de chaque casting
        for m in itertools.combinations(lst_movies, x):
            liste = set(m[0]['cast'])
            titres = m[0]['title']
            for mov in m[1:]:
                liste &= set(mov['cast'])
                # on ajoute les titres combinés
                titres += f" - {mov['title']}"
            resultats[titres] = liste

    create_tree_cast(resultats, lambda i: '')

@imdb.command()
def get_mean_rate(actor: str = typer.Option(..., '-n', help="Nom d'un acteur")):
    # faire in callback puor remplir les listes
    global lst_movies
    lst_movies = get_filmo(actor)
    search_lst_movies()

    notes = []
    for i in lst_movies:
        try:
            notes.append(float(i.get('rating')))
        except Exception as e:
            print(e)
    c = 0
    for i in notes:
        c += i
    print(c/len(notes))

def insert_base():
    global lst_movies
    lst_movies = get_filmo('isaa rae')
    search_lst_movies()
    for i in lst_movies:
        print(i['rating'])
    with open('test.json', 'a') as a:
        for i in lst_movies:
            a.write(json.dumps(i.__dict__))

    db = TinyDB(r'C:\Python\Projets\git_imdb\movies.json')
    for i in lst_movies:
        db.insert(i)

@imdb.command()
def plot(name: str = typer.Option(..., '-n', help='Nom personne'), isdir: Annotated[bool, typer.Argument()] = False,
          n: Annotated[Optional[int], typer.Argument()] = None):
    """Affiche un graphique des notes des n derniers films d'une personne"""
    global lst_movies
    dico = {}
    temp_lst = []
    # récupère les n derniers films d'une personne
    lst_movies = get_filmo(name, isdir)[:n]
    search_lst_movies()
    # tri des films sans date ou note
    for i in lst_movies:
        if i.get('year') is not None and i.get('rating') is not None:
            temp_lst.append(i)

    temp_lst.sort(key=lambda i: i.get('year'))
    # association date et note pour le plot
    year, rating = [], []
    for i in temp_lst:
        year.append(i.get('year'))
        rating.append(i.get('rating'))

    plt.scatter([i.get('year') for i in temp_lst], [i.get('rating') for i in temp_lst])
    plt.plot([i.get('year') for i in temp_lst], [i.get('rating') for i in temp_lst], label=ia.search_person(name)[0].get('name'))
    plt.legend()
    plt.show()


if __name__ == '__main__':
    # appel de l'app avec typer
    imdb()
