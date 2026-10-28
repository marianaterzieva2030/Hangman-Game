import pygame
from constants import MODES, LOGGED_IN_MODES, NO_CHALLENGES_MSG, SERVER_HOST, SERVER_PORT
from network import Network
from utils import *
from game_state import GameState

FPS = 60
MAX_LEN = {'username': 20, 'password': 32, 'friend': 20, 'word': 9, 'hint': 80, 'add': 20}

def edit_text(text, event, max_len):
    """Apply one KEYDOWN event to a text field and return the new text."""
    if event.key == pygame.K_BACKSPACE:
        return text[:-1]
    if event.unicode and event.unicode.isprintable() and len(text) < max_len:
        return text + event.unicode
    return text

# game loop
def main():

    net = Network(SERVER_HOST, SERVER_PORT)
    
    username, password = ('', '')
    username_active, password_active = (False, False)
    friend_active, word_active, hint_active = (False, False, False)
    add_name, add_active = ('', False)

    status_message, pending_message = ('', '')

    # challenge info
    ch_word, ch_hint, friend_username = ('', '', '')
     
    game = None
    leaderboard_list, friends_list = [], []

    mode = MODES['start'] # showcase start screen
    prev_mode = None
    running = True

    while running:
        mouse = pygame.mouse.get_pos()
        events = pygame.event.get()
        click = next((e for e in events 
                      if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1), # left button only
                      pygame.event.Event(pygame.NOEVENT))

        if mode in LOGGED_IN_MODES and not net.logged_in:
            mode = MODES['start']
            pending_message = 'Connection lost. Please log in again.'

        # reset input state once the mode changes
        if mode != prev_mode:
            username_active = password_active = False
            word_active = friend_active = hint_active = add_active = False
            status_message, pending_message = (pending_message, '')

            if mode in (MODES['start'], MODES['login'], MODES['register']):
                username = password = ''

            if mode in (MODES['login'], MODES['register']):
                username_active = True
                
            if mode == MODES['send_challenge']:
                friend_username = ch_word = ch_hint = ''
                friend_active = True

            if mode != MODES['play']:
                game = None

            if mode == MODES['leaderboard']:
                leaderboard_list = net.leaderboard() or []

            elif mode == MODES['friends']:
                friends_list = net.friends() or []
                add_name = ''
                add_active = True
            prev_mode = mode


        for event in events:
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if mode == MODES['play']:
                    if (isinstance(game, GameState) 
                        and not game.is_over and event.unicode.isalpha()):
                        error = net.guess(game, event.unicode)
                        if error:
                            status_message = error

                elif username_active:
                    if event.key == pygame.K_RETURN:
                        username_active = False
                        password_active = True
                    else:
                        username = edit_text(username, event, MAX_LEN['username'])
                        status_message = ''

                elif password_active:
                    if event.key == pygame.K_RETURN:
                        password_active = False
                        if not username.strip() or not password:
                            status_message = 'Enter a username and a password.'
                        else:
                            draw_loading('Connecting...')
                            submit = net.login if mode == MODES['login'] else net.register
                            error = submit(username.strip(), password)
                            if error is None:
                                mode = MODES['home']
                            else:
                                status_message = error
                    else:
                        password = edit_text(password, event, MAX_LEN['password'])
                        status_message = ''

                elif add_active:
                    if event.key == pygame.K_RETURN:
                        name = add_name.strip()
                        if not name:
                            status_message = 'Enter a username.'
                        else:
                            error = net.add_friend(name)
                            if error is None:
                                status_message = f'{name} is now your friend!'
                                add_name = ''
                                friends_list = net.friends() or friends_list
                            else:
                                status_message = error
                    else:
                        add_name = edit_text(add_name, event, MAX_LEN['add'])
                        status_message = ''

                # sending challenge to friend
                elif friend_active:
                    if event.key == pygame.K_RETURN:
                        friend_active = False
                        word_active = True
                    else:
                        friend_username = edit_text(friend_username, event, MAX_LEN['friend'])
                        status_message = ''
            
                elif word_active:
                    if event.key == pygame.K_RETURN:
                        word_active = False
                        hint_active = True
                    else:
                        ch_word = edit_text(ch_word, event, MAX_LEN['word'])
                        status_message = ''
                
                elif hint_active:
                    if event.key == pygame.K_RETURN:
                        hint_active = False
                        error = net.send_challenge(friend_username.strip(), ch_word, ch_hint)
                        if error is None:
                            status_message = 'Successfully sent to friend!'
                            friend_username = ch_word = ch_hint = ''
                        else:
                            status_message = error
                    else:
                        ch_hint = edit_text(ch_hint, event, MAX_LEN['hint'])
                        status_message = ''

        if not running:
            break
        
        if mode == MODES['start']:
            mode = draw_start_page(mode, click, mouse)
                    
        elif mode == MODES['login']:
            mode, username_active, password_active = draw_form_page(
                'Login', mode, click, mouse, username, '*' * len(password), 
                status_message, username_active, password_active)
            
        elif mode == MODES['register']:
            mode, username_active, password_active = draw_form_page(
                'Register', mode, click, mouse, username, '*' * len(password), 
                status_message, username_active, password_active)
        
        elif mode == MODES['home']:
            mode, is_signed_out = draw_home_page(mode, click, mouse, False)
            if is_signed_out:
                net.disconnect()

        elif mode == MODES['game_modes']:
            option = draw_game_page(mode, click, mouse)

            if isinstance(option, str):
                draw_loading('Finding a word...')
                result = net.new_game(option) # GameState or an error string

                # averts the bug where a click on the current page could 
                # avtivate a button in the same area on the next page
                pygame.event.clear((pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN))
                if isinstance(result, GameState) or result == NO_CHALLENGES_MSG:
                    game = result
                    mode = MODES['play']
                else:
                    status_message = result # could be "Connection lost."
            else:
                mode = option
        
        elif mode == MODES['send_challenge']:
            mode, friend_active, word_active, hint_active = draw_challenge_page(
                mode, click, mouse, friend_username, ch_word, ch_hint,
                status_message, friend_active, word_active, hint_active
            )
            
        elif mode == MODES['play']:
            mode, hint_clicked = draw_play(mode, click, mouse, game)
            if (hint_clicked and isinstance(game, GameState) 
                and not game.hint_used and not game.is_over):
                error = net.hint(game)
                if error:
                    status_message = error
        
        elif mode == MODES['leaderboard']:
            mode = draw_leaderboard(mode, click, mouse, leaderboard_list)
        
        elif mode == MODES['friends']:
            mode, add_active = draw_friends_list(
                mode, click, mouse, friends_list, add_name, add_active, status_message
            )

        # status line for screens that have no status message area of their own
        if mode in (MODES['start'], MODES['home'], MODES['game_modes']):
            draw_status(status_message)
        elif mode == MODES['play']:
            draw_status(status_message, (WINDOW_WIDTH // 2, 115))
            
        pygame.display.update()
        clock.tick(FPS)


    net.close()
    pygame.quit()


if __name__ == '__main__':
    main()