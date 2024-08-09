import random
import sys
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()
pygame.mixer.init()

pygame.display.set_caption("BELT MASTER")

WIDTH, HEIGHT = 1200, 700
FPS = 60

window = pygame.display.set_mode((WIDTH, HEIGHT))

#flip sprite depending on direction
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

#load sprite sheet
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join('assets', dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))] #load every file inside of directory

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha() #convert alpha loads transparent background

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            #draw frame from sprite sheet
            surface.blit(sprite_sheet, (0, 0), rect)
            #make sprite bigger
            surface = pygame.transform.scale(surface, (width * 4, height * 4))
            sprites.append(surface)

        #flip sprite depending on direction
        if direction:
            all_sprites[image.replace('.png', '') + '_right'] = sprites
            all_sprites[image.replace('.png', '') + '_left'] = flip(sprites)
        else:
            all_sprites[image.replace('.png', '')] = sprites

    return all_sprites

def get_block(size, door_num = None):
    if door_num is not None:
        path = join('assets', 'Doors', f'door{door_num}.png')
    else:
        path = join('assets', 'Terrain', 'floor.png')
    image = pygame.image.load(path).convert_alpha()
    image = pygame.transform.scale(image, (size, size))  #scale image to 96x96
    #create image
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, size, size) #might need to be 96 (x pos, y pos)
    #display image
    surface.blit(image, (0, 0), rect)
    if door_num is not None:
        return surface
    else:
        return pygame.transform.scale2x(surface) #scaling makes it larger

def get_box(size, sprite_file):
    path = join('assets', 'Boxes', sprite_file)
    image = pygame.image.load(path).convert_alpha()
    #create image
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, size, size) #might need to be 96 (x pos, y pos)
    #display image
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale(image, (size, size)) #scaling makes it larger

#player class
class Player(pygame.sprite.Sprite):
    GRAVITY = 1
    SPRITES = load_sprite_sheets('MainCharacters', 'man', 32, 32, True) #true for multidirectional
    ANIMATION_DELAY = 4 #make lower if velocity is increased (running)

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = 'right' #change that to right
        self.animation_count = 0
        self.fall_count = 0
        self.x_pos = 0
        self.carrying_box = False
        self.carrying_box_number = None
    
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != 'left': 
            self.direction = 'left'
            self.animation_count = 0
    
    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != 'right': 
            self.direction = 'right'
            self.animation_count = 0

    #update animation and move character in each frame
    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY) #gravity
        self.move(self.x_vel, self.y_vel)

        self.fall_count +=1 
        #update sprite every frame
        self.update_sprite()

    #determine if player has landed
    def landed(self):
        self.fall_count = 0 #stop adding gravity
        self.y_vel = 0

    #update sprite
    def update_sprite(self):
        if self.carrying_box:
            if self.x_vel != 0:
                sprite_sheet = 'carry'
            else:
                sprite_sheet = 'idle_carry'
        elif self.x_vel != 0 and not self.carrying_box:
            sprite_sheet = 'move'
        else:
            sprite_sheet = 'idle' #default sprite

        sprite_sheet_name = sprite_sheet + '_' + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        #show different frames for animation
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index] #frames
        self.animation_count += 1
        #check collision
        self.update()

    #update rectangle around sprite based on sprite frame
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite) #mapping sprite pixels

    #draw player
    def draw(self, win, offset_x):
        self.x_pos = self.rect.x - offset_x
        win.blit(self.sprite, (self.x_pos, self.rect.y))

    #maintain position
    def clamp_position(self, window_width, window_height):
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > window_width + 250:
            self.rect.right = window_width + 250
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > window_height:
            self.rect.bottom = window_height

#object class
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name = None):
        super().__init__() #initialize super class
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
    
    #draw object
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

#block class inheriting from object
class Block(Object):
    def __init__(self, x, y, size, door_num=None):
        super().__init__(x, y, size, size)
        block = get_block(size, door_num)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image)
        self.door_num = door_num

#box class inheriting from objects
class Box(Object):
    def __init__(self, x, y, size, sprite_file, number=None):
        super().__init__(x, y, size, size)
        self.number = number
        block = get_box(size, sprite_file)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image)
        self.carrying = False

def check_player_on_door(player, floor):
    for block in floor:
        if block.door_num is not None:
            door_rect = door_rect = pygame.Rect(block.rect.x - 10, block.rect.y - 10, block.rect.width + 20, block.rect.height + 20) #allow some leway
            if player.rect.colliderect(door_rect):
                return block.door_num
    return None

#draw background and player
def draw(window, background, player, objects, offset_x, score, font):
     #draw background
     window.blit(background, (0,0))
     #draw objects
     for obj in objects:
         obj.draw(window, offset_x)
     #draw player
     player.draw(window, offset_x)

     score_text = font.render(f"Score: {score}", True, (255, 255, 255))
     window.blit(score_text, (40, 20))  #position the text at (10, 10)

     #update window
     pygame.display.update()

#determine if player is colliding with object
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
                if dy > 0:
                    player.rect.bottom = obj.rect.top
                    player.landed()
                elif dy < 0:
                    player.rect.top = obj.rect.bottom
        collided_objects.append(obj)

    return collided_objects

#pick up boxes
def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.update()
    return collided_object

def handle_move(player, objects, PLAYER_VEL, window_width, window_height):
    #check for keys being pressed
    keys = pygame.key.get_pressed()
    #set velovity to 0
    player.x_vel = 0
    #pick up object
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)
    #don't move if both directions are pressed
    if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and not collide_left:
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            player.ANIMATION_DELAY = 2
            PLAYER_VEL = 7
        else:
            player.ANIMATION_DELAY = 4
            PLAYER_VEL = 5
        player.move_left(PLAYER_VEL)
    elif (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and not collide_right:
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            player.ANIMATION_DELAY = 2
            PLAYER_VEL = 7
        else:
            player.ANIMATION_DELAY = 4
            PLAYER_VEL = 5
        player.move_right(PLAYER_VEL)

    handle_vertical_collision(player, objects, player.y_vel)
    #make sure player is within screen bounds
    player.clamp_position(window_width, window_height)

def determine_box_size():
    size = random.randint(110, 190)
    height = 190 - size
    height = 360 + height

    return size, height

def determine_box_pos(size):
    size = 190 - size
    right = 25 + (size * 0.1)
    left = 85 + - (size * 0.7)

    return right, left


def extract_number_from_filename(filename):
    #extracts the number from a filename like 'box2.png'
    if filename.startswith('box') and filename.endswith('.png'):
        try:
            number = int(filename[3:filename.index('.png')])
            return number
        except ValueError:
            return None
    return None

def show_title_screen(window, floor):
    title_image1 = pygame.image.load('assets/Background/title1.png').convert()
    title_image1 = pygame.transform.scale(title_image1, (WIDTH, HEIGHT))
    title_image2 = pygame.image.load('assets/Background/title2.png').convert()
    title_image2 = pygame.transform.scale(title_image2, (WIDTH, HEIGHT))

    clock = pygame.time.Clock()
    image_switch_time = 500 #0.5 seconds
    last_switch = pygame.time.get_ticks()
    current_image = title_image1
    
    waiting = True
    while waiting:
        current_time = pygame.time.get_ticks()
        if current_time - last_switch >= image_switch_time:
            current_image = title_image2 if current_image == title_image1 else title_image1
            last_switch = current_time
        
        window.blit(current_image, (0, 0))
        
        #draw the floor
        for block in floor:
            block.draw(window, 0)  #assuming offset_x is 0 for the title screen
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
        
        clock.tick(60)  #limit to 60 FPS
    
def show_game_over_screen(window, floor, score, high_score, font, offset_x):
    pygame.mixer.music.stop() #stop music
    game_over = pygame.mixer.Sound('assets/Sounds/game_over.wav')
    game_over.play()
    gameover = pygame.image.load('assets/Background/gameover.png').convert()
    gameover = pygame.transform.scale(gameover, (WIDTH, HEIGHT))
    waiting = True

    last_toggle_time = pygame.time.get_ticks()
    show_score = True  #toggle the display of the score text
    
    while waiting:
        window.blit(gameover, (0, 0))
        
        #draw the floor
        for block in floor:
            block.draw(window, offset_x)  #assuming offset_x is 0 for the title screen
        
        #check if 0.5 seconds have passed
        current_time = pygame.time.get_ticks()
        if current_time - last_toggle_time > 500:  #500 milliseconds = 0.5 seconds
            show_score = not show_score  #toggle display state
            last_toggle_time = current_time

        #display score text based on toggle state
        if show_score:
            score_text = font.render(f"Score: {score}", True, (255, 255, 255))
            window.blit(score_text, (40, 20))


        #show high score
        high_score_text = font.render(f"High Score: {high_score}", True, (255, 255, 255))
        window.blit(high_score_text, (40, 20 + score_text.get_height() + 10))

        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN: #press any key
                    waiting = False
                    game_over.stop()

def gameplay(window, floor, block_size, door_num):
    clock = pygame.time.Clock()
    PLAYER_VEL = 5 #player speed
    background = pygame.image.load('assets/Background/hub.png')
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))

    #player score
    score = 0
    increment = 50
    box_size = 0 
    box_height = 0 
    box_number=0

    #sounds
    scan = pygame.mixer.Sound('assets/Sounds/point.mp3')
    error = pygame.mixer.Sound('assets/Sounds/error.mp3')
    alarm = pygame.mixer.Sound('assets/Sounds/alarm.mp3')


    box_spawn_interval = 2500  #2500 milliseconds = 2.5 seconds
    last_box_spawn_time = pygame.time.get_ticks()  #start timer
    boxes = []

    #list of box sprites
    box_sprites = ['box1.png', 'box2.png', 'box3.png', 'box4.png', 'box5.png']

    #create player
    player = Player(100, HEIGHT-223, 50, 50)

    #sidescrolling background
    offset_x = 0
    scroll_area_width = 200
    #scrolling boundaries
    scroll_min = 0
    scroll_max = max(0, len(floor) * block_size - WIDTH)

    #play title_screen music
    pygame.mixer.music.load('assets/Music/title_screen.mp3')
    pygame.mixer.music.play(-1) #loop indefinitely
    pygame.mixer.music.set_volume(0.3)

    #play music
    pygame.mixer.music.stop() #stops music
    pygame.mixer.music.load('assets/Music/music.mp3')
    pygame.mixer.music.play(-1) #loop indefinitely
    pygame.mixer.music.set_volume(0.4)
    alarm.play(loops=1)
    alarm.set_volume(0.4)


    game_over = False
    while not game_over:
        clock.tick(FPS)
        
        current_time = pygame.time.get_ticks()

        font = pygame.font.Font('assets/Font/Grand9K Pixel.ttf', 50) 


        #check score
        if 750 > score > 350:
            increment = 100
            box_spawn_interval = 2000
        elif 1250 > score > 750:
            box_spawn_interval = 1700
            PLAYER_VEL = 6.5
        elif score > 2000:
            increment = 150
            box_spawn_interval = 1300
            PLAYER_VEL = 8

        
        #check for window closing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
                return score, font, True, offset_x

            #check for left click to pick up/set down box
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  #left click
                    if player.carrying_box:  #let go of box
                        for box in boxes:
                            if box.carrying:
                                box.carrying = False
                                player.carrying_box = False
                                player.carrying_box_number = None
                                break
                    else: #pick up box
                        for box in boxes:
                            if box.rect.colliderect(player.rect):
                                size = box_size
                                box.carrying = True
                                player.carrying_box = True
                                player.carrying_box_number = box.number
                                break

        #moves player
        player.loop(FPS)

        #check for point
        if pygame.mouse.get_pressed()[2]: #right click
            if player.carrying_box:
                door_num = check_player_on_door(player, floor)
                if door_num == player.carrying_box_number:
                    for box in boxes:
                        if box.carrying:
                            scan.play()
                            scan.set_volume(0.3)
                            score += increment
                            box.rect.x = -box.width
                            box.rect.y = -box.height
                            box.carrying = False
                            player.carrying_box = False
                            player.carrying_box_number = None
                            box.rect.y = HEIGHT
                            boxes.remove(box)
                            break


        #create new box if needed
        if current_time - last_box_spawn_time > box_spawn_interval:
            #randomly choose box sprites
            sprite_file = random.choice(box_sprites)
            #get box number
            box_number = extract_number_from_filename(sprite_file)
            #choose scale for sprite
            box_size, box_height = determine_box_size()
            new_box = Box(0, box_height, box_size, sprite_file, number = box_number)  
            new_box.image = get_box(box_size, sprite_file)
            boxes.append(new_box)
            last_box_spawn_time = current_time
        
        #update box positions
        for box in boxes:
            if box.carrying:
                right, left = determine_box_pos(size)
                if player.direction == 'right':
                    box.rect.x = player.rect.x + right
                else:
                    box.rect.x = player.rect.x - left
            else:
                box.rect.x += 3

            if box.rect.x >= 1400: #end if box reaches past edge of the screen
                game_over = True
                return score, font, False, offset_x

    
        
        #check for input movement
        handle_move(player, floor, PLAYER_VEL, WIDTH, HEIGHT)
        
        #display background, player, and objects
        draw(window, background, player, [*floor, *boxes], offset_x, score, font)
        
        #check for scrolling background boundaries
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
            (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel
            #ensure offset_x stays within boundaries
            offset_x = max(scroll_min, min(scroll_max, offset_x))

    pygame.quit()
    sys.exit()

def main(window):
    block_size = 96
    door_num = 0
    score = 0
    end = False
    high_score = 0

    #create floor
    floor = []
    for i in range(15):
        if i % 3 == 2:
            if door_num < 5:
                door_num +=1
            block = get_block(block_size, door_num)
        else:
            block = get_block(block_size)
        floor.append(Block(i * block_size, HEIGHT - block_size, block_size, door_num if i % 3 == 2 else None))

    while not end:
        #play title_screen music
        pygame.mixer.music.load('assets/Music/title_screen.mp3')
        pygame.mixer.music.play(-1) #loop indefinitely
        pygame.mixer.music.set_volume(0.3)
        #show title_screen
        show_title_screen(window, floor)
        #gameplay loop
        score, font, end, offset_x = gameplay(window, floor, block_size, door_num)
        if end:
            break
        #game over screen
        if score > high_score:
            high_score = score
        show_game_over_screen(window, floor, score, high_score, font, offset_x)
        score = 0


    pygame.quit()
    sys.exit()

import warnings

if __name__ == '__main__':
    main(window)
