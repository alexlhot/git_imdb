import threading
import time, sys
from itertools import zip_longest
import itertools
import typer
import tqdm
from typing_extensions import Annotated
from typing import Optional
from rich import *
from rich.console import Console
from rich.tree import Tree
from rich.live import Live
from rich.table import Table
from imdb import Cinemagoer
import matplotlib.pyplot as plt
import mplcursors
import statistics

# création appli avec typer
imdb = typer.Typer(name='IMDB', add_completion=False, help='Recherche IMDB')

ia = Cinemagoer()
lst_persons = []
lst_movies = []
dico = {}
liste_th = []
nb_threads = 17

#-------------------------- Création tree --------------------------#
def create_tree_persons(dico): 
    console = Console(record=True, width=100)
   
    console.print("")
    console.print("") # création de l'arbre
    tree = Tree("Collaborations", guide_style="bold bright_black")
    
    for p, movies in dico.items(): # à chaque combinaison de personnes sa branche
        movies_tree = tree.add(f'[green]{p}', guide_style="bright_black")
        # pour chaque film, création d'une sous-branche
        for movie in movies:
            movies_tree.add(f"[orange1]{movie.get('title')} [green]({movie.get('year')}) - [bold link={create_link_movie(movie.movieID)}][dodger_blue1]Movie Link[/]")
    # liste des acteurs recherchés et de leur lien IMDB
    persons_tree = tree.add('[white]Liste des acteurs')
    for p in lst_persons:
        persons_tree.add(f"[chartreuse4]{p.get('name')}[/] - [bold link={create_link_person(p.personID)}][dodger_blue1]Person Link[/]")

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
            casting_tree.add( f"[yellow4]{i.get('name')} [orange1]{func(i)}[/] -  [bold link={create_link_person(i.personID)}][dodger_blue1]Person Link[/]")  

    console.print(tree)
    console.print("")  

#-------------------------- Gestion Table --------------------------#
def generate_table() -> Table:
    # table d'affichage des recherches
    table = Table()
    table.add_column('Personne')
    table.add_column('Recherche')
    
    for th, p, bool in liste_th:       
        if bool:
            # si c'est un objet Person, on récupère le nom 
            nom = lambda x: x.get('title') if not isinstance(x, str) else x
            table.add_row(nom(p), "[red]En cours" if th.is_alive() else "[green]Terminée")     
    return table

def live_table():
    # gestion de l'affichage des table de recherche
    with Live(generate_table()) as live:
        for _ in range(1000): # compteur empêchant l'update de cesser
            live.update(generate_table())
            if threading.active_count() == 2: # lancement de threads 
                for i, th in enumerate(liste_th):
                    # nb_threads limite le nb de threads 
                    if i < nb_threads:
                        try:
                            thread = th[0]
                            th[2] = True # status du thread :  il démarre
                            # on supprime le premier élément et on l'ajoute à la fin
                            # pour boucler sur toute la liste, nb_thread limitant l'itération 
                            liste_th.append(liste_th.pop(0))
                            thread.start()
                        except:
                            continue
            time.sleep(0.5)
            if liste_th_is_done() and threading.active_count() == 2:
                live.update(generate_table())
                time.sleep(0.5)
                break

def test_live_table():
    # gestion de l'affichage des table de recherche
    with Live(generate_table()) as live:
            while threading.active_count() > 2:
                live.update(generate_table())        
                for i, th in enumerate(liste_th):
                    # nb_threads limite le nb de threads 
                    if i < nb_threads:
                        try:
                            thread = th[0]
                            th[2] = True # status du thread :  il démarre
                            # on supprime le premier élément et on l'ajoute à la fin
                            # pour boucler sur toute la liste, nb_thread limitant l'itération 
                            liste_th.append(liste_th.pop(0))
                            thread.start()
                        except:
                            continue
                time.sleep(0.5)
                if liste_th_is_done() and threading.active_count() == 2:
                    live.update(generate_table())
                    time.sleep(0.5)
                    break

#-------------------------- Utils --------------------------#
def run_in_thread(f):
    # thread decorator
    def run(*args, **kwargs):
        thread = threading.Thread(target=f, args=args, kwargs=kwargs)
        # ajout dans une liste pour connaitre le status
        # et l'associer à une recherche
        liste_th.append([thread, args[0], False])
    return run

def stopwatch(f):
    def run(*args, **kwargs):
        debut = time.perf_counter()
        func = f()
        print(time.perf_counter() - debut)
        return func
    return run

def liste_th_is_done():
    # si un thread n'est pas lancé : False
    for i in liste_th:
        if not i[2]:
            return False
    return True

#-------------------------- Recherches personnes et films --------------------------#
@run_in_thread
def search_person(pers):
    # fonction de recherche pour chaque personne
    if isinstance(pers, str):
        persons = ia.search_person(pers)
        if not persons:
            print(f'{pers} not found.')
            sys.exit()
        person = ia.get_person(persons[0].personID)        
    else:
        person = ia.get_person(pers.personID)
    lst_persons.append(person) 

def search_lst_persons():
    # recherche de la liste de personnes via api
    liste = lst_persons[:]
    lst_persons.clear()
    for p in liste:
        search_person(p)
    live_table()

    # vérification de la recherche
    [lst_persons.remove(i) for i in lst_persons if i is None]
    if isinstance(lst_persons[0], str) or isinstance(lst_persons[0], int):
        print('Nobody found.')
        typer.Exit()

@run_in_thread
def search_movie(film):
    # fonction de recherche pour chaque film
    if isinstance(film, str): # vérifie si str ou obj Movie
        film = ia.search_movie(film)[0]
    movie = ia.get_movie(film.movieID)
    lst_movies.append(movie)

def search_lst_movies(title):
    # recherche de la liste de films via api
    lst_temp = lst_movies[:]
    lst_movies.clear()

    for m in lst_temp:
        search_movie(m)  
    live_table()   
    [lst_movies.remove(i) for i in lst_movies if i is None]

#-------------------------- Link IMDB --------------------------#
def create_link_movie(id):
    return f'http://www.imdb.com/title/tt{id}'

def create_link_person(id):
    return f'http://www.imdb.com/name/nm{id}'

#-------------------------- Utils --------------------------#
def get_persons(name):
    # recherche une liste de personnes
    for p in [name]:
        lst_persons.append(p)
        search_lst_persons()
    # retourne la personne si liste == 1
    # sinon lst_person est feed dans 'search_lst_persons()'
    if len(lst_persons) == 1:
        name = lst_persons[0]
        return name
    
def get_movies(title):
    # même fonctionnement que la précédente
    for m in [title]:
        lst_movies.append(m)
        search_lst_movies()
    if len(lst_movies) == 1:
        return lst_movies[0]
        
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
        # concaténation des noms en communs
        noms += f" - {pers.get('name')}"
        resultats[noms] = lst_movies

    return resultats

def get_filmo(person, isdir=False, isSorted=False):
    # renvoie la filmo grâce au genre : actor/actress
    person = get_persons(person)  
    if isdir and 'director' in person.get('filmography'):      
        # on retourne uniquement les films d'un réal 
        filmo = [i for i in person.get('director') if i.get('kind') == 'movie']
    else:
        filmo = person.get(get_genre_person(person))
    if isSorted:
        filmo.sort(key=lambda x: x.get('year'))
        return filmo
    return filmo
     
def get_genre_person(person):
    # cherche si c'est un acteur et détermine le genre   
    if 'actress' in person['filmography']:
        return 'actress'
    return 'actor'

x, y = [], []
def onpick(event):
    ind = event.ind
    x1 = x[int(ind)]
    y1 = y[int(ind)]
    title = ''
    for i in lst_movies:
        try:
            if i.get('year') == x1 and i.get('rating') == y1:
                title = i.get('title') 
        except:
            continue
    plt.annotate(f'{title} ({x1}), {y1}', xy=(x1, y1), xytext=(x1, y1))
    plt.draw()
    
def get_mean(name, isdir=False):
    global lst_movies
    liste_films = []
  
    lst_movies = get_filmo(name, isdir)
    search_lst_movies()
    # tri des films sans note 
    [liste_films.append(i.get('rating')) for i in lst_movies if i.get('rating')]
    return statistics.mean(liste_films)

#-------------------------- Typer commands --------------------------#
def test_search_actors(name: Annotated[list[str], typer.Argument(..., help="Nom d'un acteur")]):
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

@imdb.command()
def filmo(name: str = typer.Argument(..., help="Une seule personne à entrer"),  isdir: Annotated[Optional[bool], typer.Argument()] = False):
    """Retourne la filmographie d'un acteur ou réalisateur"""
    dico[name] = get_filmo(name, isdir)
    create_tree_persons(dico)

@imdb.command()
def cast(title: str = typer.Argument(..., help="Un seul titre à entrer")):
    """Retourne le casting d'un film."""
    # recherche du film   
    movie = get_movies(title)

    dico[movie] = movie.get('cast')
    create_tree_cast(dico, lambda i: f'({i.currentRole}) ')

@imdb.command()
def compare_casts(title: Annotated[list[str], typer.Option(..., '-t', help="Un titre par argument")]):
    """Compare le casting de plusieurs films"""
    get_movies(title)
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
def mean(name: str = typer.Option(..., '-n', help='Nom personne'), isdir: Annotated[Optional[bool], typer.Argument()] = False,
          d: Annotated[Optional[int], typer.Argument()] = None, f: Annotated[Optional[int], typer.Argument()] = None):
    """Retourne la moyenne totale de la filmo d'une personne"""
    # faire un callback pour remplir les listes
    print("{:.1f}".format(get_mean(name, isdir)))

@imdb.command()
def best_mean():
    set_films = set()
    set_actors = set()
    lst_ratings = []
    dico = {}
    movies = ia.get_top250_movies()
    
    bar_movies = tqdm.tqdm(movies[:1], position=0)
    for movie in bar_movies:
        set_actors.clear()
        bar_movies.set_description(movie.get('title'))
        ia.update(movie)
        bar_persons = tqdm.tqdm(movie.get('cast'), position=1, leave=False)
        for p in bar_persons:
            bar_persons.set_description(p.get('name'))
            set_actors.add(p)
    
    bar_actors = tqdm.tqdm(set_actors, position=0, leave=True)
    for pers in bar_actors:
        set_films.clear()
        bar_actors.set_description(pers.get('name'))
        filmo = ia.get_person_filmography(pers.personID)
        if 'actor' in filmo['data']['filmography']:
            for m in filmo['data']['filmography']['actor']:
                set_films.add(m)
            dico[pers] = list(set_films)
        else:
            for m in filmo['data']['filmography']['actress']:
                set_films.add(m)
            dico[pers] = list(set_films)
    
    bar_pers = tqdm.tqdm(dico.keys(), position=0)
    bar_ratings = tqdm.tqdm(dico.values(), position=1, leave=False)
    for p in bar_pers:
        bar_pers.set_description(p.get('name'))
        lst_ratings.clear()
        for movies in bar_ratings:
            for m in movies:
                bar_ratings.set_description(m.get('title'))
                ia.update(m)
                if m.get('rating'):
                    lst_ratings.append(m.get('rating'))
        print(p.get('name'), statistics.mean(lst_ratings))

@imdb.command()
def plot(name: str = typer.Option(..., '-n', help='Nom personne'), isdir: Annotated[bool, typer.Argument()] = False,
          n: Annotated[Optional[int], typer.Argument()] = None):
    """Affiche un graphique des notes des n derniers films d'une personne"""
    global lst_movies, x, y
    temp_lst = []
    # récupère les n derniers films d'une personne
    lst_movies = get_filmo(name, isdir)[:n]
    search_lst_movies()
    # tri des films sans date ou note
    [temp_lst.append(i) for i in lst_movies if i.get('year') and i.get('rating')]

    temp_lst.sort(key=lambda i: i.get('year'))
    # association date et note pour le graph
    x = [i.get('year') for i in temp_lst]
    y = [i.get('rating') for i in temp_lst]
    titles =  [i.get('title') for i in temp_lst]
    # création de l'event click sur le scatter
    fig, ax = plt.subplots()
    fig.canvas.mpl_connect('pick_event', onpick)
  
    # calcul scatter dots
    colors = [i for i in y]
    sizes = [i * 75 for i in y]
    # création du graph
    scatter = plt.scatter(x, y, picker=True, c=colors, s=sizes, alpha=0.5, cmap='RdYlGn',
                 label=ia.search_person(name)[0])
    # calcul moyenne
    plt.axhline(statistics.mean(y), color='b')
    # calcul médiane
    plt.axhline(statistics.median(y), color='r')

    plt.ylim(1, 10)
    plt.clim(1, 10)
    # création event hover
    mplcursors.cursor(scatter, hover=True).connect('add', lambda x: x.annotation.set_text(titles[x.index]))
    
    plt.colorbar()
    plt.legend()
    plt.show()

@imdb.command()
def proba(name: str = typer.Option(..., '-n', help='Nom personne')):
    """Calcul la note probable du prochain film d'une personne"""
    liste = get_filmo(name, isSorted=True)
    movie = liste.pop()
    dico = {}

    for i in liste:
        p = i.get('rating')
        if p in dico:
            dico[p] += 1
        else:
            dico[p] = 1

    proba = {}
    for note, freq in dico.items():
        proba[note] = freq / len(liste)
    print(movie, movie.get('rating'), movie.get('year'))
    dict(sorted(proba.items(), key=lambda x: x[1]))
    print(list(proba.items())[0])

if __name__ == '__main__':
    # appel de l'app avec typer
    #filmo_actor('jake lloyd')
    imdb()
