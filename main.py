import threading
import time
import sys
from itertools import zip_longest
import itertools
from rich.progress import track
import typer
from typing import List, Optional
from typing_extensions import Annotated
from rich import *
from rich.console import Console
from rich.tree import Tree
from prodict import Prodict
from imdb import Cinemagoer
import keyboard

app = typer.Typer(name='IMDB', add_completion=False, help='Recherche IMDB')

class Demo(Prodict):
    # variables de demographics
    all = 'ttrt fltr imdb users'
    all_18 = 'ttrt fltr aged under 18'
    all_1829 = 'ttrt fltr aged 18 29'
    all_3044 = 'ttrt fltr aged 30 44'
    all_45 = 'ttrt fltr aged 45 plus'
    males = 'ttrt fltr males'
    m_18 = 'ttrt fltr males aged under 18'
    m_1829 = 'ttrt fltr males aged 18 29'
    m_3044 = 'ttrt fltr males aged 30 44'
    m_45 = 'ttrt fltr males aged 45 plus'
    females = 'ttrt fltr females'
    f_18 = 'ttrt fltr females aged under 18'
    f_1829 = 'ttrt fltr females aged 18 29'
    f_3044 = 'ttrt fltr females aged 30 44'
    f_45 = 'ttrt fltr females aged 45 plus'
    top_100 = 'ttrt fltr top 1000 voters'
    us = 'ttrt fltr us users'
    non_us = 'ttrt fltr non us users'


def create_tree_persons(dico):
    console = Console(record=True, width=100)

    console.print("")
    console.print("")
    tree = Tree("Collaborations", guide_style="bold bright_black")
    for p, movies in dico.items():   
        movies_tree = tree.add(f'[green]{[p]}', guide_style="bright_black")
        if movies:                 
            for movie in movies:
                movies_tree.add( f"[yellow]{movie['title']} - [bold link={create_link_movie(movie.movieID)}][blue]Movie Link[/]")
        else:
            movies_tree.add(f"[red]No movies shared.")
    persons_tree = tree.add('[white]Liste des acteurs')
    for p in lst_persons:
        persons_tree.add(f"[yellow]{p['name']}[/] - [bold link={create_link_person(p.personID)}][blue]Person Link[/]")

    console.print(tree)
    console.print("")   

def create_tree_cast(dico):
    console = Console(record=True, width=100)

    console.print("")
    console.print("")
    tree = Tree("Casting", guide_style="bold bright_black")
    for m, cast in dico.items():
        casting_tree = tree.add(f'[green]{[mov["title"] for mov in m]}', guide_style="bright_black")
        for i in cast:
            casting_tree.add( f"[yellow]{i['name']} [green]({i.currentRole})[/] - [bold link={create_link_person(i.personID)}][blue]Movie Link[/]")  

    console.print(tree)
    console.print("")  

def run_in_thread(f):
    def run(*args, **kwargs):
        thread = threading.Thread(target=f, args=args, kwargs=kwargs)
        thread.start()
        print(thread, 'start')
        return thread
    return run

def while_threads():
    i = 0
    while threading.active_count() > 1:
        time.sleep(0.5)
        i += 0.5
        print(f'{i} secondes', end='\r')

ia = Cinemagoer()
dico = Demo()
lst_persons = []
lst_movies = []
set_movies = set()
titre = ''

def start():    
    # on récupère les objets Person
    search_lst_persons()
    while_threads()    
    find_shared_movies()

@app.command()
def search_actors(name: Annotated[list[str], typer.Argument(..., help="Enter persons' name ")]):
    """Recherche les correspondances entre plusieurs personnes"""
    global lst_persons

    set_noms = set()
    noms = [iter(name)] * 2
    zip_noms = zip_longest(*noms, fillvalue='')
    [set_noms.add(f'{i[0]} {i[1]}') for i in zip_noms]
    lst_persons = list(set_noms)
    search_lst_persons()
    find_shared_movies()

def get_title_from_keys():
    global titre
    set_movies.add(titre)
    # remonte le curseur, au début de la ligne
    sys.stdout.write('\033[1A\033[1G')
    sys.stdout.write(titre)
    # le redescend pour conntinuer l'ajout 
    sys.stdout.write('\033[1B')
    # reset le titre
    titre = ''

def on_keypress(event):
    global titre
    key = event.name
    
    if key == 'space':
        titre += ' '
        print(' ', end='')
    elif key == 'backspace':
        if len(titre) > 0:
            sys.stdout.write('\033[2K\033[1G')# erase line and go to beginning of line
            titre = titre[:-1]
            print(titre, end='')
    elif key == 'enter':
        set_movies.add(titre)
        print('\n', set_movies)
        exit()
    else:
        print(key, end='')
        titre += key

@app.command()
def keys():
    """Recherche des films"""
    print('Entrer titres films, séparés par "," ; Enter pour confirmer :')
    print('')    
    keyboard.on_press(on_keypress)
    keyboard.add_hotkey(',', get_title_from_keys)
    keyboard.wait()

@run_in_thread
def search_person(pers):    
    persons = ia.search_person(pers)
    person = ia.get_person(persons[0].personID)
    lst_persons.remove(pers) 
    lst_persons.insert(0, person)
    
def search_lst_persons():
    for p in lst_persons:           
        search_person(p)
    while_threads()       
    
def create_link_movie(id):
    return f'http://www.imdb.com/title/tt{id}'

def create_link_person(id):
    return f'http://www.imdb.com/name/nm{id}'

#@app.command()
def get_notes_real(nom):
    lst_persons.append(nom)
    search_lst_persons()
    
    for person in lst_persons:
        for film in person['director']:
            film = ia.update(film, 'vote details')
            try:
                lst_movies.append([film['title'], float(film['notes'])])
            except:
                print(film)
                continue
        for i in lst_movies:
            for j, k in i:
                print(j, k)

def find_shared_movies():  
    resultats = {}
    for x in range(2, len(lst_persons)+1):
        for p in itertools.combinations(lst_persons, x):
            lst_movies = set(get_filmo(p[0]))
            for pers in p[1:]:
                lst_movies &= set(get_filmo(pers))
            resultats[p] = lst_movies
    
    create_tree_persons(resultats)

@run_in_thread    
def search_movie(name):
    movie = ia.get_movie(ia.search_movie(name)[0].movieID)    
    lst_movies.remove(name) 
    lst_movies.insert(0, movie)

def search_lst_movies():
    for m in lst_movies:
        search_movie(m)
    while_threads()

def get_genre_person(person):
    # cherche si c'est un acteur et détermine le genre
    if 'actor' in person['filmography']:
        return 'actor'
    elif 'actress' in person['filmography']:
        return 'actress'
       
def get_filmo(person):
    try:
        genre = get_genre_person(person)
        return  person[genre]
    except:
        return []
 
@app.command()
def filmo(nom: str = typer.Option(..., prompt="Enter actor's names ")):
    """Retourne la filmographie d'une personne"""
    lst_persons.append(nom)
    search_lst_persons()
    dico[lst_persons[0]] = get_filmo(lst_persons[0])
    create_tree_persons(dico)

@app.command()
def casting(title: str = typer.Option(..., prompt="Enter movie's names ")):
    """Retourne le cast d'un film"""
    movie = search_movie(title)
    dico[movie] = movie['cast']
    create_tree_cast(dico)

@app.command()
def compare_casts(movies: Annotated[list[str], typer.Option(..., '-m')]):
    """Compare le cast de plusieurs films"""
    global lst_movies
    lst_movies = movies
    print(movies)
    search_lst_movies()
    resultats = {}

    for x in range(2, len(lst_movies)+1):
        for m in itertools.combinations(lst_movies, x):
            liste = set(m[0]['cast'])
            for mov in m[1:]:
                liste &= set(mov['cast'])
            resultats[m] = liste

    create_tree_cast(resultats)

@app.command()
def demographics(nom: str = typer.Option(..., prompt="Enter movie's name ")):
    """Get the démographics of a movie"""
    movie = search_movie(nom)
    ia.update(movie, 'vote details')
    print(movie['demographics'][dico.all])


if __name__ == '__main__':
    #app()
    #search_actors(['peter', 'stormare', 'keanu', 'reeves', 'lance', 'reddick', 'carrie', 'fisher', 'lance', 'reddick', 'common'])
    #filmo('keanu reeves')
    #compare_casts(['matrix', 'matrix-revolutions'])
    get_notes_real('shyamalan')