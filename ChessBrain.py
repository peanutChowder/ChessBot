"""
TODO:
    - implement way to create deep copy of the entire ChessBoard object OR
    - store the state of its attributes only
        - Ensure that this does not occur during promotion (separate method call)
"""
from random import randrange
from chessboardBot import ChessBoardSim

# deleteme
from lightweightChess import LightweightChessSim


class ChessBrain:
    def __init__(self, chessBoard, selfPieceset):
        self.chessBoard = chessBoard
        self.pieceSet = selfPieceset

        # White pieces are always the minimizer
        self.minimizer = True if selfPieceset.colorPrefix == "w_" else False
        self.boardValue = None

        self.recursionDepth = 3
        self.pieceValues = {"pawn": 10, "knight": 30, "bishop": 30, "rook": 40, "queen": 90, "king": 900}

        # deleteme
        a = LightweightChessSim.convertObjRepr(chessBoard)
        b = LightweightChessSim(a, "bruh", "w_", "b_")




    def getMove(self):
        return self.getRandomMove()

    def getPromotionChoice(self):
        # always pick queen
        # TODO: implement proper promotion mechanism. How do we work promotion in?
        return 0

    def getRandomMove(self):
        randoPiece = self.pieceSet.pieces[randrange(0, len(self.pieceSet.pieces))]

        # make sure the randomly selected piece has a valid move (Presence of at least 1 legal move is checked external)
        while not len(randoPiece.moveset):
            randoPiece = self.pieceSet.pieces[randrange(0, len(self.pieceSet.pieces))]

        listVerifiedMoveset = randoPiece.moveset.getListifiedVerifiedset()

        xIndex, yIndex = listVerifiedMoveset[randrange(0, len(listVerifiedMoveset))]

        return randoPiece, xIndex, yIndex

    def getRandomPromotion(self):
        return randrange(0, 3)

    def getMiniMaxMove(self):
        miniMaxDict = self.miniMax(self.chessBoard, 0)

        if self.pieceSet.colorPrefix == "w_":
            key = min(miniMaxDict)
        elif self.pieceSet.colorPrefix == "b_":
            key = max(miniMaxDict)

        print("Minimax dict: ", miniMaxDict)

        piece = self.pieceSet.pieces[miniMaxDict[key][0]]
        moveTuple = piece.moveset.getListifiedVerifiedset()[miniMaxDict[key][1]]

        return piece, moveTuple[0], moveTuple[1]

    def miniMax(self, chessBoard, depth):
        selfPieceSet = chessBoard.getPieceSet(chessBoard.game.currentColor)

        # print("Depth: ", depth, "    currentColor: ", chessBoard.game.currentColor)

        boardValues = {}

        if depth == self.recursionDepth:
            return {chessBoard.score: "empty"}



        pieceIndex = 0
        while pieceIndex < len(selfPieceSet.pieces):
            piece = selfPieceSet.pieces[pieceIndex]

            listVerifiedset = piece.moveset.getListifiedVerifiedset()
            moveIndex = 0
            while moveIndex < len(listVerifiedset):
                move = listVerifiedset[moveIndex]
                assert selfPieceSet.colorPrefix == chessBoard.game.currentColor, "bruh"
                chessSim = ChessBoardSim(chessBoard, self.pieceValues, selfPieceSet.colorPrefix)
                chessSim.getBotMove(piece, move[0], move[1])

                if selfPieceSet.colorPrefix == "w_":
                    boardValues[min(self.miniMax(chessSim, depth + 1))] = (pieceIndex, moveIndex)
                else:
                    boardValues[max(self.miniMax(chessSim, depth + 1))] = (pieceIndex, moveIndex)

                moveIndex += 1
            pieceIndex += 1

        return boardValues


