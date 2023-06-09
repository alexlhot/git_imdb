from imdb_api import *

def test_get_movies():
    movie = get_movies('matrix')
    assert movie.get('title') == 'The Matrix'
    get_movies(['matrix'])
    movie = lst_movies[0]
    assert movie.get('title') == 'The Matrix'

def test_get_persons():
    person = get_persons('keanu reeves')
    assert person.get('name') == 'Keanu Reeves'
    get_persons(['keanu reeves'])
    person = lst_persons[0]
    assert person.get('name') == 'Keanu Reeves'

def test_get_genre_person_actor():
    assert get_genre_person(ia.get_person('000001')) == 'actor'
    assert get_genre_person(ia.get_person('000002')) == 'actress'

def test_liste_th_is_done():
    liste_th.append(['test', 'test1', False])
    liste_th.append(['test2', 'test6', True])
    liste_th.append(['test3', 'test8', True])
    assert liste_th_is_done() == False

def test_get_filmo():
    person = get_persons('danny lloyd')
    assert get_filmo(person)[-1] == 'The Shinning'
    person = get_persons('kubrick')
    assert get_filmo(person, True)[0] == 'Eyes Wide Shut'
