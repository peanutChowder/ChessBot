from chessGame import Game


def getListifiedVersion(dictSet):
    listVersion = []

    for key in dictSet.keys():
        listVersion += dictSet[key]
    return listVersion

class GameSim(Game):
    def __init__(self, chessSim, currentColor, opponentColor):
        super().__init__(None)
        self.chessSim = chessSim
        self.currentColor = currentColor
        self.opponentColor = opponentColor

        self.checkPiecesPositions = {}

    def capturePiece(self, tilePos):
        assert self.chessSim.getPieceName(tilePos) != "king", "The king cannot be captured!!"

        self.chessSim.removePiece(tilePos)
        self.turnsSinceCapture = 0

    def movePiece(self, oldTileIndices, newTileIndices):
        updatedAttributes = ["N/A", "N/A", "N/A", False, newTileIndices[0], newTileIndices[1]]
        self.chessSim.updatePiece(oldTileIndices, updatedAttributes)

        self.chessSim.board[oldTileIndices[0]][oldTileIndices[1]] = 0

    def checkPawnDoublestep(self, oldPos, newYIndex):
        """
        Checks whether the move about to be performed is a pawn double step. Sets self.recentDoublestep
        to true/false depending on this.
        :param oldPos: tuple of the piece before the move
        :param newYIndex: tuple that the piece will move to
        :return:
        None
        """
        if self.chessSim.getPieceName(oldPos) == "pawn" and oldPos[1] - newYIndex == 2:
            self.recentDoublestep = self.chessSim.board[oldPos[0]][oldPos[1]]
        else:
            self.recentDoublestep = False

    def isMoveEnPassant(self, pawnPos, newTileIndices):
        """
        Checks whether a given move tuple is en passant by checking if it is diagonal even though no opponent piece
        occupies the diagonal tile.
        Assumes the given piece position is that of a pawn. Additionally assumes the newTileIndices are not occupied by
        anything. Opponent occupied tiles should have been caught in __________
        :param pawnPos: tuple of the pawn's position pre-move
        :param newTileIndices: tuple of the tile to move to
        :return:
        bool of whether the given move is en passant
        """
        diagonalMove = ["left-down", "right-down"] \
            if self.chessSim.getPieceColor(pawnPos) == "b_" else ["left-up", "right-up"]
        legalMoves = self.chessSim.pieceMoves["verifiedMoveset"]

        if newTileIndices in legalMoves[diagonalMove[0]] or newTileIndices in legalMoves[diagonalMove[1]]:
            return True
        else:
            return False

    def enPassantCapture(self, pawnPos, newTileIndices):
        """
        Captures the opponent pawn during an en passant move. Only to be called when confirmed the newTileIndices are
        en passant. Additionally only performs the capture, does not actually move the self pawn.
        :param pawnPos: tuple of the self pawn's position pre-move
        :param newTileIndices: tuple of the tile the self pawn will move to
        :return:
        None
        """
        # En passant for black pieces
        if newTileIndices[1] > pawnPos[1]:
            self.chessSim.removePiece((newTileIndices[0], newTileIndices[1] - 1))
        # White pieces
        elif newTileIndices[1] < pawnPos[1]:
            self.chessSim.removePiece((newTileIndices[0], newTileIndices[1] + 1))
        else:
            raise Exception("Pieces are in wrong locations for en passant.")

    def isCastling(self, kingPos, tileIndices):
        """
        Checks whether the given move is a castling move. Assumes the method is called on a king piece.
        Castling checking is done by finding the difference between the king's previous and new position x indices.
        Castling always results in the king moving 2 tiles in the x direction.
        :param kingPos: tuple of the king's pre-move position
        :param tileIndices: tuple of the position the king will move to
        :return:
        bool of whether or not the move is a castling move
        """
        return abs(tileIndices[0] - kingPos[0]) == 2

    def castlingMoveRook(self, kingYIndex, tileIndices):
        """
        To be called on a move that is confirmed to be castling. Moves the appropriate rook to its post-castling
        position. Does NOT move the king.
        :return:
        """
        if tileIndices[0] == 2:
            self.movePiece(self.chessSim.board[0][kingYIndex], (3, kingYIndex))
        elif tileIndices[0] == 6:
            self.movePiece(self.chessSim.board[7][kingYIndex], (5, kingYIndex))
        else:
            raise Exception("Invalid movement during castling.")

    def updateCheckStatus(self, kingPos, pieceMoves):
        checkStatus = False

        allOpponentPieceReprs = self.chessSim.pieces[self.opponentColor]

        for opponentPieceRepr in allOpponentPieceReprs:
            opponentPieceMoveset = getListifiedVersion(pieceMoves[opponentPieceRepr]["verifiedMoveset"])

            # Append the opponent's piece to a list of pieces putting the king in check
            if kingPos in opponentPieceMoveset:
                checkStatus = True
                self.checkPiecesPositions[self.chessSim.getPosFromRepr(opponentPieceRepr)] = None

        self.inCheck[self.currentColor] = checkStatus

    def currentlyInCheck(self, selfPieceSet, opponentPieceSet):
        for checkPiecePos in self.checkPiecesPositions:
            # TODO: create new func for checkpieces. previous version used CheckPieces class
            # TODO: WARNING!! in CheckPiece.getBlockCheckPiece, the moveset of each potential sacrifice piece is cleared
            #   EACH TIME, even if its previous moveset already was updated w. a sacrifice move.
            #   Tl;dr, multiple check pieces could fuck things up.
            #   corollary: how can we ensure that when multiple checkpieces exist, given that a move exists that can
            #   block ALL checkpieces, we force the user to play that move?

            # recent note: it might be impossible for the above scenario to occur anyways.
            #   1. there does not seem to a single move that could result in TWO+ checkpieces
            #   2. sacrificemoves appear to be set BEFORE preventKingCheck moves, thus the former is overwritten by the
            #   latter. make sure this holds true
            # leftoff here. Just started working on the method below
            pass

    def setCheckQuadrant(self):
        """

        :return:
        """

