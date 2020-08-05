import pygame
from moveset import MoveSets
from chessGame import Game


def main():
    pygame.init()
    surface = pygame.display.set_mode((1200, 800))
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
        self.boardMargin = 0.15   # This means the top and bottom margins are 10% of the entire screen, respectively
        self.chessBoard = None
        self.createBoard()

    def createBoard(self):
        boardTop = self.surface.get_height() * self.boardMargin
        boardBottom = self.surface.get_height() - (self.surface.get_height() * self.boardMargin)

        self.chessBoard = ChessBoard(self.surface, boardTop, boardBottom)

    def play(self):
        while not self.close:
            self.handleEvents()
            self.draw()

            self.clock.tick(self.fps)

    def handleEvents(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close = True

            if event.type == pygame.MOUSEBUTTONUP:
                self.chessBoard.checkBoardClick(pygame.mouse.get_pos())

                # deleteme
                print("click: ", pygame.mouse.get_pos())

    def draw(self):
        self.surface.fill(self.backgroundColor)
        self.chessBoard.draw()
        pygame.display.update()


class PromotionDisplay:
    def __init__(self, colorPrefix, surface, promotionPiece):
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
        pygame.draw.rect(self.surface, self.backgroundColor, self.windowBackground)
        for tile in self.promotionOptionList:
            tile.draw()
            piece = tile.currentPiece
            self.surface.blit(piece.image, PieceSet.getCenteredCoord(piece.image, tile))

        self.surface.blit(self.textSurface, (self.x + 40, self.y + (self.height - 30)))

    def getPromotionSelection(self, mouseCoords):
        for tile in self.promotionOptionList:
            if tile.rect.collidepoint(mouseCoords):
                self.promotePiece(tile.currentPiece.name, tile.currentPiece.image)

                return tile.currentPiece.name

    def promotePiece(self, newName, newImage):
        self.promotionPiece.name = newName
        self.promotionPiece.image = newImage


class CapturedPiecesMargin:
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
    game = Game()
    def __init__(self, surface, top, bottom):
        """
        Object of the board itself, i.e. only the checkerboard excluding top/bottom margins
        :param surface: The surface that the game takes place on
        :param top: Top coordinate of the ChessBoard object
        :param bottom: Bottom coordinate of the ChessBoard object
        """
        self.surface = surface
        self.top = top
        self.bottom = bottom
        self.size = (surface.get_width(), self.bottom - self.top)

        # Tile specific attributes/methods
        self.board = []
        self.createTiles()
        self.currentlyClicked = None

        # Piece specific attributes/methods
        self.whitePieces = None
        self.blackPieces = None
        self.createPieces()

        # Promotion board specific attributes/methods
        self.promotionBoard = None

        # deleteme
        self.testerImage = pygame.image.load("tester-img.png")
        self.testerImage = pygame.transform.scale(self.testerImage, (30, 30))


        # deleteme or not...?
        # Game specific attributes/methods
        self.draw()
        ChessBoard.game.setChessBoard(self)
        ChessBoard.game.updateEntireMoveset("b_", self.blackPieces)
        ChessBoard.game.updateEntireMoveset("w_", self.whitePieces)

    def createPieces(self):
        blackPiecePrefix = "b_"
        bPiecePath = "black-piece"
        whitePiecePrefix = "w_"
        wPiecePath = "white-piece"

        PieceSet.setBoard(self)
        self.blackPieces = PieceSet(bPiecePath, blackPiecePrefix, 0, self.top)
        self.whitePieces = PieceSet(wPiecePath, whitePiecePrefix, self.bottom, self.surface.get_height())

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

    def checkBoardClick(self, mouseCoords):
        if self.promotionBoard:
            selection = self.promotionBoard.getPromotionSelection(mouseCoords)
            if selection:
                self.promotionBoard = None

        # Tiles do not react to clicks while the promotion board is open
        else:
            for rowNum in range(len(self.board)):
                for colNum in range(len(self.board[rowNum])):
                    tile = self.board[rowNum][colNum]

                    # check if the tile has been clicked
                    if tile.rect.collidepoint(mouseCoords):
                        # Nothing is currently selected and the clicked tile contains a piece of the current color
                        if tile.currentPiece and not self.currentlyClicked \
                                and tile.currentPiece.colorPrefix == ChessBoard.game.currentColor:
                            self.toggleClickAttributes(tile)
                            tile.currentPiece.getMoveSet()

                        # A tile with a piece is currently selected and the user deselects it by re-clicking it
                        elif tile == self.currentlyClicked:
                            self.toggleClickAttributes(tile)
                            ChessPiece.movesetObj.setTileValidMove(False)

                        # Move the currently selected piece to the new tile
                        elif self.currentlyClicked and tile.validMove:
                            print(f"============={self.currentlyClicked.currentPiece.name} has moved")  # Diagnostic

                            # If the valid new tile contains an opposing piece, capture it
                            if tile.currentPiece:
                                self.capturePiece(tile)
                            elif self.currentlyClicked.currentPiece.name == "pawn":
                                self.checkEnPassant((rowNum, colNum))
                            elif self.currentlyClicked.currentPiece.name == "king":
                                self.checkCastling((rowNum, colNum))

                            movedPiece = self.currentlyClicked.currentPiece

                            ChessPiece.movesetObj.setTileValidMove(False)
                            self.movePiece(self.currentlyClicked, (rowNum, colNum))
                            self.toggleClickAttributes(self.currentlyClicked)

                            if movedPiece.name == "pawn":
                                self.checkPromotion(movedPiece)

                            ChessBoard.game.alternateCurrentColor()
                            ChessBoard.game.updateEntireMoveset("w_", self.whitePieces)
                            ChessBoard.game.updateEntireMoveset("b_", self.blackPieces)

    @staticmethod
    def movePiece(oldTile, newTileIndices):
        chessPiece = oldTile.currentPiece
        chessPiece.unMoved = False

        oldTile.currentPiece = None
        chessPiece.setIndices(newTileIndices)

    def checkPromotion(self, movedPawn):
        print(movedPawn.yIndex)
        if (movedPawn.colorPrefix == "b_" and movedPawn.yIndex == 7) or \
                (movedPawn.colorPrefix == "w_" and movedPawn.yIndex == 0):
            self.promotionBoard = PromotionDisplay(movedPawn.colorPrefix, self.surface, movedPawn)

    def checkCastling(self, tileIndices):
        king = self.currentlyClicked.currentPiece

        kingMoveset = ChessPiece.movesetObj.verifiedMoves
        if abs(tileIndices[0] - king.xIndex) == 2 and tileIndices in kingMoveset["left"] + kingMoveset["right"]:
            if tileIndices[0] == 2:
                self.movePiece(self.board[0][king.yIndex], (3, king.yIndex))
            elif tileIndices[0] == 6:
                self.movePiece(self.board[7][king.yIndex], (5, king.yIndex))
            else:
                raise Exception("Invalid movement during castling.")

    def capturePiece(self, newTile):
        """
        Pops the captured piece from the opponent's PieceSet.pieces list. The new tile's currentPiece attr. is set
        to None as a defensive measure. Appends the captured piece to the current player's PieceSet.CapturedPiecesMargin
        list of captured pieces. Method only works for moves where the current piece takes the place of the captured
        piece. (i.e. doesn't work for en passant)
        :param newTile: Tile object of the destination of the move. newTile is ASSUMED to contain an opponent's piece
        :return: None
        """
        capturedPiece = newTile.currentPiece

        opponentPieces = self.getPieceSet(capturedPiece.colorPrefix)
        capturedPiecesObj = self.getCapturedMargin(self.currentlyClicked.currentPiece.colorPrefix)

        opponentPieces.pop(opponentPieces.index(capturedPiece))
        newTile.currentPiece = None
        capturedPiecesObj.addCapturedPiece(capturedPiece)

    def checkEnPassant(self, newTileIndices):
        """
        Checks if an en passant move is possible. Strictly for pawns. Additionally ASSUMES the provided newTile is not
        occupied by anything, as opponent-occupied tiles should have been caught in self.checkBoardClick.
        Executes the en passant move if possible.
        :param newTileIndices: Tuple of the newTile indices. Explicitly passed in because Tile objects do not have an
        attribute keeping track of their indices.
        :return: None
        """
        currentPiece = self.currentlyClicked.currentPiece
        diagonalMove = ["left-down", "right-down"] if currentPiece.colorPrefix == "b_" else ["left-up", "right-up"]
        legalMoves = ChessPiece.movesetObj.verifiedMoves

        # En passant valid when a pawn can move diagonally yet its destination tile is empty
        if newTileIndices in legalMoves[diagonalMove[0]] or newTileIndices in legalMoves[diagonalMove[1]]:

            # En passant for black pieces
            if newTileIndices[1] > currentPiece.yIndex:
                tileContainingPawn = self.board[newTileIndices[0]][newTileIndices[1] - 1]
                capturedPiece = tileContainingPawn.currentPiece
            # White pieces
            elif newTileIndices[1] < currentPiece.yIndex:
                tileContainingPawn = self.board[newTileIndices[0]][newTileIndices[1] + 1]
                capturedPiece = tileContainingPawn.currentPiece
            else:
                raise Exception("Pieces are in wrong locations for en passant.")

            opponentPieces = self.getPieceSet(capturedPiece.colorPrefix)
            capturedPiecesObj = self.getCapturedMargin(self.currentlyClicked.currentPiece.colorPrefix)

            opponentPieces.pop(opponentPieces.index(capturedPiece))
            tileContainingPawn.currentPiece = None
            capturedPiecesObj.addCapturedPiece(capturedPiece)

    def getPieceSet(self, colorPrefix):
        if colorPrefix == "b_":
            return self.blackPieces.pieces
        elif colorPrefix == "w_":
            return self.whitePieces.pieces
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

        tile.toggleColor()
        tile.clicked = not tile.clicked

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


class PieceSet:
    chessBoard = None

    @classmethod
    def setBoard(cls, board):
        cls.chessBoard = board

    def __init__(self, directory, colorPrefix, marginTop, marginBottom):
        self.directory = directory
        self.colorPrefix = colorPrefix
        self.pieces = []

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

        ChessPiece.setMovesetObj(PieceSet.chessBoard)

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
            tile.currentPiece = piece

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

    def toggleColor(self):
        temp = self.color
        self.color = self.alternateColor
        self.alternateColor = temp


class ChessPiece:
    # deleteme cleanup
    # gameObj = None
    movesetObj = None

    # @classmethod
    # def setGameObj(cls, game):
    #     cls.gameObj = game

    @classmethod
    def setMovesetObj(cls, chessBoardObj):
        cls.movesetObj = MoveSets(chessBoardObj, ChessBoard.game)

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

        if not self.startPos:
            self.startPos = coord

    def getCaptureMoveset(self):
        return ChessPiece.movesetObj.getCaptureMoveset(self.name, self.colorPrefix, (self.xIndex, self.yIndex),
                                       self.startPos, self.unMoved)

    def getMoveSet(self):
        ChessPiece.movesetObj.getMoves(self.name, self.colorPrefix, (self.xIndex, self.yIndex),
                                       self.startPos, self.unMoved)


main()
