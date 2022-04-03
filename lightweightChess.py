"""
TODO:
    1. verify king moveset PRIOR to actual movement
"""

from lightweightChessGame import GameSim
from lightweightMoveset import MoveSetLightweight


class LightweightChessSim:
    @staticmethod
    def convertObjRepr(chessBoardObj):
        newRepr = [[0, 0, 0, 0, 0, 0, 0, 0],
                   [0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0]]
        row = 0
        while row < 8:
            col = 0
            while col < 8:
                piece = chessBoardObj.board[row][col].currentPiece
                if piece:
                    # TODO: how come it only works when col and row are reversed?
                    newRepr[col][row] = str(piece.moveset) + f"-{row}-{col}"

                col += 1
            row += 1
        return newRepr

    diagnostic = False
    def __init__(self, lightweightBoard, pieceValueDict, currentColor, opponentColor):

        self.gameOver = False

        self.pieceValues = pieceValueDict
        self.score = None

        # Tile specific attributes/methods
        self.board = lightweightBoard

        self.pieces = {"b_": [], "w_": []}
        # Tuple of each color prefix's king position
        self.kingPos = {}
        self.getPieces()

        # Moveset / Captureset attributes
        self.lightMovesetObj = MoveSetLightweight(self.board)
        self.pieceMoves = {}

        self.lightGame = GameSim(self, currentColor, opponentColor)

        self.promotion = False

        # deleteme
        print(self)


    def __str__(self):
        strRepr = ""
        for row in self.board:
            strRepr += str(row)
            strRepr += "\n"

        return strRepr

    def getPieceColor(self, pos):
        if not self.board[pos[0]][pos[1]]:
            return None
        return self.board[pos[0]][pos[1]][:2]

    def getPieceName(self, pos):
        if not self.board[pos[0]][pos[1]]:
            return None
        pieceAttrList = self.board[pos[0]][pos[1]].split("-")
        return pieceAttrList[1]

    def getPieceUnmoved(self, pos):
        if not self.board[pos[0]][pos[1]]:
            return None
        pieceAttrList = self.board[pos[0]][pos[1]].split("-")

        if pieceAttrList[3] == "True":
            return True
        else:
            return False

    def getPosFromRepr(self, pieceRepr):
        pieceAttrList = pieceRepr.split("-")
        xIndex = int(pieceAttrList[4])
        yIndex = int(pieceAttrList[5])

        return xIndex, yIndex


    def getPieces(self):
        for rowNum in range(len(self.board)):
            for colNum in range(len(self.board)):
                pieceColor = self.getPieceColor((rowNum, colNum))
                if pieceColor == "w_":
                    self.pieces["w_"].append(self.board[rowNum][colNum])
                elif pieceColor == "b_":
                    self.pieces["b_"].append(self.board[rowNum][colNum])

                if self.getPieceName((rowNum, colNum)) == "king":
                    self.kingPos[pieceColor] = (rowNum, colNum)

    def setPieceMovesets(self):
        self.pieceMoves = {}
        for pieceRepr in self.pieces["b_"] + self.pieces["w_"]:
            self.lightMovesetObj.setPieceAttributes(pieceRepr)
            self.pieceMoves[pieceRepr] = self.lightMovesetObj.getLightweightMoves()

    def updatePiece(self, piecePos, newAttributeList):
        """
        Updates the piece's attributes. Note that ALL of the piece's attributes must be called in via newAttributeList.
        Additionally, does not delete the old piece repr on self.board if the piece is moved.
        :param piecePos: Tuple of the piece to update
        :param newAttributeList: A list of exactly len 5 of all the attributes. If the attribute is not to be updated,
        the attribute will be a string: "N/A".
        :return:
        """
        assert len(newAttributeList) == 5, "Must enter all attributes"

        oldPieceRepr = self.board[piecePos[0]][piecePos[1]]
        pieceAttributes = oldPieceRepr.split("-")

        # update any requested attributes with new values
        for i in range(len(newAttributeList)):
            # N/A represents an unchanged attribute
            if newAttributeList[i] == "N/A":
                # TODO: it is continue right? to pass a single loop iteration but not break it?
                continue
            else:
                pieceAttributes[i] = newAttributeList[i]

        # Convert the updated attributes back into the string repr
        newPieceRepr = "-".join(pieceAttributes.values())

        # Update self.board
        self.board[newAttributeList[4]][newAttributeList[5]] = newPieceRepr

        # No need to update self.pieceMoves since it is emptied and re-created per turn based off self.pieces

        # Update self.pieces
        pieceColor = newAttributeList[0]

        self.pieces[pieceColor].pop(self.pieces[pieceColor].index(oldPieceRepr))
        self.pieces[pieceColor].append(newPieceRepr)

    def removePiece(self, piecePos):
        """
        Removes a piece from all saved game data (movesets, board, piecesets) to be eaten by the garbage collector.
        Does not clear self.pieceMoves as it is based off self.pieces.
        :param piecePos:
        :return:
        """
        # Keep a reference to the piece's repr to remove from self.pieces
        pieceColor = self.getPieceColor(piecePos)
        piece = self.board[piecePos[0]][piecePos[1]]

        # Remove the piece from self.board
        self.board[piecePos[0]][piecePos[1]] = 0

        # Remove the piece from self.pieces
        self.pieces[pieceColor].pop(piece)

        # No need to update self.pieceMoves since it is emptied and re-created per turn based off self.pieces

    def calcBoardScore(self):
        # TODO: make
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

    def getBotMove(self, piecePos, rowNum, colNum):

        if not self.gameOver:
            if self.promotion:
                pass
                # TODO: make

            else:
                # TODO: create an "adapter" to convert from ChessPiece obj to repr pos on the board, prolly external
                pieceRepr = self.board[piecePos[0]][piecePos[1]]
                assert (rowNum, colNum) in self.pieceMoves[pieceRepr]["verifiedMoveset"], \
                    "Move tuple passed to LWChess is not a legal move!"

                self.movementUpdates(piecePos, rowNum, colNum)
                self.postMovementUpdates()

            self.calcBoardScore()

    def preMovementUpdates(self):
        # TODO: current goal:
        #   bit by bit converting 3 movement functions. Currently on this one.
        self.setPieceMovesets()

        self.lightGame.updateCheckStatus(self.kingPos[self.lightGame.currentColor],
                                         self.pieceMoves)

        # TODO: everything below is copy pasted from post-movement updates, so they will be using the wrong color.
        #   fix dat shit
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

    def movementUpdates(self, movePiecePos, rowNum, colNum):

        # If the valid new tile contains an opposing piece, capture it
        if self.board[rowNum][colNum]:
            self.lightGame.capturePiece((rowNum, colNum))

        # if the piece to be moved is a pawn check if the move is en passant
        elif self.getPieceName(movePiecePos) == "pawn":
            if self.lightGame.isMoveEnPassant(movePiecePos, (rowNum, colNum)):
                self.lightGame.enPassantCapture(movePiecePos, (rowNum, colNum))

        # if the piece to be moved is the king check if the move is castling
        elif self.getPieceName(movePiecePos) == "king":
            if self.lightGame.isCastling(movePiecePos, (rowNum, colNum)):
                self.lightGame.castlingMoveRook(movePiecePos[1], (rowNum, colNum))
            self.kingPos[self.getPieceColor(movePiecePos)] = (rowNum, colNum)

        # TODO: make sure that the piece repr has pre-move indices
        self.lightGame.checkPawnDoublestep(movePiecePos, colNum)

        self.lightGame.movePiece(movePiecePos, (rowNum, colNum))

        if self.getPieceName((rowNum, colNum)) == "pawn":
            # TODO bug: protected promotion pieces:
            #   1. king captures promoted pawn
            #   2. bishop previously protecting pawn captures king
            #   3. ??
            self.checkPromotion((rowNum, colNum))

    def checkPromotion(self, pawnPos):
        # Do not need to check pawn color since pawns can only attain these positions by going forwards
        if pawnPos[1] == 7 or pawnPos[1]:
            # TODO: make this shit
            self.promotion = True

    def postMovementUpdates(self):
        """
        Updates required due to a movement: movesets, check status, and finally switching turns.
        If a check occurs, a forced king movement/sacrifice occurs for the next player's turn.
        :return: None
        """
        if not self.promotionBoard:
            # TODO: we gonna have to deal with promotion boards. do we add the above if clause here?
            #   or in pre-movement updates? or both?
            self.game.alternateCurrentColor()

            #     # Check immediately after turn change whether a check has occurred
            # if self.game.inCheck[self.game.currentColor]:
            #     # Force a sacrifice or a king movement if the king is in check
            #     self.game.currentlyInCheck(self.getPieceSet(self.game.currentColor),
            #                                self.getPieceSet(self.game.opponentColor))
            #
            # self.game.verifyCheckBlockingMovesets(self.getPieceSet(self.game.currentColor).king)
            #
            # # Remove any moves that could leave the king in check
            # self.game.preventKingCapture(self.getPieceSet(self.game.currentColor).king,
            #                              self.getPieceSet(self.game.opponentColor))
            #
            # # Update and check whether the current player has any legal moves
            # self.game.checkLegalMoveExists(self.getPieceSet(self.game.currentColor))
            #
            # # Check whether the game has ended (stalemate / checkmate)
            # self.gameOver = self.game.checkGameOver()

    def getPieceSet(self, colorPrefix):
        if colorPrefix == "b_":
            return self.blackPieces
        elif colorPrefix == "w_":
            return self.whitePieces
        else:
            raise Exception("Invalid color prefix")



