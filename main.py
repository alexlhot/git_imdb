import threading
import time
import sys
from itertools import zip_longest
import itertools
import typer
from typing_extensions import Annotated
from rich import *
from rich.console import Console
from rich.tree import Tree
from rich.live import Live
from rich.table import Table
from prodict import Prodict
from imdb import Cinemagoer
from imdb import Movie
import keyboard
import plotext as plt


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
    print(dico.values())

    console.print("")
    console.print("")
    tree = Tree("Collaborations", guide_style="bold bright_black")
    
    for p, movies in dico.items():
        movies_tree = tree.add(f'[green]{p}', guide_style="bright_black")
        if movies:
            for movie in movies:
                movies_tree.add( f"[yellow]{movie['title']} - [bold link={create_link_movie(movie.movieID)}][blue]Movie Link[/]")
        """ else:
            movies_tree.add(f"[red]No movies shared.")"""
    persons_tree = tree.add('[white]Liste des acteurs')
    for p in lst_persons:
        persons_tree.add(f"[yellow]{p['name']}[/] - [bold link={create_link_person(p.personID)}][blue]Person Link[/]")

    console.print(tree)
    console.print("")

def create_tree_cast(dico, func):
    console = Console(record=True, width=100)

    console.print("")
    console.print("")
    tree = Tree("Casting", guide_style="bold bright_black")
    for m, cast in dico.items():
        casting_tree = tree.add(f'[green]{func(m)}', guide_style="bright_black")
        for i in cast:
            casting_tree.add( f"[green]{i['name']} [green]({i.currentRole})[/] - [bold link={create_link_person(i.personID)}][blue]Movie Link[/]")  

    console.print(tree)
    console.print("")  

def generate_table() -> Table:
    table = Table()
    table.add_column('Personne')
    table.add_column('Recherche')

    for th, p in dico_th.items():
        nom = p
        if not isinstance(nom, str):
            nom = p['title']
        table.add_row(nom, "[red]En cours" if th.is_alive() else "[green]Terminée")
    return table

def test_generate_table() -> Table:
    table = Table()
    table.add_column('Personne')
    table.add_column('Recherche')

    for th, p in dico_th.items():
        nom = p
        if not isinstance(nom, str):
            nom = p['name']
        table.add_row(nom, "[red]En cours" if th.is_alive() else "[green]Terminée")
        for _ in table.rows:
            if not th.is_alive():
                table.rows.clear()
           
 
    return table

def live_table():
    with Live(generate_table()) as live:
        for _ in range(1000):
            live.update(generate_table())
            time.sleep(0.5)
            if threading.active_count() == 2:
                live.update(generate_table())
                time.sleep(0.5)
                break

def run_in_thread(f):
    def run(*args, **kwargs):
        thread = threading.Thread(target=f, args=args, kwargs=kwargs)     
        thread.start()
        dico_th[thread] = args[0]
        return thread
    return run

ia = Cinemagoer()
dico = {}
lst_persons = []
lst_movies = []
set_movies = set()
dico_th = {}
titre = ''

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

liste = []
liste2 = []
lock = threading.Lock()
def test_search_person(id):
    liste2.append(ia.get_person(id))
def test(person):
    [liste.append(p) for p in ia.search_person(person)]

def test_search_lst_persons():
    for p in lst_persons:
        th = threading.Thread(target=test, args=(p,))
        dico_th[th] = p
        th.start()
    time.sleep(3)
    for p in liste:
        th = threading.Thread(target=test_search_person, args=(p.personID,))
        th.start()
        dico_th[th] = p
    live_table()

    print(liste2)

@run_in_thread
def search_person(pers):
    try:
        persons = ia.search_person(pers)
        person = ia.get_person(persons[0].personID)
        lst_persons.remove(pers) 
        lst_persons.insert(0, person)
    except:
        print(f'search_person, {pers} not found.')

def search_lst_persons():
    liste_tests = lst_persons
    print(liste_tests, lst_persons)
    for p in lst_persons:
        search_person(p)        
    live_table()
    print(liste_tests, lst_persons)#"""a voir !"""
    if liste_tests == lst_persons:
        print(f'lst_persons not found.')
        sys.exit()

def create_link_movie(id):
    return f'http://www.imdb.com/title/tt{id}'

def create_link_person(id):
    return f'http://www.imdb.com/name/nm{id}'

def get_notes_real(nom):
   year, rating, titles = [2017, 2019, 2022, 2025, 2026], [2.8, 7, 5.2, 1, 9.4], ['Us', 'Get Out', 'Nope']
   
   lst_persons.append(nom)
   search_lst_persons()
   p = lst_persons[0]
   [lst_movies.append(i) for i in p['director']]
   search_lst_movies_by_id()
   #[lst_movies.append(i['title']) for i in p['director']]
   #search_lst_movies()
   year, rating, titles = [], [], []
   for film in lst_movies:
        try:
            if film['year'] and film['rating']:
                year.append(film['year'])
                rating.append(film['rating'])
                titles.append(film['title'])
        except Exception as e:
            print(e)
   test_plot(year, rating, p['name'])
   
def test_plot(ratings, year, name):
    plt.scatter(ratings, year)
    print(plt.doc.scatter())
    plt.title(f'Ratings of {name}')
    plt.show()

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
def search_movie(film):
    movie = ia.get_movie(ia.search_movie(film)[0].movieID)
    lst_movies.remove(film)
    lst_movies.insert(0, movie)

def search_lst_movies():
    for m in lst_movies:
        search_movie(m)  
    live_table()

@run_in_thread
def search_movie_by_id(film):
    movie = ia.get_movie(film.movieID)
    lst_movies.remove(film)
    lst_movies.insert(0, movie)

def search_lst_movies_by_id():
    for m in lst_movies:
        search_movie_by_id(m)         
    live_table()

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
        return None
 
@app.command()
def filmo(nom: str = typer.Option(..., prompt="Enter actor's name ")):
    """Retourne la filmographie d'une personne"""
    lst_persons.append(nom)
    search_lst_persons()
    dico[lst_persons[0]] = get_filmo(lst_persons[0])
    create_tree_persons(dico)

@app.command()
def cast(title: str = typer.Option(..., '-t', prompt="Enter movie's name ")):
    """Retourne le casting d'un seul film"""
    lst_movies.append(title)
    search_lst_movies()
    movie = lst_movies[0]
    dico[movie] = movie['cast']
    create_tree_cast(dico, lambda m: m)

@app.command()
def compare_cast(movies: Annotated[list[str], typer.Option(..., '-m')]):
    """Compare le cast de plusieurs films"""
    #global lst_movies
    [lst_movies.append(m) for m in movies]
    search_lst_movies()
    resultats = {}

    for x in range(2, len(lst_movies)+1):
        for m in itertools.combinations(lst_movies, x):
            liste = set(m[0]['cast'])
            for mov in m[1:]:
                liste &= set(mov['cast'])
            resultats[m] = liste

    create_tree_cast(resultats, (lambda m: m['title'] for m in resultats.values()))

@app.command()
def demographics(nom: str = typer.Option(..., prompt="Enter movie's name ")):
    """Get the démographics of a movie"""
    lst_movies.append(nom)
    search_lst_movies()
    for movie in lst_movies:
        ia.update(movie, 'vote details')
        print(movie['demographics'][dico.all])

if __name__ == '__main__':
    #app()
    #search_actors(['peter', 'stormare', 'chloe', 'moretz', 'lance', 'reddick', 'nicolas', 'cage', 'lance', 'reddick', 'common'])
    #filmo('keanu reeves common')
    compare_cast(['goodfellas', 'brazil'])
    #get_notes_real('Chad Stahelski')
    #cast('avatar')
    #lst_persons.append('chloe moretz')
    #test_search_lst_persons()