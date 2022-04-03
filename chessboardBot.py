from moveset import MoveSet
from chessGame import Game

class PromotionSim:
    """
    An object representing the temporary display that appears when a pawn reaches its opposite side. The presence of
    this display overwrites tile clicks so that the game only reacts to clicks on the Promotion display.

    This object handles promotion within itself. All promoted pieces are assigned a unique negative id/number. Following
    promotion the instance is thrown to the garbage collector implicitly.
    """
    promotedPieceID = -1

    def __init__(self, colorPrefix, promotionPiece):
        """
        :param colorPrefix: str of the pawn's color
        :param promotionPiece: ChessPiece object of the pawn to be promoted
        """
        self.colorPrefix = colorPrefix
        self.promotionPiece = promotionPiece
        self.promotionOptionList = ["queen", "knight", "rook", "bishop"]

    def getBotPromotionSelection(self):
        # TODO: temporarily set to always promote to queen
        selectedPieceName = self.promotionOptionList[0]

        self.promotePiece(selectedPieceName)

    def promotePiece(self, newName):
        self.promotionPiece.setName(newName)
        self.promotionPiece.setID(PromotionSim.promotedPieceID)
        PromotionSim.promotedPieceID -= 1


class ChessBoardSim:
    diagnostic = False
    def __init__(self, realChessBoard, pieceValueDict, currentTurn):


        self.gameOver = False
        self.realChessBoard = realChessBoard

        self.pieceValues = pieceValueDict
        self.score = None

        # Tile specific attributes/methods
        self.board = []
        self.createTiles()
        self.currentlyClicked = None

        # Piece specific attributes/methods
        PieceSetSim.setBoard(self)
        self.blackPieces = PieceSetSim("b_", realChessBoard.blackPieces)
        self.whitePieces = PieceSetSim("w_", realChessBoard.whitePieces)

        # Promotion board specific attributes/methods
        self.promotionBoard = None

        # Game flow specific attributes/methods
        self.game = GameSim(self, realChessBoard.game.currentColor, realChessBoard.game.opponentColor)
        self.setPieceMovesets()

    def createTiles(self):
        for i in range(8):
            row = []
            for j in range(8):
                singleTile = TileSim()
                row.append(singleTile)
            self.board.append(row)

    def calcBoardScore(self):
        self.score = 0

        # Black pieces are always the maximizer
        for piece in self.blackPieces.pieces:
            self.score += self.pieceValues[piece.name]
        # Add the king being in check as a value since it cannot actually be captured
        if self.game.inCheck["w_"]:
            self.score += self.pieceValues["king"]

        # White pieces are always the minimizer
        for piece in self.whitePieces.pieces:
            self.score -= self.pieceValues[piece.name]
        if self.game.inCheck["b_"]:
            self.score -= self.pieceValues["king"]

    def getBoardScore(self):
        return self.getBoardScore()

    def setPieceMovesets(self):
        for pieceSet in [self.blackPieces, self.whitePieces]:
            for piece in pieceSet.pieces:
                piece.getMoveSet()

    def getBotMove(self, piece, rowNum, colNum):

        if not self.gameOver:
            if self.promotionBoard:
                if ChessBoardSim.diagnostic:
                    print("BOT PROMOTION BOARD")
                self.promotionBoard.getBotPromotionSelection()

                self.promotionBoard = None
                self.postMovementUpdates()

            else:
                self.toggleClickAttributes(self.board[piece.xIndex][piece.yIndex])
                self.currentlyClicked.currentPiece.moveset.setTileValidMove(True)

                tile = self.board[rowNum][colNum]

                assert self.currentlyClicked.currentPiece.colorPrefix == self.game.currentColor, "Colors do not match up."

                self.movementUpdates(tile, rowNum, colNum)
                self.postMovementUpdates()

            self.calcBoardScore()

    def movementUpdates(self, tile, rowNum, colNum):
        """
        Wrapper method to perform a piece move. Toggles tile attributes to return it to its default state after a piece
        leaves it.
        :param tile: Tile object of the tile to move to
        :param rowNum: int index of the tile's row
        :param colNum: int index of the tile's col
        :return: None
        """
        if ChessBoardSim.diagnostic:
            print(f"\n\n============={self.currentlyClicked.currentPiece.name} has moved")  # Diagnostic

        # If the valid new tile contains an opposing piece, capture it
        if tile.currentPiece and tile.validMove:
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

        # TODO: testing player change turns
        if not self.promotionBoard:
            self.game.alternateCurrentColor()
            if ChessBoardSim.diagnostic:
                print("BOT HAS CHANGED COLOUR")

        # Check immediately after turn change whether a check has occurred
        if self.game.inCheck[self.game.currentColor]:
            # Force a sacrifice or a king movement if the king is in check
            self.game.currentlyInCheck(self.getPieceSet(self.game.currentColor),
                                       self.getPieceSet(self.game.opponentColor))

        self.game.verifyCheckBlockingMovesets(self.getPieceSet(self.game.currentColor).king)

        # Remove any moves that could leave the king in check
        self.game.preventKingCapture(self.getPieceSet(self.game.currentColor).king,
                                     self.getPieceSet(self.game.opponentColor))

        # Update and check whether the current player has any legal moves
        self.game.checkLegalMoveExists(self.getPieceSet(self.game.currentColor))

        # Check whether the game has ended (stalemate / checkmate)
        self.gameOver = self.game.checkGameOver()

    def getPieceSet(self, colorPrefix):
        if colorPrefix == "b_":
            return self.blackPieces
        elif colorPrefix == "w_":
            return self.whitePieces
        else:
            raise Exception("Invalid color prefix")

    def toggleClickAttributes(self, tile):
        if self.currentlyClicked == tile:  # unnecessary to check this condition again, but defensive
            self.currentlyClicked = None
        else:
            self.currentlyClicked = tile

        tile.clicked = not tile.clicked

    def checkPromotion(self, movedPawn):
        if ChessBoardSim.diagnostic:
            print(movedPawn.yIndex)
        if (movedPawn.colorPrefix == "b_" and movedPawn.yIndex == 7) or \
                (movedPawn.colorPrefix == "w_" and movedPawn.yIndex == 0):
            self.promotionBoard = PromotionSim(movedPawn.colorPrefix, movedPawn)


class PieceSetSim:
    chessBoard = None

    @classmethod
    def setBoard(cls, board):
        cls.chessBoard = board

    def __init__(self, colorPrefix, realPieceSet):
        self.realPieceSet = realPieceSet
        self.colorPrefix = colorPrefix
        self.pieces = []
        self.king = None

        self.setSimulation()

    def setSimulation(self):
        # Clear previous usage
        self.pieces = []

        for piece in self.realPieceSet.pieces:
            pieceCopy = self.makePieceCopy(piece)

            # Set a link from the occupied tile to the pieceCopy
            pieceOccupiedTile = PieceSetSim.chessBoard.board[pieceCopy.xIndex][pieceCopy.yIndex]
            pieceOccupiedTile.currentPiece = pieceCopy

            if pieceCopy.name == "king":
                self.king = pieceCopy

            self.pieces.append(pieceCopy)

    @staticmethod
    def makePieceCopy(piece):
        """
        Makes a deep copy of the provided ChessPiece obj by setting the new object attributes to that of the original.
        Returns the deep copy.
        :param piece: ChessPiece obj of the piece to be deep copied
        :return: ChessPiece obj of the deep copy
        """
        pieceCopy = ChessPieceSim(piece.name, piece.num, piece.colorPrefix)

        pieceCopy.startPos = piece.startPos
        pieceCopy.xIndex = piece.xIndex
        pieceCopy.yIndex = piece.yIndex

        # captured attribute is False by default so does not need to be set

        # Give each copied piece a fresh MoveSet instance
        pieceCopy.moveset = MoveSet(pieceCopy, PieceSetSim.chessBoard)

        return pieceCopy


class TileSim:
    def __init__(self):
        self.clicked = False
        self.currentPiece = None
        self.validMove = False


class ChessPieceSim:
    def __init__(self, name, num, colorPrefix):
        self.name = name
        self.num = num
        self.colorPrefix = colorPrefix

        self.xIndex = None
        self.yIndex = None

        self.startPos = None
        self.unMoved = True

        self.captured = False

        self.moveset = None

    def setIndices(self, coord):
        self.xIndex, self.yIndex = coord

        # Initialize moveset and location on first run
        if not self.startPos:
            self.startPos = coord
            self.moveset = MoveSet(self, PieceSetSim.chessBoard)

        # Update the moveset object's ChessPiece index values
        self.moveset.position = coord

        # Update the tile that now contains the current self ChessPiece
        tile = PieceSetSim.chessBoard.board[self.xIndex][self.yIndex]
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


class GameSim(Game):
    def __init__(self, chessBoard, currentColor, opponentColor):
        super().__init__(chessBoard)
        self.currentColor = currentColor
        self.opponentColor = opponentColor

    def capturePiece(self, newTile):
        capturedPiece = newTile.currentPiece
        assert capturedPiece.name != "king", "The king cannot be captured!!"

        opponentPieces = self.chessBoard.getPieceSet(capturedPiece.colorPrefix).pieces

        # Let garbage collector eat the captured piece
        opponentPieces.pop(opponentPieces.index(capturedPiece))
        capturedPiece.captured = True
        newTile.currentPiece = None

        self.turnsSinceCapture = 0