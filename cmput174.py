# The following program is a game called memory. The player's goal is to flip
# and match each card one by one. When the player picks two cards that do not
# match, they are shown briefly before being flipped back again. The player
# wins when they have successfully matched all card pairs.

# Import modules
import pygame, random, time


# User-defined functions

def main():
    # initialize all pygame modules (some need initialization)
    pygame.init()
    # create a pygame display window
    pygame.display.set_mode((500, 400))
    # set the title of the display window
    pygame.display.set_caption('Tic Tac Toe')
    # get the display surface
    w_surface = pygame.display.get_surface()
    # create a game object
    game = Game(w_surface)
    # start the main game loop by calling the play method on the game object
    game.play()
    # quit pygame and clean up the pygame window
    pygame.quit()


# User-defined classes

class Game:
    # An object in this class represents a complete game.

    def __init__(self, surface):
        # Initialize a Game.
        # - self is the Game to initialize
        # - surface is the display window surface object

        # === objects that are part of every game that we will discuss
        self.surface = surface
        self.bg_color = pygame.Color('black')

        self.FPS = 60
        self.game_Clock = pygame.time.Clock()
        self.close_clicked = False
        self.continue_game = True

        # === game specific objects
        self.image_list = []
        self.create_image_list()
        self.board_size = 4
        self.board = []
        self.create_board()
        self.score = 0
        self.score_offset = 30
        # ----
        self.tile1 = 0
        self.tile2 = 0
        self.tracked_tile = self.tile1
        self.pause = False

    def create_image_list(self):
        # Open and create a duplicated list of images. Appends each tile to an image
        for i in range(1, 9):
            image = pygame.image.load("image" + str(i) + ".bmp")
            self.image_list.append(image)
        self.image_list += self.image_list
        random.shuffle(self.image_list)

    def create_board(self):
        # Creates a list of Tile objects
        Tile.set_surface(self.surface)
        width = self.image_list[0].get_width()
        height = self.image_list[0].get_height()
        for row_index in range(0, self.board_size):
            row = []
            for col_index in range(0, self.board_size):
                x = col_index * width
                y = row_index * height
                tile = Tile(x, y, width, height, self.image_list[(row_index * 4) + col_index])
                row.append(tile)
            self.board.append(row)

    def play(self):
        # Play the game until the player presses the close box.
        # - self is the Game that should be continued or not.

        while not self.close_clicked:  # until player clicks close box
            # play frame
            self.handle_events()
            self.draw()
            if self.continue_game:
                self.update()
                self.decide_continue()
            self.game_Clock.tick(self.FPS)  # run at most with FPS Frames Per Second

    def handle_events(self):
        # Handle each user event by changing the game state appropriately.
        # - self is the Game whose events will be handled

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.close_clicked = True
            if event.type == pygame.MOUSEBUTTONUP:
                self.detect_mouseup(event)

    def detect_mouseup(self, event):
        # Detect if there is a mouseup event and where
        # - event is the MOUSEBUTTONUP event
        for row in self.board:
            for tile in row:
                if tile.clicked(event.pos):
                    tile.flip()
                    self.track_tile(tile)

    def track_tile(self, tile):
        # Keeps track of which tile has been clicked and assigns the tile as tile1
        # or tile2
        # - tile is the most recently clicked tile
        if self.tracked_tile == self.tile1:
            self.tile1 = tile
            self.tracked_tile = self.tile2
        else:
            self.tile2 = tile
            self.tracked_tile = self.tile1
            if not self.tile1.compare_tiles(self.tile2) or self.tile1 is self.tile2:
                self.pause = True
                self.draw()
                self.tile1.hide_image(self.tile2)

    def draw(self):
        # Draw all game objects.
        # - self is the Game to draw

        self.surface.fill(self.bg_color)  # clear the display surface first
        for row in self.board:
            for tile in row:
                tile.draw()
        self.draw_score()
        pygame.display.update()  # make the updated surface appear on the display
        if self.pause:
            time.sleep(1)
            self.pause = False

    def update(self):
        # Update the game objects for the next frame.
        # - self is the Game to update
        self.score = pygame.time.get_ticks() // 1000

    def draw_score(self):
        # Calculate and display the current score
        if self.score > 9:
            self.score_offset = 55
        score_font = pygame.font.SysFont('', 70)
        score_image = score_font.render(str(self.score), True, pygame.Color('white'))
        self.surface.blit(score_image, (self.surface.get_width() - self.score_offset, 0))

    def decide_continue(self):
        # Check and remember if the game should continue
        # - self is the Game to check
        x = 16
        for row in self.board:
            for tile in row:
                if not tile.is_win():
                    x -= 1
                    if x == 0:
                        self.continue_game = False


class Tile:
    # An object in this class represents a Tile in TTT

    border_width = 5
    fg_color = pygame.Color('black')
    surface = None
    hidden_tile = pygame.image.load('image0.bmp')

    @classmethod
    def set_surface(cls, surface):
        cls.surface = surface

    def __init__(self, x, y, width, height, image):
        # Initializes a Tile.
        # - self is the Dot to initialize

        self.rect = pygame.Rect(x, y, width, height)
        self.image = image
        self.display = Tile.hidden_tile
        self.hidden = True

    def draw(self):
        # Draws each tile object as well as blitting images onto the same surface
        if not self.hidden:
            self.display = self.image
        else:
            self.display = Tile.hidden_tile
        pygame.draw.rect(Tile.surface, Tile.fg_color, self.rect, Tile.border_width)
        Tile.surface.blit(self.display, (self.rect.left, self.rect.top))

    def clicked(self, position):
        # Returns a boolean indicating a click within the tile
        # - position is the coordinate of the MOUSEUP event
        if self.hidden:
            return self.rect.collidepoint(position)
        else:
            return False

    def hide_image(self, tile):
        # Sets attributes that tell the respective tiles to flip back over
        self.hidden = True
        tile.hidden = True

    def flip(self):
        # Sets attribute that tells respective tile to reveal itself
        self.hidden = False

    def compare_tiles(self, tile2):
        # Returns if the images of two tiles are the same
        # - tile2 is the second tile being compared with the first tile
        return self.image == tile2.image

    def is_win(self):
        # Returns an attribute indicating whether the tile is in a hidden state
        return self.hidden


main()

