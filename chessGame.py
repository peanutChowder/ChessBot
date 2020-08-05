"""
TODO: need to implement en passant only immediately after turn has been taken.

TODO: Game conditions:
    1. Check
        1. movement out of check
            - force king to move away
            - force another piece to sacrifice
        2. preventing movement into check
            - prevent king from moving into path of check
            - prevent other piece blocking check from moving
    2. Checkmate
        - should be fairly simple: when king is check, the above will force movement to be the king. Create method that
        checks whether verfiedmoves is empty -> checkmate
    3. Stalemate
        - might be difficult. Might have to check for each and every piece if a legal move exists within at least one
        verifiedmove list

    TODO: Check
        - Preventing a move into check
        - Forcing a move out of check

    TODO: getting movesets
            4. en passant:
                - pawns can only threaten other pawns with en passant, therefore it is left out of CaptureMovesets
"""

class Game:
    """
    The game object handles chess in a game-ending orientation, i.e. checkmate, checks, etc. Additionally handles turn-
    based aspects of movements, s/a en passant.
    Basis of checking for game-ending events lies in self.bothMovesets, which contains every possbile move either color
    could take.
    A similar dict exists (self.bothCaptureMovesets) which consists of only moves that could result in a
    CAPTURE. E.g. pawns moving forward are not included.
    """
    chessBoard = None

    @classmethod
    def setChessBoard(cls, board):
        cls.chessBoard = board

    def __init__(self):
        self.currentColor = "w_"
        self.opponentColor = "b_"
        self.bothMovesets = {"b_": [], "w_": []}
        self.bothCaptureMovesets = {"b_": [], "w_": []}

    def updateEntireMoveset(self, colorPrefix, pieceSet):
        """
        Creates a dict of the movesets of every piece of one color. The init'd moveset are stored in self.bothMovesets.
        A color's moveset dict is organized on a piece-basis, where the keys are composed of the piece's color prefix,
        name, and ID/number.
        :param colorPrefix: str of the color's prefix
        :param pieceSet: PieceSet object of the desired color
        :return: None
        """
        for piece in pieceSet.pieces:
            self.updatePieceMoveset(piece, colorPrefix)

        # deleteme diagnostic
        print("Capture moveset: ", self.bothCaptureMovesets[colorPrefix])
        print("Verfied moveset: ", self.bothMovesets[colorPrefix])
        print("================================")

    def updatePieceMoveset(self, piece, colorPrefix):
        """
        Updates movesets on a piece-basis. This is called after every move to update the moveset dictionary of a color.
        :param piece: ChessPiece object of the moveset to update
        :return: None
        """
        captureSet = self.bothCaptureMovesets[colorPrefix]
        fullMoveset = self.bothMovesets[colorPrefix]

        key = f"{colorPrefix}{piece.name}-{piece.num}"

        # captureSet[key] = []
        # fullMoveset[key] = []

        cMoveset = piece.getCaptureMoveset()

        piece.getMoveSet()
        vMoveset = piece.movesetObj.verifiedMoves
        piece.movesetObj.setTileValidMove(False)

        for moveDirection in cMoveset.keys():
            quadrantMoves = cMoveset[moveDirection]
            captureSet += quadrantMoves
        for moveDirection in vMoveset.keys():
            quadrantMoves = vMoveset[moveDirection]
            fullMoveset += quadrantMoves

    def alternateCurrentColor(self):
        temp = self.currentColor
        self.currentColor = self.opponentColor
        self.opponentColor = temp

class CheckCalculator(Game):

    def validMovesAvailable(self, kingPiece):
        """
        Checks if the king can move at all
        :param kingPiece: ChessPiece object of the king instance
        :return: bool of whether the king can move anywhere
        """
        assert kingPiece.name == "king", "Piece given is not the king"
        verifiedMovesDict = kingPiece.moveSetObj.verifiedMoves

        for key in verifiedMovesDict.keys():
            if len(verifiedMovesDict[key]) > 0:
                print("yuh")
                return True
        return False

    def isInCheck(self, chessPiece):
        """
        Checks if the given piece is at risk of being captured next move. Can be used with any piece but mainly for king
        :param chessPiece: ChessPiece object of the piece to check
        :return: bool of whether the piece is in check
        """
        if (chessPiece.xIndex, chessPiece.yIndex) in self.bothCaptureMovesets[self.opponentColor]:
            return True
        else:
            return False

    def isSacrificialPiece(self, chessPiece):
        pass

