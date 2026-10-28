import pygame
from constants import MODES, NO_CHALLENGES_MSG, FONT_DIR, IMAGE_DIR
from game_state import GameState

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600
WINDOW_COLOUR = '#383682'
BUTTON_COLOUR = '#868fd9'
HOVER_COLOUR = '#27265c'

LEADERBOARD_NAME_MAX = 20
FRIENDS_VISIBLE = 6

pygame.init()

window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('DDZ')

clock = pygame.time.Clock() # clock to control the frame rate

title_font = pygame.font.Font(str(FONT_DIR / 'HouseOfTerror Regular.otf'), 90)
subtitle_font = pygame.font.Font(str(FONT_DIR / 'DiaryOfAn8BitMage-lYDD.ttf'), 40)
smaller_title = pygame.font.Font(str(FONT_DIR / 'HouseOfTerror Regular.otf'), 50)
basic_font = pygame.font.Font(str(FONT_DIR / 'HouseOfTerror Regular.otf'), 35)
guessing_word_font = pygame.font.Font(str(FONT_DIR / 'DiaryOfAn8BitMage-lYDD.ttf'), 50)
bulgarian_font = pygame.font.Font(str(FONT_DIR / 'DiaryOfAn8BitMage-lYDD.ttf'), 25)

back_button = subtitle_font.render('Back', False, 'White')
home_button = subtitle_font.render('Home', False, 'White')

def load_image(name, scale=1.0):
    image = pygame.image.load(str(IMAGE_DIR / name)).convert_alpha()
    if scale != 1.0:
        width, height = image.get_size()
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
    return image

zombie_python_img = load_image('zombie_python.PNG', scale=1/3)
zombie_knight_img = load_image('knight_zombie.PNG', scale=1/2.3)
zombie_hand_img = load_image('zombie_hand.PNG', scale=1/2.5)
peashooter_img = load_image('peashooter_pea.PNG')


def mouse_hovering(mouse_pos, rect_dimensions):
    x, y, width, height = rect_dimensions
    return x <= mouse_pos[0] <= x + width and y <= mouse_pos[1] <= y + height


def fit_tail(text, font, max_width):
    """Return the end of `text` that fits in max_width pixels. Long input scrolls instead of overflowing."""
    while text and font.size(text)[0] > max_width:
        text = text[1:]
    return text


def draw_button(mouse_pos, text_surface, rect_dimensions):
    x, y, width, height = rect_dimensions

    if mouse_hovering(mouse_pos, rect_dimensions):
        pygame.draw.rect(window, HOVER_COLOUR, (x, y, width, height))
    else:
        pygame.draw.rect(window, BUTTON_COLOUR, (x, y, width, height))

    text_rect = text_surface.get_rect(
        center=(x + width // 2, y + height // 2)
    )

    window.blit(text_surface, text_rect)

    return pygame.Rect(rect_dimensions)


def draw_multiline_text(text, font, colour, x, y, line_spacing=10):
    lines = text.split('\n')

    for i, line in enumerate(lines):
        surf = font.render(line, False, colour)
        window.blit(surf, (x, y + i * (surf.get_height() + line_spacing)))


def draw_wrapped_text(text, font, colour, rect):
    x, y, width, height = rect

    words = text.split(' ')
    lines = []
    current_line = ''

    for word in words:
        test_line = current_line + word + ' '

        test_surface = font.render(test_line, False, colour)

        if test_surface.get_width() <= width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + ' '

    lines.append(current_line)

    for i, line in enumerate(lines):
        surf = font.render(line.strip(), False, colour)
        window.blit(surf, (x, y + i * (surf.get_height() + 5)))


def draw_status(message, center=(WINDOW_WIDTH // 2, 555)):
    if message:
        surf = bulgarian_font.render(message, False, 'White')
        window.blit(surf, surf.get_rect(center=center))


def draw_start_page(mode, event, mouse):
    game_title = title_font.render('DDZ', False, 'White')
    subtitle = subtitle_font.render('Да Довършим Зомбито', False, 'White')

    login_text = subtitle_font.render('Login', False, 'White')
    register_text = subtitle_font.render('Register', False, 'White')

    window.fill(WINDOW_COLOUR)

    window.blit(game_title, (530, 40))
    window.blit(subtitle, (360, 150))

    window.blit(zombie_python_img, (40, 130))
    window.blit(zombie_knight_img, (890, 140))

    login_rect = draw_button(
        mouse,
        login_text,
        (390, 340, 150, 60)
    )

    register_rect = draw_button(
        mouse,
        register_text,
        (580, 340, 225, 60)
    )

    if event.type == pygame.MOUSEBUTTONDOWN:
        if login_rect.collidepoint(mouse):
            mode = MODES['login']

        elif register_rect.collidepoint(mouse):
            mode = MODES['register']

    return mode


def draw_form_page(page_type, mode, event, mouse,
                   first_field, second_field,
                   status_message,
                   first_active, second_active,
                   input_font=None):

    input_font = basic_font if input_font is None else input_font

    title = title_font.render(page_type, False, 'White')

    if page_type == 'Challenge a Friend':
        first_field_surf = smaller_title.render('Friend', False, 'White')
        second_field_surf = smaller_title.render('Word', False, 'White')
        button_type = home_button
        button_dimensions = (1020, 45, 135, 60)
    else:
        first_field_surf = smaller_title.render('Username', False, 'White')
        second_field_surf = smaller_title.render('Password', False, 'White')
        button_type = back_button
        button_dimensions = (60, 40, 140, 60)

    window.fill(WINDOW_COLOUR)

    if page_type == 'Login':
        window.blit(title, (510, 40))
    elif page_type == 'Register':
        window.blit(title, (450, 40))
    else:
        window.blit(title, (320, 10))

    window.blit(first_field_surf, (380, 220))
    window.blit(second_field_surf, (380, 360))

    first_rect = pygame.Rect((380, 280, 420, 60))
    second_rect = pygame.Rect((380, 420, 420, 60))

    button_rect = draw_button(mouse, button_type, button_dimensions)

    if event.type == pygame.MOUSEBUTTONDOWN:

        if first_rect.collidepoint(mouse):
            first_active = True
            second_active = False

        elif second_rect.collidepoint(mouse):
            second_active = True
            first_active = False

        elif button_rect.collidepoint(mouse):
            if page_type == 'Challenge a Friend':
                mode = MODES['home']
            else:
                mode = MODES['start']

    pygame.draw.rect(
        window, BUTTON_COLOUR if first_active else HOVER_COLOUR, first_rect, 3
    )
    pygame.draw.rect(
            window, BUTTON_COLOUR if second_active else HOVER_COLOUR, second_rect, 3
        )

    first_input_surf = input_font.render(
        fit_tail(first_field, input_font, 400), False, 'White')
    second_input_surf = input_font.render(
        fit_tail(second_field, input_font, 400), False, 'White')

    window.blit(first_input_surf, 
                (first_rect.x + 10, first_rect.centery - first_input_surf.get_height() // 2)
    )
    window.blit(second_input_surf, 
                (second_rect.x + 10, second_rect.centery - second_input_surf.get_height() // 2)
    )

    draw_wrapped_text(status_message, bulgarian_font, 'White', (380, 150, 780, 60))

    return (mode, first_active, second_active)


def draw_home_page(mode, event, mouse, is_signed_out):
    title = title_font.render('Welcome to DDZ!', False, 'White')

    game_surf = smaller_title.render('NEW GAME', False, 'White')
    leaderboard_surf = smaller_title.render('LEADERBOARD', False, 'White')
    friends_surf = smaller_title.render('MY FRIENDS', False, 'White')
    send_challenge_surf = smaller_title.render('CHALLENGE A FRIEND', False, 'White')
    logout_surf = subtitle_font.render('Sign Out', False, 'White')

    window.fill(WINDOW_COLOUR)

    window.blit(zombie_hand_img, (60, 120))
    window.blit(title, (550, 40))

    game_rect = draw_button(mouse, game_surf, (550, 180, 260, 55))
    leaderboard_rect = draw_button(mouse, leaderboard_surf, (550, 250, 260, 55))
    friends_rect = draw_button(mouse, friends_surf, (550, 320, 260, 55))
    challenge_rect = draw_button(mouse, send_challenge_surf, (550, 390, 380, 55))
    logout_rect = draw_button(mouse, logout_surf, (980, 520, 200, 60))

    if event.type == pygame.MOUSEBUTTONDOWN:

        if game_rect.collidepoint(mouse):
            mode = MODES['game_modes']

        elif leaderboard_rect.collidepoint(mouse):
            mode = MODES['leaderboard']

        elif friends_rect.collidepoint(mouse):
            mode = MODES['friends']

        elif challenge_rect.collidepoint(mouse):
            mode = MODES['send_challenge']

        elif logout_rect.collidepoint(mouse):
            mode = MODES['start']
            is_signed_out = True

    return (mode, is_signed_out)


HINT_RECT = pygame.Rect(230, 520, 720, 60)

def draw_challenge_page(mode, event, mouse, friend, word, hint,
                        status_message, friend_active, word_active,
                        hint_active):
    mode, friend_active, word_active = draw_form_page(
        'Challenge a Friend', mode, event, mouse, friend, word,
        status_message, friend_active, word_active,
        input_font=bulgarian_font
    )
 
    window.blit(smaller_title.render('Hint', False, 'White'), (110, 518))
 
    if event.type == pygame.MOUSEBUTTONDOWN:
        if HINT_RECT.collidepoint(mouse):
            hint_active, friend_active, word_active = True, False, False
        else:
            hint_active = False
 
    pygame.draw.rect(
        window, BUTTON_COLOUR if hint_active else HOVER_COLOUR, HINT_RECT, 3
    )
 
    hint_surf = bulgarian_font.render(
        fit_tail(hint, bulgarian_font, HINT_RECT.w - 20), False, 'White'
    )
    window.blit(hint_surf,
                (HINT_RECT.x + 10, HINT_RECT.centery - hint_surf.get_height() // 2)
    )
 
    return mode, friend_active, word_active, hint_active


def draw_leaderboard(mode, event, mouse, leaderboard_list):
    """leaderboard_list: list of {'username': str, 'points': int}."""

    title = title_font.render('Leaderboard', False, 'White')
 
    window.fill(WINDOW_COLOUR)
    window.blit(title, (420, 10))
 
    home_rect = draw_button(mouse, home_button, (1020, 45, 135, 60))
 
    if event.type == pygame.MOUSEBUTTONDOWN:
        if home_rect.collidepoint(mouse):
            mode = MODES['home']
 
    padding = 0
 
    for entry in leaderboard_list:
        user_surf = smaller_title.render(
            entry['username'][:LEADERBOARD_NAME_MAX], False, 'White'
        )
        points_surf = smaller_title.render(str(entry['points']), False, 'White')
 
        window.blit(user_surf, (350, 220 + padding))
        window.blit(points_surf, (850, 220 + padding))
 
        padding += 50
 
    return mode


ADD_RECT = pygame.Rect(760, 270, 380, 50)

def draw_friends_list(mode, event, mouse, friends_list,
                      add_name, add_active, status_message):
    """friends_list: list of {'username': str, 'points': int}."""

    title = title_font.render('My Friends', False, 'White')
 
    window.fill(WINDOW_COLOUR)
    window.blit(title, (420, 10))
 
    home_rect = draw_button(mouse, home_button, (1020, 45, 135, 60))
 
    if event.type == pygame.MOUSEBUTTONDOWN:
        if home_rect.collidepoint(mouse):
            mode = MODES['home']
        elif ADD_RECT.collidepoint(mouse):
            add_active = True
        else:
            add_active = False
 
    for i, entry in enumerate(friends_list[:FRIENDS_VISIBLE]):
        user_surf = smaller_title.render(
            entry['username'][:LEADERBOARD_NAME_MAX], False, 'White'
        )
        window.blit(user_surf, (350, 220 + i * 50))
 
    extra = len(friends_list) - FRIENDS_VISIBLE
    if extra > 0:
        more_surf = smaller_title.render(f'+{extra} more', False, 'White')
        window.blit(more_surf, (350, 220 + FRIENDS_VISIBLE * 50))

    window.blit(smaller_title.render('Add friend', False, 'White'), (760, 215))
    pygame.draw.rect(window, 
                     BUTTON_COLOUR if add_active else HOVER_COLOUR, ADD_RECT, 3
    )
    name_surf = bulgarian_font.render(
        fit_tail(add_name, bulgarian_font, ADD_RECT.w - 20), False, 'White'
    )
    window.blit(name_surf,
                (ADD_RECT.x + 10, ADD_RECT.centery - name_surf.get_height() // 2)
    )
    draw_wrapped_text(status_message, bulgarian_font, 'White', (760, 335, 400, 80))
 
    return (mode, add_active)


def draw_game_page(mode, event, mouse):
    title = title_font.render('Game Modes', False, 'White')

    zen_surf = smaller_title.render('ZEN', False, 'White')
    compete_surf = smaller_title.render('COMPETITION', False, 'White')
    challenge_surf = smaller_title.render('CHALLENGE', False, 'White')

    window.fill(WINDOW_COLOUR)

    window.blit(peashooter_img, (55, 150))
    window.blit(title, (550, 40))

    zen_rect = draw_button(mouse, zen_surf, (550, 180, 130, 55))
    compete_rect = draw_button(mouse, compete_surf, (550, 250, 260, 55))
    challenge_rect = draw_button(mouse, challenge_surf, (550, 320, 260, 55))
    home_rect = draw_button(mouse, home_button, (1020, 45, 135, 60))

    if event.type == pygame.MOUSEBUTTONDOWN:

        if zen_rect.collidepoint(mouse):
            return 'Zen'

        if compete_rect.collidepoint(mouse):
            return 'Competition'

        if challenge_rect.collidepoint(mouse):
            return 'Challenge'

        if home_rect.collidepoint(mouse):
            mode = MODES['home']

    return mode

def draw_loading(message):
    window.fill(WINDOW_COLOUR)
    surf = basic_font.render(message, False, 'White')
    window.blit(surf, surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))
    pygame.display.update()

def draw_play(mode, event, mouse, game):
    name = ''
    hint_clicked = False

    if game == NO_CHALLENGES_MSG:
        name = 'Challenge'

    elif isinstance(game, GameState):
        name = game.mode

    title = title_font.render(name, False, 'White')
    window.fill(WINDOW_COLOUR)

    if name == 'Zen':
        window.blit(title, (540, 10))
    else:
        window.blit(title, (420, 10))

    home_rect = draw_button(mouse, home_button, (1020, 45, 135, 60))
    back_rect = draw_button(mouse, back_button, (50, 45, 140, 60))

    if event.type == pygame.MOUSEBUTTONDOWN:
        if home_rect.collidepoint(mouse):
            mode = MODES['home']
        elif back_rect.collidepoint(mouse):
            mode = MODES['game_modes']

    if game == NO_CHALLENGES_MSG:
        msg = basic_font.render(NO_CHALLENGES_MSG, False, 'White')
        window.blit(msg, (400, 280))

    elif isinstance(game, GameState):
        mystery_word = guessing_word_font.render(
            ' '.join(game.mystery_word), False,'White'
        )
        used_surf = basic_font.render('Used Letters:', False, 'White')
        tries_left = basic_font.render(
            f'Tries left: {game.guesses_left}', False,'White'
        )
        hint_surf = subtitle_font.render('HINT', False, 'White')

        window.blit(used_surf, (760, 180))
        window.blit(tries_left, (180, 180))
        window.blit(mystery_word, (180, 420))

        if game.mode != 'Zen':
            points_surf = basic_font.render(f'Points: {game.points}', False, 'White')
            window.blit(points_surf, (60, 120))

        if game.hint_used:
            draw_wrapped_text(
                game.definition, bulgarian_font, 'White', (30, 500, 1100, 90)
            )
        elif not game.is_over: # hidden when the game ends
            hint_rect = draw_button(mouse, hint_surf, (160, 500, 140, 60))
            if event.type == pygame.MOUSEBUTTONDOWN and hint_rect.collidepoint(mouse):
                hint_clicked = True

        padding = 0

        for used_letter in game.used_letters:
            letter_surf = subtitle_font.render(used_letter, False, 'White')
            window.blit(letter_surf, (685 + padding, 225))
            padding += 35

        if game.word_guessed:
            if game.mode == 'Zen':
                win_message = 'Yay! You guessed the\nmystery word!'
            else:
                win_message = f'Yay! You earned {game.points_earned} points!'

            draw_multiline_text(win_message, smaller_title, 'White', 660, 330)

        elif game.is_over:
            draw_multiline_text(
                f'You failed to guess\n{game.word} :(', smaller_title, 'White', 660, 330
            )

    return (mode, hint_clicked)