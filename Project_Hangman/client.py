import pygame
from network import Network, NO_CHALLENGES_MSG
from hangman import *
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
    guess_made = False
    is_signed_out = False

    running = True
    net = Network("192.168.1.182", 9999)
    window.fill(WINDOW_COLOUR)
    mode = MODES['start'] # showcase start screen

    while running:
        mouse = pygame.mouse.get_pos()
        letter = ''

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                break
            if event.type == pygame.KEYDOWN:
                letter = event.unicode # for play mode later

                if mode == MODES['play']:
                    guess_made = True

                if username_active:
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
                        net.connect() # trying to connect to server
                        if mode == MODES['login']:
                            login_info = net.send([username, password]) 
                            if net.recv_login_user_info(login_info):
                                status_message = ''
                                mode = MODES['home']
                            else:
                                status_message = 'Incorrect username or password.'
                        elif mode == MODES['register']:
                            register_info = net.send([username, password])
                            if net.register_user(register_info):
                                status_message = ''
                                mode = MODES['home']
                            else:
                                status_message = 'This username is already taken.'
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
                        challenge_info = net.send([friend_username, ch_word, ch_hint]) 
                        if net.send_challenge(challenge_info):
                            status_message = 'Successfully sent to friend!'
                        else:
                            status_message = 'No such friend in friend list.'
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
                game = net.create_game(option)
                mode = MODES['play']
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
            mode, guess_made = draw_play(mode, event, mouse, game, letter, guess_made)
        
        elif mode == MODES['leaderboard']:
            leaderboard_list = net.get_leaderboard()
            mode = draw_leaderboard(mode, event, mouse, leaderboard_list)
        
        elif mode == MODES['friends']:
            friend_list = net.get_friends()
            mode = draw_friends_list(mode, event, mouse, friend_list)
            
        pygame.display.update()

main()