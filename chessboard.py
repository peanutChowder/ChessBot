import pygame
from chessGame import Game
from chessGame import MoveSet


def main():
    pygame.init()
    surface = pygame.display.set_mode((1350, 800))
    pygame.display.set_caption("Chess")
    a = ChessWindow(surface)
    a.play()


def alternator(current, optionsList):
    """
    Alternates the value to its opposite. Meant to be used for items with two valid values.
    :param current: The item's current value
    :param optionsList: A list of the two valid values
    :return option: The alternate value of current
    """
    assert len(optionsList) == 2, "Alternator is meant to be used for items with two values"
    for option in optionsList:
        if current != option:
            return option


class ChessWindow:
    def __init__(self, surface):
        self.surface = surface
        self.close = False
        self.fps = 60
        self.clock = pygame.time.Clock()
        self.backgroundColor = pygame.Color("black")

        # Board specific attribute
        self.boardMargin = 0.15   # Percent height a single margin takes up
        self.chessBoard = None
        self.createBoard()

    def createBoard(self):
        """
        Initializes the board object. Does not include the margin areas.
        :return: None
        """
        boardTop = self.surface.get_height() * self.boardMargin
        boardBottom = self.surface.get_height() - (self.surface.get_height() * self.boardMargin)

        self.chessBoard = ChessBoard(self.surface, boardTop, boardBottom)

    def play(self):
        """
        Main loop. Runs infinitely until the user closes the window.
        :return: None
        """
        while not self.close:
            self.handleEvents()
            self.draw()

            self.clock.tick(self.fps)

    def handleEvents(self):
        """
        Handles all user-generated events, i.e. clicking.
        :return: None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close = True

            if event.type == pygame.MOUSEBUTTONUP:
                self.chessBoard.checkBoardClick(pygame.mouse.get_pos())

                # deleteme
                print("click: ", pygame.mouse.get_pos())

    def draw(self):
        """
        Main drawing method, calls other objects' drawing methods to generate a visual representation.
        :return: None
        """
        self.surface.fill(self.backgroundColor)
        self.chessBoard.draw()
        pygame.display.update()


class PromotionDisplay:
    """
    An object representing the temporary display that appears when a pawn reaches its opposite side. The presence of
    this display overwrites tile clicks so that the game only reacts to clicks on the Promotion display.

    This object handles promotion within itself. All promoted pieces are assigned a unique negative id/number. Following
    promotion the instance is thrown to the garbage collector implicitly.
    """
    def __init__(self, colorPrefix, surface, promotionPiece):
        """
        :param colorPrefix: str of the pawn's color
        :param surface: pygame.surface object of the surface to display to
        :param promotionPiece: ChessPiece object of the pawn to be promoted
        """
        self.surface = surface
        self.colorPrefix = colorPrefix
        self.promotionPiece = promotionPiece
        self.colorDirectory = "black-piece" if self.colorPrefix == "b_" else "white-piece"

        self.width = 800
        self.height = 150
        self.x = (surface.get_width() - self.width) / 2
        self.y = (surface.get_height() - self.height) / 2
        self.backgroundColor = pygame.Color(200, 200, 200)

        self.textFont = pygame.font.SysFont("arial", 20)
        self.textSurface = self.textFont.render("Select a piece to promote to", False, (0, 0, 0))

        self.promotedPieceID = -1

        self.windowBackground = pygame.Rect(self.x, self.y, self.width, self.height)
        self.promotionOptionList = []
        self.initPromotionOptions()

    def initPromotionOptions(self):
        """
        Initializes the possible pieces the pawn could be promoted to.
        :return: None
        """
        strOptions = ["queen", "knight", "rook", "bishop"]
        x = self.width / 5
        padding = x / 2
        y = 10

        for optionIndex in range(len(strOptions)):
            tile = Tile(x * optionIndex + padding + self.x, y + self.y, pygame.Color(255, 255, 255))
            tile.currentPiece = ChessPiece(strOptions[optionIndex],
                                           self.promotedPieceID,
                                           f"{self.colorDirectory}/{self.colorPrefix}{strOptions[optionIndex]}.png",
                                           self.colorPrefix)
            self.promotionOptionList.append(tile)

            # ensures every init'd piece on the board has a unique id-name pair
            self.promotedPieceID -= 1

    def draw(self):
        """
        Draws the promotion board.
        :return: None
        """
        pygame.draw.rect(self.surface, self.backgroundColor, self.windowBackground)
        for tile in self.promotionOptionList:
            tile.draw()
            piece = tile.currentPiece
            self.surface.blit(piece.image, PieceSet.getCenteredCoord(piece.image, tile))

        self.surface.blit(self.textSurface, (self.x + 40, self.y + (self.height - 30)))

    def getPromotionSelection(self, mouseCoords):
        """
        Intercepts the user's click and checks which piece they selected for their pawn to be promoted to.
        :param mouseCoords: tuple of the user click's coordinates
        :return: str of the clicked piece's name
        """
        for tile in self.promotionOptionList:
            if tile.rect.collidepoint(mouseCoords):
                self.promotePiece(tile.currentPiece.name, tile.currentPiece.image, tile.currentPiece.num)

                return tile.currentPiece.name

    def promotePiece(self, newName, newImage, newID):
        """
        Updates the piece's attributes so that in the future the correct moveset is generated for the promoted piece.
        :param newName: str of the piece that the pawn is being promoted to
        :param newImage: pygame.image object of the piece that the pawn is being promoted to
        :param newID: int of the newly promoted piece
        :return: None
        """
        self.promotionPiece.setName(newName)
        self.promotionPiece.setID(newID)
        self.promotionPiece.setImage(newImage)


class CapturedPiecesMargin:
    """
    Object representing a single margin. Takes up the empty spaces outside of the chess board. Displays the captured
    pieces of the corresponding side.
    """
    surface = None

    @classmethod
    def setSurface(cls, surface):
        cls.surface = surface

    def __init__(self, top, height):
        self.capturedPieces = [[], []]
        self.height = height

        self.padding = 20

        self.rowHeight = height / 2
        self.row1Top = top

        self.rect = None
        self.backgroundColor = None

    def setBackground(self, pygameColor):
        self.rect = pygame.Rect(0, self.row1Top, CapturedPiecesMargin.surface.get_width(), self.height)
        self.backgroundColor = pygameColor

    def addCapturedPiece(self, chessPieceObj):
        addSuccess = False
        for sublist in self.capturedPieces:
            if len(sublist) < 8 and not addSuccess:
                sublist.append(chessPieceObj)
                addSuccess = True

        assert addSuccess, "The number of captured chess pieces has exceeded the capacity of the margin"

        # Verify that chess image will not exceed height of a single row. Otherwise changes height and width to height
        if chessPieceObj.image.get_height() > (self.height / 2):
            chessPieceObj.image = pygame.transform.scale(chessPieceObj.image, (self.rowHeight, self.rowHeight))

    def draw(self):
        pygame.draw.rect(CapturedPiecesMargin.surface, self.backgroundColor, self.rect)
        for rowIndex in range(len(self.capturedPieces)):
            for colIndex in range(len(self.capturedPieces[rowIndex])):
                pieceImage = self.capturedPieces[rowIndex][colIndex].image
                x = (pieceImage.get_width() + self.padding) * colIndex
                y = pieceImage.get_height() * rowIndex + self.row1Top

                CapturedPiecesMargin.surface.blit(pieceImage, (x, y))


class ChessBoard:
    def __init__(self, surface, top, bottom):
        """
        Object of the board itself, i.e. only the checkerboard excluding top/bottom margins
        :param surface: The surface that the game takes place on
        :param top: Top coordinate of the ChessBoard object
        :param bottom: Bottom coordinate of the ChessBoard object
        """
        self.surface = surface
        self.gameOver = False
        self.top = top
        self.bottom = bottom
        self.size = (surface.get_width(), self.bottom - self.top)

        # Tile specific attributes/methods
        self.board = []
        self.createTiles()
        self.currentlyClicked = None

        # Piece specific attributes/methods
        MoveSet.setChessBoard(self)
        self.whitePieces = None
        self.blackPieces = None
        self.createPieces()

        # Promotion board specific attributes/methods
        self.promotionBoard = None

        # Game flow specific attributes/methods
        self.game = Game(self)
        self.setPieceMovesets()

        # deleteme
        self.testerImage = pygame.image.load("tester-img.png")
        self.testerImage = pygame.transform.scale(self.testerImage, (30, 30))
        self.moveCount = 0

    def createPieces(self):
        blackPiecePrefix = "b_"
        bPiecePath = "black-piece"
        whitePiecePrefix = "w_"
        wPiecePath = "white-piece"

        PieceSet.setBoard(self)
        self.blackPieces = PieceSet(bPiecePath, blackPiecePrefix, 0, self.top)
        self.whitePieces = PieceSet(wPiecePath, whitePiecePrefix, self.bottom, self.surface.get_height())

    def setPieceMovesets(self):
        for pieceSet in [self.blackPieces, self.whitePieces]:
            for piece in pieceSet.pieces:
                piece.getMoveSet()

    def createTiles(self):
        tileColorList = [pygame.Color(240, 230, 230), pygame.Color(90, 90, 90)]   # A list of the checkerboard colours
        currentColor = tileColorList[0]
        tileWidth = self.size[0] / 8
        tileHeight = self.size[1] / 8

        Tile.setSurface(self.surface)
        Tile.setSize(tileWidth, tileHeight)

        for i in range(8):
            row = []
            for j in range(8):
                singleTile = Tile((tileWidth * i), self.top + (tileHeight * j), currentColor)
                row.append(singleTile)

                currentColor = alternator(currentColor, tileColorList)
            currentColor = alternator(currentColor, tileColorList)     # This is required to create the checker pattern
            self.board.append(row)

    def dispGameOver(self):
        textFont = pygame.font.SysFont("arial", 50)
        textSurface = textFont.render(self.gameOver, False, (250, 140, 255))

        x = self.surface.get_width() / 2 - (textSurface.get_width() / 2)
        y = self.surface.get_height() / 2 - (textSurface.get_height() / 2)
        self.surface.blit(textSurface, (x, y))

    def getPlayerMove(self, mouseCoords):
        pass

    def checkBoardClick(self, mouseCoords):
        if self.gameOver:
            pass
        elif self.promotionBoard:
            selection = self.promotionBoard.getPromotionSelection(mouseCoords)
            if selection:
                self.game.alternateCurrentColor()
                self.postMovementUpdates()
                self.promotionBoard = None

        # Tiles do not react to clicks while the promotion board is open
        else:
            # Check legality of moves and endgame conditions
            self.preMovementUpdates()

            for rowNum in range(len(self.board)):
                for colNum in range(len(self.board[rowNum])):
                    tile = self.board[rowNum][colNum]

                    # check if the tile has been clicked
                    if tile.rect.collidepoint(mouseCoords):
                        # Nothing is currently selected and the clicked tile contains a piece of the current color
                        if tile.currentPiece and not self.currentlyClicked \
                                and tile.currentPiece.colorPrefix == self.game.currentColor:
                            self.toggleClickAttributes(tile)
                            tile.currentPiece.moveset.setTileValidMove(True)

                        # A tile with a piece is currently selected and the user deselects it by re-clicking it
                        elif tile == self.currentlyClicked:
                            self.currentlyClicked.currentPiece.moveset.setTileValidMove(False)
                            self.toggleClickAttributes(tile)

                        # Move the currently selected piece to the new tile
                        elif self.currentlyClicked and tile.validMove:
                            print(f"============={self.currentlyClicked.currentPiece.name} has moved")  # Diagnostic

                            # Handle all piece movements (capturing, check, etc.)
                            self.movementUpdates(tile, rowNum, colNum)

                            # Handle post-move related attributes/events (e.g. movesets, check, changing turn...)
                            self.postMovementUpdates()

    def preMovementUpdates(self):
        """
        Wrapper method containing the necessary methods to be called before a turn begins. Checks endgame conditions,
        and re-verifies the king's moveset to ensure king captures do not occur.
        :return: None
        """
        # Remove any moves that could leave the king in check
        self.game.kingCheckVerification(self.getPieceSet(self.game.currentColor).king,
                                        self.getPieceSet(self.game.opponentColor))

        # Update and check whether the current player has any legal moves
        self.game.checkLegalMoveExists(self.getPieceSet(self.game.currentColor))

        # Check whether the game has ended (stalemate / checkmate)
        self.gameOver = self.game.checkGameOver()

    def movementUpdates(self, tile, rowNum, colNum):
        """
        Wrapper method to perform a piece move. Toggles tile attributes to return it to its default state after a piece
        leaves it.
        :param tile: Tile object of the tile to move to
        :param rowNum: int index of the tile's row
        :param colNum: int index of the tile's col
        :return: None
        """
        # If the valid new tile contains an opposing piece, capture it
        if tile.currentPiece:
            self.game.capturePiece(tile)
        elif self.currentlyClicked.currentPiece.name == "pawn":
            self.game.checkEnPassant((rowNum, colNum))
        elif self.currentlyClicked.currentPiece.name == "king":
            self.game.checkCastling((rowNum, colNum), self.currentlyClicked.currentPiece)

        self.game.checkPawnDoublestep(self.currentlyClicked.currentPiece, colNum)

        movedPiece = self.currentlyClicked.currentPiece

        movedPiece.moveset.setTileValidMove(False)
        self.game.movePiece(self.currentlyClicked, (rowNum, colNum))
        self.toggleClickAttributes(self.currentlyClicked)
        movedPiece.moveset.updatePosition((movedPiece.xIndex, movedPiece.yIndex))

        if movedPiece.name == "pawn":
            # TODO bug: protected promotion pieces:
            #   1. king captures promoted pawn
            #   2. bishop previously protecting pawn captures king
            #   3. ??
            self.checkPromotion(movedPiece)

    def postMovementUpdates(self):
        """
        Updates required due to a movement: movesets, check status, and finally switching turns.
        If a check occurs, a forced king movement/sacrifice occurs for the next player's turn.
        :return: None
        """
        opponentKing = (self.getPieceSet(self.game.opponentColor)).king
        selfPieceSet = self.getPieceSet(self.game.currentColor)

        self.setPieceMovesets()
        self.game.updateCheckStatus(selfPieceSet, opponentKing)
        self.game.alternateCurrentColor()

        # Check immediately after turn change whether a check has occurred
        if self.game.inCheck[self.game.currentColor]:
            # Force a sacrifice or a king movement if the king is in check
            self.game.currentlyInCheck(self.getPieceSet(self.game.currentColor),
                                       self.getPieceSet(self.game.opponentColor))

        self.game.verifyCheckBlockingMovesets(self.getPieceSet(self.game.currentColor).king)

    def getPieceSet(self, colorPrefix):
        if colorPrefix == "b_":
            return self.blackPieces
        elif colorPrefix == "w_":
            return self.whitePieces
        else:
            raise Exception("Invalid color prefix")

    def getCapturedMargin(self, currentColorPrefix):
        if currentColorPrefix == "b_":
            return self.blackPieces.capturedPiecesMargin
        elif currentColorPrefix == "w_":
            return self.whitePieces.capturedPiecesMargin
        else:
            raise Exception("Invalid color prefix")

    def toggleClickAttributes(self, tile):
        if self.currentlyClicked == tile:  # unnecessary to check this condition again, but defensive
            self.currentlyClicked = None
        else:
            self.currentlyClicked = tile

        tile.toggleClickColor()
        tile.clicked = not tile.clicked

    def checkPromotion(self, movedPawn):
        print(movedPawn.yIndex)
        if (movedPawn.colorPrefix == "b_" and movedPawn.yIndex == 7) or \
                (movedPawn.colorPrefix == "w_" and movedPawn.yIndex == 0):
            self.promotionBoard = PromotionDisplay(movedPawn.colorPrefix, self.surface, movedPawn)

    def draw(self):

        for row in self.board:
            for tile in row:
                tile.draw()

        for pieceSet in [self.blackPieces, self.whitePieces]:
            pieceSet.draw()

        # Drawing the valid move dots over the chess pieces
        for row in self.board:
            for tile in row:
                tile.drawValidMove()

        if self.promotionBoard:
            self.promotionBoard.draw()

        # deleteme
        self.surface.blit(self.testerImage, (pygame.mouse.get_pos()))

        # Display game over message
        if self.gameOver:
            self.dispGameOver()


class PieceSet:
    chessBoard = None

    @classmethod
    def setBoard(cls, board):
        cls.chessBoard = board

    def __init__(self, directory, colorPrefix, marginTop, marginBottom):
        self.directory = directory
        self.colorPrefix = colorPrefix
        self.pieces = []
        self.king = None

        self.capturedPiecesMargin = CapturedPiecesMargin(marginTop, marginBottom - marginTop)
        CapturedPiecesMargin.setSurface(PieceSet.chessBoard.surface)
        self.capturedPiecesMargin.setBackground(pygame.Color(240, 230, 230))

        self.initPieces()

    def initPieces(self):
        """
        Initializes one set of chess pieces (i.e black, white). Additionally sets the indices for each piece w.r.t. the
        board as a whole. e.g. Left black rook = (0, 0), left white rook = (0, 7)
        :return: None
        """
        binaryPieces = ["rook", "knight", "bishop"]

        for pieceNum in range(8):
            pawnX = pieceNum
            pawnY = self.getBottomEdgeIndices(1)     # Needlessly evaluated each loop but done for readability

            pawn = ChessPiece("pawn", pieceNum,
                              f"{self.directory}/{self.colorPrefix}pawn.png",
                              self.colorPrefix)
            pawn.setIndices((pawnX, pawnY))
            self.pieces.append(pawn)

        for pieceNum in range(2):
            for pieceName in binaryPieces:
                pieceX = self.getXEdgeIndices(binaryPieces.index(pieceName), pieceNum)
                pieceY = self.getBottomEdgeIndices(0)

                piece = ChessPiece(pieceName, pieceNum,
                                   f"{self.directory}/{self.colorPrefix}{pieceName}.png",
                                   self.colorPrefix)
                piece.setIndices((pieceX, pieceY))
                self.pieces.append(piece)

        self.setQueenKing()

    def setQueenKing(self):
        queen = ChessPiece("queen", 0, f"{self.directory}/{self.colorPrefix}queen.png",
                           self.colorPrefix)
        king = ChessPiece("king", 0, f"{self.directory}/{self.colorPrefix}king.png",
                          self.colorPrefix)

        queenX = 3
        kingX = 4
        queenY = kingY = self.getBottomEdgeIndices(0)
        queen.setIndices((queenX, queenY))
        king.setIndices((kingX, kingY))

        self.pieces.append(queen)
        self.pieces.append(king)
        self.king = king

    @staticmethod
    def getXEdgeIndices(sideIndex, pieceNum):
        """
        Converts indices w.r.t. the board's edges to be in reference to the board AS A WHOLE. Remark that this is
        opposing to getBottomEdgeIndices. Additionally, this is not dependent on whether this is white/black instance.
        :param sideIndex: int of the piece's distance from the closest side
        :param pieceNum: int that is either 0 or 1. 0 is the leftmost piece, 1 is the rightmost piece.
        :return: int representing the index w.r.t. the board as a WHOLE
        """
        if pieceNum == 0:
            return sideIndex
        elif pieceNum == 1:
            return 7 - sideIndex
        else:
            raise Exception("There are more than two copies of a binary piece. (e.g. 2+ knights, rooks, etc.)")

    def getBottomEdgeIndices(self, yIndex):
        """
        Converts indices to be w.r.t the color piece set's respective bottom rather than the board as a whole.
        E.g. an index of 7 for a white piece becomes 0.
        :param yIndex:
        :return:
        """
        bottomBoardIndex = 7

        if self.colorPrefix == "b_":
            return yIndex
        elif self.colorPrefix == "w_":
            return bottomBoardIndex - yIndex
        else:
            raise Exception("The image prefixes are hardcoded. Ensure that the hard code matches the actual file.")

    def draw(self):
        for piece in self.pieces:
            tile = PieceSet.chessBoard.board[piece.xIndex][piece.yIndex]
            PieceSet.chessBoard.surface.blit(piece.image, self.getCenteredCoord(piece.image, tile))
        self.capturedPiecesMargin.draw()

    @staticmethod
    def getCenteredCoord(image, tile):
        imageWidth, imageHeight = image.get_size()
        imageWidth /= 2
        imageHeight /= 2

        return tile.rect.centerx - imageWidth, tile.rect.centery - imageHeight


class Tile:
    validMoveImg = pygame.transform.scale(pygame.image.load("green-dot.png"), (20, 20))
    surface = None
    width = None
    height = None

    @classmethod
    def setSurface(cls, surface):
        cls.surface = surface

    @classmethod
    def setSize(cls, width, height):
        cls.width = width
        cls.height = height

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.alternateColor = pygame.Color(255, 200, 200)
        self.color = color
        self.currentPiece = None

        self.rect = pygame.Rect(x, y, Tile.width, Tile.height)
        self.clicked = False
        self.validMove = False

    def draw(self):
        pygame.draw.rect(Tile.surface, self.color, self.rect)

    def drawValidMove(self):
        """
        Separate function to draw dot indicating the tile is a legal move to make. Needed to be separate from self.draw
        as drawing occurs in the order: Tiles -> Pieces, thus resulting in pieces being drawn OVER the dots. This method
        allows us to separately draw the dots AFTER drawing the chess pieces.
        :return:  None
        """
        if self.validMove:
            Tile.surface.blit(Tile.validMoveImg, PieceSet.getCenteredCoord(Tile.validMoveImg, self))

    def toggleClickColor(self):
        temp = self.color
        self.color = self.alternateColor
        self.alternateColor = temp


class ChessPiece:
    def __init__(self, name, num, imageDirStr, colorPrefix):
        self.name = name
        self.num = num
        self.image = pygame.image.load(imageDirStr)
        self.colorPrefix = colorPrefix

        self.xIndex = None
        self.yIndex = None

        self.startPos = None
        self.unMoved = True

        self.moveset = None

    def setIndices(self, coord):
        self.xIndex, self.yIndex = coord

        # Initialize moveset and location on first run
        if not self.startPos:
            self.startPos = coord
            self.moveset = MoveSet(self)

        # Update the moveset object's ChessPiece index values
        self.moveset.position = coord

        # Update the tile that now contains the current self ChessPiece
        tile = PieceSet.chessBoard.board[self.xIndex][self.yIndex]
        tile.currentPiece = self

    def setName(self, name):
        self.name = name
        self.moveset.pieceName = name

    def setImage(self, image):
        self.image = image

    def setID(self, num):
        self.num = num
        self.moveset.id = num

    def getMoveSet(self):
        self.moveset.getMoves()


main()
