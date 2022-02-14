import pygame
from pygame.locals import *
from pygame import mixer, image  # pygame.mixer() is used for music.
import pickle
from os import path
from pathlib import Path  # To make the paths work on any platform, by extracting the path as a path, instead of a string.

images_folder = Path("images")
sounds_folder = Path("sounds")
levels_folder = Path("levels") 
sprites_folder = Path("sprites")
fonts_folder = Path("fonts")


pygame.mixer.pre_init(44100, -16, 10, 256)  # (frequency, size, channel, buffer)
mixer.init()
pygame.init()

pygame.mixer.set_num_channels(10)

clock = pygame.time.Clock()
fps = 60

# Setting the height and width of the game screen (in units of pixels).
screen_width = 1500
screen_height = 900

# "screen" is the name of the variable which will be used to refer to the game's output.
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Python Platformer Game")

tile_size = 50
game_over = 0
main_menu = True
level = 2
max_levels = 2
score = 0

# Accessing an image file from the system to be used as the background, and resizing it to fit the screen
# background_image_1 = pygame.image.load(images_folder / r"Background 1.png")
'''background_image_1 = pygame.image.load(images_folder / r"Background 1.png")
scaled_background_image_1 = pygame.transform.smoothscale(background_image_1, (1500, 900))'''

background_image_list = []
for i in range(1,4):
    background_image_temp = f"Background {i}(jpg).jpg"
    background_image_list.append(background_image_temp)

menu_image = pygame.image.load(images_folder / r"menu.jpg")
scaled_menu_image = pygame.transform.scale(menu_image, (1500, 900))

restart_button_image = pygame.image.load(images_folder / r"restart button.png")
scaled_restart_button_image = pygame.transform.scale(restart_button_image, (300, 150))
start_button_image = pygame.image.load(images_folder / r"start button.png")
scaled_start_button_image = pygame.transform.scale(start_button_image, (350, 150))

exit_button_image = pygame.image.load(images_folder / r"exit button.png")
scaled_exit_button_image = pygame.transform.scale(exit_button_image, (350, 150))

logo_image = pygame.image.load(images_folder / r"logo.png")
scaled_logo_image = pygame.transform.scale(logo_image, (1000, 600))
 
# Sounds
pygame.mixer.music.load(sounds_folder / r"background music.wav")
pygame.mixer.music.set_volume(0.15)
pygame.mixer.music.play(loops = -1, start = 0.0, fade_ms = 5000)

run_fx = pygame.mixer.Sound(sounds_folder / r"run sound.wav")
run_fx.set_volume(0.2)
coin_fx = pygame.mixer.Sound(sounds_folder / r"coin sound.wav")
coin_fx.set_volume(0.7)  # Changes the volume of the sound 
jump_fx = pygame.mixer.Sound(sounds_folder / r"jump sound.wav")
jump_fx.set_volume(1.5)
game_over_fx = pygame.mixer.Sound(sounds_folder / r"retro game over.wav")
game_over_fx.set_volume(0.3)


def draw_text(text, font, text_colour, x, y):  # Function to draw text onto screen to display score, etc.
    img = font.render(text, True, text_colour)
    screen.blit(img, (x, y))

 
def reset_level(level):  # Function to reset level
    player.reset(100, screen_height - 130)
    
    ice_snake_group.empty() 
    ice_spirit_group.empty()
    fire_monster_group.empty()
    fire_spirit_group.empty()
    lava_group.empty()
    exit_group.empty()
    platform_group.empty()
    
    if path.exists(levels_folder / fr"level{level}_data") == True:
        pickle_in = open(levels_folder / fr"level{level}_data", "rb")
        world_data = pickle.load(pickle_in)
    world = World(world_data)
    
    return world
    

class Button():

    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):  # Draw function
        action = False  # This variable tells whether the button was clicked at any point
        
        mouse_pos = pygame.mouse.get_pos()  # Getting mouse position
        
        # Checking if mouse is over the button
        if self.rect.collidepoint(mouse_pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:  # Checking if button has been clicked
            # The index [0] indicates that a left click was done, [1] indicates that a middle click was done, etc.
                action = True
                self.clicked = True
            
            if pygame.mouse.get_pressed()[0] == 0:
                self.clicked = False  
    
        screen.blit(self.image, self.rect)  # Draw button
        
        return action

# Defining a class which allows the user to control the player 
class Player():

    def __init__(self , x, y):
        self.reset(x, y)  
        
    # Movement of the player 
    def update(self, game_over):
        Dx = 0  # change in x and y 
        Dy = 0
        walk_cooldown = 4.5
        collision_threshold = 30
        
        if game_over == 0:
            
            # Getting input from keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.did_jump == False and self.in_air == False: 
                # To prevent the player from being able to jump while already in the air
                self.y_velocity = -15  # Velocity obtained on jumping
                self.did_jump = True
                run_fx.stop()
                jump_fx.play()
                # To prevent being able to hold the spacebar indefinitely and keep on going upwards
            
            if key[pygame.K_SPACE] and self.did_jump == False and self.in_air == True and self.against_wall == True and \
            self.did_wall_jump == False:
                self.y_velocity = -15
                self.did_jump = True
                self.did_wall_jump = True
                run_fx.stop()
                jump_fx.play()
                
            if key[pygame.K_SPACE] == False:
                self.did_jump = False 
    
            if key[pygame.K_LEFT]:
                Dx -= 6
                self.counter += 1
                self.direction = -1
                
            if key[pygame.K_RIGHT]:
                Dx += 6
                self.counter += 1 
                self.direction = 1
                        
         
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.walking_towards_right_image_list[self.index] 
                if self.direction == -1:
                    self.image = self.walking_towards_left_image_list[self.index] 
                   
            ''' To make sure the player can't walk through walls, we shall implement this algorithm:
                1. Calculate future player position beforehand
                2. Check if collision will occur at this position
                3. Adjust/update player position'''
                
            # Handle animation   
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1 
                if self.index >= len(self.walking_towards_right_image_list):
                    self.index = 1
                if self.direction == 1:
                    self.image = self.walking_towards_right_image_list[self.index] 
                if self.direction == -1:
                    self.image = self.walking_towards_left_image_list[self.index] 
                
      
            # Add gravity
            self.y_velocity += 1
            if self.y_velocity >= 12:  # Terminal velocity
                self.y_velocity = 12   
            Dy += self.y_velocity    
            
            # Check for collision
            self.in_air = True
            self.against_wall = False
            
            for tile in world.tile_list:
                # Check for collision in x axis
                if tile[1].colliderect(self.rect.x + Dx, self.rect.y, self.width, self.height):
                    Dx = 0  # Since the character stops moving if he hits the side of a block
                    self.against_wall = True
    
                # Check for collision in y axis
                if tile[1].colliderect(self.rect.x, self.rect.y + Dy, self.width, self.height):
                    # Check if below the block i.e jumping and hitting head on a block
                    if self.y_velocity < 0:
                        Dy = tile[1].bottom - self.rect.top
                        self.y_velocity = 0  # Since the y velocity becomes zero if the character hits the bottom of a block 
                    # Check if above the block i.e falling
                    elif self.y_velocity >= 0:
                        Dy = tile[1].top - self.rect.bottom
                        self.y_velocity = 0
                        self.in_air = False  # If the player has collided with a block from above, they are not in the air.
                        self.did_wall_jump = False
                        
                # Check for collision with enemies
                if pygame.sprite.spritecollide(self, ice_snake_group or ice_spirit_group or fire_monster_group or fire_spirit_group, False):
                    game_over = -1  # if game_over == -1, the player dies
                    run_fx.stop()
                    game_over_fx.play()
                
                # Check for collision with lava
                if pygame.sprite.spritecollide(self, lava_group, False):
                    game_over = -1  
                    run_fx.stop()
                    game_over_fx.play()
                    
                # Check for collision with exit (the exit is a transparent block)         
                if pygame.sprite.spritecollide(self, exit_group, False):
                    game_over = 1  # game_over = 1: player has won.
                 
                # Checking for collision with moving platforms
                for platform in platform_group:
                    # x direction
                    if platform.rect.colliderect(self.rect.x + Dx, self.rect.y, self.width, self.height):
                        Dx = 0
                        
                    if platform.rect.colliderect(self.rect.x, self.rect.y + Dy, self.width, self.height): 
                        # Checking if collision happens from below platform
                        if abs(platform.rect.bottom - (self.rect.top + Dy)) < collision_threshold: 
                        # If the distance between the player's head and the bottom of any platform is less than collision threshold:
                        # (The collision threshold is smaller than the player's sprite)
                            self.y_velocity = 0
                            Dy = platform.rect.bottom - self.rect.top 
 
                        # Make the player's head's y coordinate equal the y coordinate of the bottom of the platform.   
                        # platform.rect.bottom - self.rect.top > 0, but since the Dy term may make it negative, we apply the abs().
                        
                        if abs((self.rect.bottom + Dy) - platform.rect.top) < collision_threshold:
                            # self.rect.bottom - platform.rect.top > 0, but the Dy term may make it negative. (Dy may be negative.)
                            self.rect.bottom = platform.rect.top - 1
                            
                            
                            ''' We subtract 1 from the self.rect.bottom (the y axis is inverted in python) so that the x direction collision
                             code does not think that the think that the player is constantly colliding with the platform and thus set Dx to zero.
                            (The x direction collision checker checks for collision with self.rect.x + Dx and self.rect.y) If this is not done, the 
                            player will not be able to move the character left or right when the platform moves upwards.''' 
                            
                            Dy = 0
                            self.in_air = False
                            self.did_jump = False
                            self.did_wall_jump = False
                            
                            ''' The bottom of the player's sprite is equated to the y coordinate of the top of the platform so that 
                            the player stays on the platform even if it moves up or down.'''
                            
                            # Making sure that the player moves along with sideways-moving platforms
                            if platform.move_x != 0:
                                self.rect.x += platform.move_direction
                
                       
                if Dx != 0 and Dy == 0:
                    run_fx.play()
                if Dx == 0:
                    run_fx.stop()
                
                                
            # Update player coordinates
            self.rect.x += Dx
            self.rect.y += Dy
            
            
            
        elif game_over == -1:
            draw_text("GAME OVER", pygame.font.Font(fonts_folder / r"super-legend-boy-font\SuperLegendBoy-4w8Y.ttf", 60), \
             (0, 0, 0), screen_width // 2 - 220, screen_height // 2 - 100)
            '''dead_images_list_right = []
            dead_images_list_left = []
            for i in range(7):
                dead_image_right = pygame.image.load(sprites_folder / fr"adventurer-die-{i}")
                dead_image_right = pygame.transform.scale(dead_image_right, (48,64))
                dead_image_left = pygame.transform.flip(dead_image_right, True, False)
                dead_images_list_right.append(dead_image_right)
                dead_images_list_left.append(dead_image_left)'''
                
            self.image = self.dead_image
            self.rect.y -= 5
            
        # Drawing the player onto the screen
        screen.blit(self.image , self.rect)
        # pygame.draw.rect(screen, (255,255,255), self.rect, 2)
        return game_over
    
    def reset(self, x, y): 
        ''' Putting all the initialization parameters in a new method instead of in __init__ allows us
        to call the reset method whenever we want to re-initialize the player position..'''
        self.walking_towards_right_image_list = []
        self.walking_towards_left_image_list = []
        self.index = 0
        self.counter = 0
        
        for num in range(1, 8): 
            image_right = pygame.image.load(sprites_folder / fr"Sprite_Moving_Right_{num}.png")
            image_right = pygame.transform.scale(image_right, (48, 64))
            image_left = pygame.transform.flip(image_right, True, False)
            self.walking_towards_right_image_list.append(image_right)
            self.walking_towards_left_image_list.append(image_left)
              
        dead_image = pygame.image.load(images_folder / r"Stone Brick.png")  
        self.dead_image = pygame.transform.scale(dead_image, (50, 50))
        self.image = self.walking_towards_right_image_list[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.y_velocity = 0
        self.did_jump = False
        self.direction = 0
        self.in_air = True  # This variable tells us whether the player is in the air or on a block.
        self.against_wall = False
        self.did_wall_jump = False
            
    
class World():

    def __init__(self, data):
        self.tile_list = []  # The list in which we will put info regarding the positions of each tile
        
        bricks_image = pygame.image.load(images_folder / r"Stone Brick.png")
        
        row_counter = 0
        for row in data:
            column_counter = 0
            for tile in row:
                if tile == 1:
                    image = pygame.transform.smoothscale(bricks_image, (50, 50))
                    image_rect = image.get_rect()
                    image_rect.x = column_counter * tile_size
                    image_rect.y = row_counter * tile_size
                    tile = (image , image_rect)
                    self.tile_list.append(tile)
               
                if tile == 2:
                    ice_snake = Enemy(column_counter * tile_size, row_counter * tile_size + 10, 1)
                    ice_snake_group.add(ice_snake)
                    
                if tile == 3:
                    lava = Lava(column_counter * tile_size, row_counter * tile_size + tile_size // 2)
                    lava_group.add(lava)
                    
                if tile == 4:
                    exit = Exit(column_counter * tile_size, row_counter * tile_size)
                    exit_group.add(exit)
                
                if tile == 5:
                    coin = Coin(column_counter * tile_size + (tile_size // 2), row_counter * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                
                if tile == 6:  # Horizontal moving platform
                    platform = Platform(column_counter * tile_size, row_counter * tile_size, 1, 0)
                    platform_group.add(platform)
                    
                if tile == 7:  # Vertical moving platform
                    platform = Platform(column_counter * tile_size, row_counter * tile_size, 0, 1)
                    platform_group.add(platform)
                    
                if tile == 8:
                    ice_spirit = Enemy(column_counter * tile_size, row_counter * tile_size + 10, 2)
                    ice_spirit_group.add(ice_spirit)
                    
                if tile == 9:
                    fire_monster = Enemy(column_counter * tile_size, row_counter * tile_size + 10, 3)
                    fire_monster_group.add(fire_monster)
                    
                if tile == 10:
                    fire_spirit = Enemy(column_counter * tile_size, row_counter * tile_size + 10, 4)
                    fire_spirit_group.add(fire_spirit)
                    
                column_counter += 1
            row_counter += 1        

    def draw(self):  # This function(method) takes the data from the tile list and draws it on the screen
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1]) 
            # pygame.draw.rect(screen, (255,255,255), tile[1], 2)
          

class Enemy(pygame.sprite.Sprite):

    def __init__(self, x, y, enemy_number):
        pygame.sprite.Sprite.__init__(self)
        global ice_snake_image, ice_spirit_image, fire_monster_image, fire_spirit_image             
        ice_snake_image = pygame.transform.scale(pygame.image.load(sprites_folder / r"Ice_Snake.png"), (40,40))
        ice_spirit_image = pygame.transform.scale(pygame.image.load(sprites_folder / r"Ice_Spirit.png"), (50,50))
        fire_monster_image = pygame.transform.scale(pygame.image.load(sprites_folder / r"Fire_Monster.png"), (80,40))
        fire_spirit_image = pygame.transform.scale(pygame.image.load(sprites_folder / r"Fire_Spirit.png"), (40,50))
        global enemy_list
        enemy_list = []  
        enemy_list.extend([ice_snake_image, ice_spirit_image, fire_monster_image, fire_spirit_image])
        
        self.image = enemy_list[enemy_number - 1]
        #self.image = pygame.transform.scale(ice_snake_image, (40, 40))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = -2
        self.move_counter = 0
        
    def update(self, enemy_number): 
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1
        if self.move_direction >= 0: # Since the original sprites face towards the left, but the positive direction is right.
            self.image = pygame.transform.flip(enemy_list[enemy_number -1], True, False)
        elif self.move_direction <= 0:
            self.image = enemy_list[enemy_number -1]


class Lava(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        lava_image = pygame.image.load(images_folder / r"lava.png")
        self.image = pygame.transform.scale(lava_image, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        
class Coin(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        coin_image = pygame.image.load(images_folder / r"coin.png")
        self.image = pygame.transform.scale(coin_image, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)  # The coins are placed in the center of the tile

        
class Exit(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        exit_image = pygame.image.load(images_folder / r"lava.png")
        self.image = pygame.transform.scale(exit_image, (48, 64))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y    


class Platform(pygame.sprite.Sprite):

    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        platform_image = pygame.image.load(images_folder / r"lava.png")
        self.image = pygame.transform.scale(platform_image, (tile_size, int(tile_size // 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y  
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y
        
    def update(self): 
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

# This list contains info on where to place what tile, which will be stored in a separate binary file.

'''world_data = [
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,2,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,1,3,3,3,3,3,3,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
[1,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1],
[1,0,0,0,1,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]'''

# Starting location of player
player = Player(100, screen_height - 130)

ice_snake_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
ice_spirit_group = pygame.sprite.Group()
fire_monster_group = pygame.sprite.Group()
fire_spirit_group = pygame.sprite.Group()

# Loading in level data and creating world
if path.exists(levels_folder / fr"level{level}_data") == True:
    pickle_in = open(levels_folder / fr"level{level}_data", "rb")
    world_data = pickle.load(pickle_in)
world = World(world_data)
    

# Creating buttons
restart_button = Button(screen_width // 2 - 125, screen_height // 2 - 50, scaled_restart_button_image)
start_button = Button(screen_width // 2 - 150, screen_height // 2 , scaled_start_button_image)
exit_button = Button(screen_width // 2 - 150, screen_height // 2 + 200, scaled_exit_button_image)
logo = Button(screen_width // 2 - 500, screen_height // 2 - 600, scaled_logo_image)

run = True
while run == True:
    
    clock.tick(fps)  # Set frame rate
    
    if main_menu == False:
        screen.blit(pygame.transform.scale(pygame.image.load(images_folder / background_image_list[level-1]), (1500,900)), (0, 0))
    else:
        screen.blit(scaled_menu_image, (0, 0))
    
    if main_menu == True:
        if exit_button.draw() == True:
            run = False
        if start_button.draw() == True:
            main_menu = False
        logo.draw()
        # screen.blit(scaled_menu_image,(0,0))
        
    else:
        world.draw ()
        
        if game_over == 0:
            ice_snake_group.update(1) 
            ice_spirit_group.update(2)
            fire_monster_group.update(3)
            fire_spirit_group.update(4)
            platform_group.update()
            # Update score, check if a coin has been collected.
            if pygame.sprite.spritecollide(player, coin_group, True):
                run_fx.stop()
                coin_fx.play()
                score += 100 
            # "True" in the spritecollide argument causes the coins to disappear when touched
            draw_text("Score: " + str(score), pygame.font.Font\
        (fonts_folder / r"super-legend-boy-font\SuperLegendBoy-4w8Y.ttf", 30), (255, 255, 255), tile_size - 10, 10)
            # draw_text( text, font, (font, size), position )    
            
        ice_snake_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)
        platform_group.draw(screen)
        ice_spirit_group.draw(screen)
        fire_monster_group.draw(screen)
        fire_spirit_group.draw(screen)
        
        game_over = player.update(game_over)
        
        if game_over == -1:
            
            if restart_button.draw() == True:
                world_data = [] 
                world = reset_level(level)  # Restart the level
                game_over = 0
                score = 0  # Score resets if player dies
        
        # If the player completes the level
        if game_over == 1:
            level += 1
            if level <= max_levels:
                # Reset the level, but with the "level" variable += 1 (i.e. Starting the next level from scratch.)
                world_data = [] 
                world = reset_level(level) 
                game_over = 0
            else:  # All levels completed i.e. The game is over.
                # Restart game
                draw_text("YOU WIN!", pygame.font.Font(fonts_folder / r"super-legend-boy-font\SuperLegendBoy-4w8Y.ttf", 60), \
                (0, 0, 0), (screen_width // 2) - 170, screen_height // 2 - 100)
                if restart_button.draw() == True:
                    level = 1  # Go back to first level.
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0  # If the game is completed, the score resets if the game is restarted.
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    
    pygame.display.update()
    
pygame.quit()
