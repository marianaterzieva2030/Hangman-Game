import pygame
from constants import MODES, LOGGED_IN_MODES, NO_CHALLENGES_MSG, SERVER_HOST, SERVER_PORT
from network import Network
from utils import *

# game loop
def main():
    
    username, password, password_dots, status_message = ('', '', '', '')
    username_active = False
    password_active = False

    # challenge info
    ch_word, ch_hint, friend_username = ('', '', '')
    friend_active, word_active, hint_active = (False, False, False)
     
    game = None
    is_signed_out = False

    running = True
    net = Network(SERVER_HOST, SERVER_PORT)
    window.fill(WINDOW_COLOUR)
    mode = MODES['start'] # showcase start screen

    while running:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                break
            if event.type == pygame.KEYDOWN:

                if mode == MODES['play']:
                    if (isinstance(game, GameState) and not game.is_over and event.unicode.isalpha()):
                        error = net.guess(game, event.unicode)
                        if error:
                            status_message = error

                elif username_active:
                    if event.key == pygame.K_RETURN:
                        username_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                        status_message = ''
                    else:
                        username += event.unicode

                elif password_active:
                    if event.key == pygame.K_RETURN:
                        password_active = False
                        if not username.strip() or not password:
                            status_message = 'Enter a username and a password.'
                        else:
                            if mode == MODES['login']:
                                draw_loading('Logging in...')
                                error = net.login(username.strip(), password)
                            else:
                                draw_loading('Registering...')
                                error = net.register(username.strip(), password)
                            if error is None:
                                status_message = ''
                                mode = MODES['home']
                            else:
                                status_message = error
                    elif event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                        password_dots = password_dots[:-1]
                        status_message = ''
                    else:
                        password_dots += '*'
                        password += event.unicode
                
                elif word_active:
                    if event.key == pygame.K_RETURN:
                        word_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        ch_word = ch_word[:-1]
                        status_message = ''
                    else:
                        ch_word += event.unicode
                
                elif friend_active:
                    if event.key == pygame.K_RETURN:
                        friend_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        friend_username = friend_username[:-1]
                        status_message = ''
                    else:
                        friend_username += event.unicode
                
                elif hint_active:
                    if event.key == pygame.K_RETURN:
                        hint_active = False
                        error = net.send_challenge(friend_username.strip(), ch_word, ch_hint)
                        status_message = 'Successfully sent to friend!' if error is None else error
                    elif event.key == pygame.K_BACKSPACE:
                        ch_hint = ch_hint[:-1]
                        status_message = ''
                    else:
                        ch_hint += event.unicode
        
        if mode == MODES['start']:
            mode, username, password, password_dots = draw_start_page(
                mode, event, mouse, username, password, password_dots)
                    
        elif mode == MODES['login']:
            mode, username_active, password_active = draw_form_page(
                'Login', mode, event, mouse, username, password_dots, status_message, 
                username_active, password_active)
            
        elif mode == MODES['register']:
            mode, username_active, password_active = draw_form_page(
                'Login', mode, event, mouse, username, password_dots, status_message, 
                username_active, password_active)
        
        elif mode == MODES['home']:
            mode, is_signed_out = draw_home_page(mode, event, mouse, is_signed_out)
            if is_signed_out:
                net.disconnect()
            is_signed_out = False

        elif mode == MODES['game_modes']:
            game = None
            option = draw_game_page(mode, event, mouse)
            if isinstance(option, str):
                draw_loading('Finding a word...')
                game = net.new_game(option) # GameState, or an error string
                if isinstance(game, GameState) or game == NO_CHALLENGES_MSG:
                    mode = MODES['play']
                else:
                    status_message = game # could be "Connection lost."
                    game = None
            else:
                mode = option
        
        elif mode == MODES['send_challenge']:
            mode, friend_active, word_active = draw_form_page(
                'Challenge a Friend', mode, event, mouse, friend_username, ch_word, status_message, 
                friend_active, word_active)
            
            custom_hint_surf = smaller_title.render('Hint', False, 'White')
            hint_rect_dimensions = (230, 520, 720, 60)
            hint_rect_padding_dim = (235, 525, 710, 50)

            window.blit(custom_hint_surf, (110, 518))
            pygame.draw.rect(window, HOVER_COLOUR, hint_rect_dimensions, 3)

            hint_rect = pygame.Rect(hint_rect_dimensions)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if hint_rect.collidepoint(mouse):
                    hint_active = True
                    word_active = False
                    friend_active = False
                else:
                    hint_active = False
            
            if hint_active:
                pygame.draw.rect(window, BUTTON_COLOUR, hint_rect, 3)
            else:
                pygame.draw.rect(window, HOVER_COLOUR, hint_rect, 3)
            pygame.draw.rect(window, WINDOW_COLOUR, hint_rect_padding_dim)

            hint_input_surf = bulgarian_font.render(ch_hint, False, 'White')
            window.blit(hint_input_surf, (hint_rect.x + 10, hint_rect.y + 20))


        elif mode == MODES['play']:
            mode, hint_clicked = draw_play(mode, event, mouse, game)
            if (hint_clicked and isinstance(game, GameState) 
                and not game.hint_used and not game.is_over):
                error = net.hint(game)
                if error:
                    status_message = error
        
        elif mode == MODES['leaderboard']:
            leaderboard_list = net.get_leaderboard()
            mode = draw_leaderboard(mode, event, mouse, leaderboard_list)
        
        elif mode == MODES['friends']:
            friend_list = net.get_friends()
            mode = draw_friends_list(mode, event, mouse, friend_list)
            
        pygame.display.update()

main()