from moveset import MoveSet


class Game:
    """
    The game object handles chess in a game-ending orientation, i.e. checkmate, checks, etc. Additionally handles turn-
    based aspects of movements, s/a pawn diagonal capturing and other nuanced conditional movements.
    :var self.chessBoard: ChessBoard object
    :var self.currentColor: str representation of the current turn
    :var self.opponentColor: str representation of the other player
    :var self.inCheck: dict of two bool values. Represents whether either player's king is in check.
    """
    def __init__(self, board):
        self.chessBoard = board
        self.currentColor = "w_"
        self.opponentColor = "b_"

        self.inCheck = {"b_": False, "w_": False}

        self.recentDoublestep = False

        self.kingStuck = False
        self.legalMoveExists = False

    def alternateCurrentColor(self):
        temp = self.currentColor
        self.currentColor = self.opponentColor
        self.opponentColor = temp

    @staticmethod
    def movePiece(oldTile, newTileIndices):
        chessPiece = oldTile.currentPiece
        chessPiece.unMoved = False

        oldTile.currentPiece = None
        chessPiece.setIndices(newTileIndices)

    def currentColorCheck(self):
        """
        Return whether the current color is in check.
        :return: bool
        """
        return self.inCheck[self.currentColor]

    def checkLegalMoveExists(self, pieceSet):
        """
        Cycles through the provided PieceSet object to check whether at least one legal move can be made. Sets the
        result as a bool to self.legalMoveExists.
        :param pieceSet: PieceSet object of the piece set to check
        :return: None
        """
        self.legalMoveExists = False

        pieceIndex = 0
        while not self.legalMoveExists and pieceIndex < len(pieceSet.pieces):
            piece = pieceSet.pieces[pieceIndex]

            # Check if the piece has at least 1 valid move
            if len(piece.moveset):
                self.legalMoveExists = True
            pieceIndex += 1

    def currentlyInCheck(self, selfPieceSet, opponentPieceSet):
        """
        Force the current player to either sacrifice a piece or move the king out of check to end the check state.
        Called at the beginning of a turn IF the current player is in check.
        :return:
        """
        checkPieceList = Game.getCheckPieces(opponentPieceSet)

        print("CHECK PIECES:", [checkPiece.name for checkPiece in checkPieceList])
        for checkPiece in checkPieceList:
            checkPieceObj = CheckPiece(checkPiece, selfPieceSet.king)
            for piece in selfPieceSet.pieces:
                if piece.name != "king":
                    piece.moveset.verifiedMoveset = checkPieceObj.getBlockCheckPiece(piece)

    @staticmethod
    def getCheckPieces(checkPieceSet):
        checkPieces = []
        for piece in checkPieceSet.pieces:
            if piece.moveset.checkingKing:
                checkPieces.append(piece)

        return checkPieces

    def checkGameOver(self):
        if self.kingStuck:
            if self.inCheck[self.currentColor] and not self.legalMoveExists:
                return "CHECKMATE"
            elif not self.legalMoveExists:
                return "STALEMATE"

    def kingCheckVerification(self, king, opponentPieceSet):
        """
        Update the king's moveset to avoid any moves that could leave him in check. Works proactively and reactively,
        i.e. can be called while king is in check as well as called prior.
        :param king: ChessPiece object for the current color's king
        :param opponentPieceSet: PieceSet object of the opponent
        :return: None
        """
        for quadrantKey in king.moveset.verifiedMoveset.keys():
            updatedQuadrant = []

            for move in king.moveset.verifiedMoveset[quadrantKey]:
                legalMove = True
                index = 0

                while legalMove and index < len(opponentPieceSet.pieces):
                    opponentPieceCaptureset = opponentPieceSet.pieces[index].moveset.getListifiedCaptureset()
                    protectedPositions = opponentPieceSet.pieces[index].moveset.protectedPieces

                    # Does not append king moves that can be found by
                    if move in opponentPieceCaptureset or move in protectedPositions:
                        legalMove = False
                    index += 1

                if not legalMove and abs(move[0] - king.xIndex) == 1:
                    # If the king cannot move to its immediate left/right, prevent castling
                    updatedQuadrant = []
                    break
                elif legalMove:
                    updatedQuadrant.append(move)

            # Assign the newly created list of quadrant moves
            king.moveset.verifiedMoveset[quadrantKey] = updatedQuadrant

            # Label the king as stuck if it has no legal moves to take
            if len(king.moveset):
                self.kingStuck = False
            else:
                self.kingStuck = True

    def updateCheckStatus(self, selfPieceset, opponentKing):
        """
        Updates the inCheck dict for the opponentColor's check status.
        Note that this is a proactive method, i.e. should be called immediately following a self move, not an opponent
        one. Such a call would result in the illegal king capture, not checked.
        :param selfPieceset: PieceSet object of the current player
        :param opponentKing: ChessPiece object of the king of the opponent player
        :return: None
        """
        checkStatus = False

        index = 0
        while index < len(selfPieceset.pieces):
            pieceMoveset = selfPieceset.pieces[index].moveset.getListifiedCaptureset()

            if (opponentKing.xIndex, opponentKing.yIndex) in pieceMoveset:
                checkStatus = True
                selfPieceset.pieces[index].moveset.checkingKing = True
                print(f"{self.opponentColor} is now in check")
            else:
                selfPieceset.pieces[index].moveset.checkingKing = False
            index += 1

        self.inCheck[self.opponentColor] = checkStatus

    def checkCastling(self, tileIndices, king):
        kingMoveset = king.moveset["verifiedMoveset"]
        if abs(tileIndices[0] - king.xIndex) == 2 and tileIndices in kingMoveset["left"] + kingMoveset["right"]:
            if tileIndices[0] == 2:
                self.movePiece(self.chessBoard.board[0][king.yIndex], (3, king.yIndex))
            elif tileIndices[0] == 6:
                self.movePiece(self.chessBoard.board[7][king.yIndex], (5, king.yIndex))
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

        opponentPieces = self.chessBoard.getPieceSet(capturedPiece.colorPrefix).pieces
        capturedPiecesObj = self.chessBoard.getCapturedMargin(self.chessBoard.currentlyClicked.currentPiece.colorPrefix)

        opponentPieces.pop(opponentPieces.index(capturedPiece))
        newTile.currentPiece = None
        capturedPiecesObj.addCapturedPiece(capturedPiece)

    def checkPawnDoublestep(self, chessPiece, newTileY):
        """
        Checks if the current player performed a double step with their pawn. Sets recentDoublestep to a boolean false
        if not. Otherwise, recentDoublestep is set to the pawn that performed the move, which also acts as a truthy
        value.
        :param chessPiece: ChessPiece object of the piece to check
        :param newTileY: Y index of the tile that the piece is going to move to in the current turn
        :return: None
        """
        if chessPiece.name == "pawn" and abs(chessPiece.yIndex - newTileY) == 2:
            self.recentDoublestep = chessPiece
        else:
            self.recentDoublestep = False

    def checkEnPassant(self, newTileIndices):
        """
        Checks if an en passant move is possible. Strictly for pawns. Additionally ASSUMES the provided newTile is not
        occupied by anything, as opponent-occupied tiles should have been caught in self.checkBoardClick.
        Executes the en passant move if possible.
        :param newTileIndices: Tuple of the newTile indices. Explicitly passed in because Tile objects do not have an
        attribute keeping track of their indices.
        :return: None
        """
        currentPiece = self.chessBoard.currentlyClicked.currentPiece
        diagonalMove = ["left-down", "right-down"] if currentPiece.colorPrefix == "b_" else ["left-up", "right-up"]
        legalMoves = currentPiece.moveset["verifiedMoveset"]

        # En passant valid when a pawn can move diagonally yet its destination tile is empty
        if newTileIndices in legalMoves[diagonalMove[0]] or newTileIndices in legalMoves[diagonalMove[1]]:

            # En passant for black pieces
            if newTileIndices[1] > currentPiece.yIndex:
                tileContainingPawn = self.chessBoard.board[newTileIndices[0]][newTileIndices[1] - 1]
                capturedPiece = tileContainingPawn.currentPiece
            # White pieces
            elif newTileIndices[1] < currentPiece.yIndex:
                tileContainingPawn = self.chessBoard.board[newTileIndices[0]][newTileIndices[1] + 1]
                capturedPiece = tileContainingPawn.currentPiece
            else:
                raise Exception("Pieces are in wrong locations for en passant.")

            opponentPieces = self.chessBoard.getPieceSet(capturedPiece.colorPrefix).pieces
            capturedPiecesObj = self.chessBoard.getCapturedMargin(self.chessBoard.currentlyClicked.currentPiece.colorPrefix)

            opponentPieces.pop(opponentPieces.index(capturedPiece))
            tileContainingPawn.currentPiece = None
            capturedPiecesObj.addCapturedPiece(capturedPiece)

    def verifyCheckBlockingMovesets(self, king):
        """
        Method that checks whether a self piece is stopping a check from occurring. If so, updates said piece's moveset
        so that it cannot move and expose the king to a check.
        To be called post-move for the next player's turn (i.e. pre-move for the current player).
        :param king: ChessPiece object representing the king of the current player
        :return:
        """
        vulnerablePaths = self.getKingVulnerablePaths(king)

        for quadrantKey in vulnerablePaths.keys():

            possibleCheck = False
            selfPieces = []
            numPieces = 0
            index = 0
            while index < len(vulnerablePaths[quadrantKey]) and numPieces < 2:
                tileX, tileY = vulnerablePaths[quadrantKey][index]
                tile = self.chessBoard.board[tileX][tileY]
                if tile and tile.currentPiece:
                    numPieces += 1
                    if tile.currentPiece.colorPrefix == king.colorPrefix:
                        selfPieces.append(tile.currentPiece)

                    else:
                        if quadrantKey in ["left", "up", "right", "down"] and \
                                tile.currentPiece.name in ["queen", "rook"]:
                            possibleCheck = True
                        elif tile.currentPiece.name in ["queen", "bishop"]:
                            possibleCheck = True

                index += 1

            # Stop a self piece from moving only if there is only one piece between the self king and opponent's
            # threaten piece. (i.e. two pieces in total)
            if possibleCheck and len(selfPieces) == 1 and numPieces == 2:
                self.verifySacrificialPiece(selfPieces[0], quadrantKey, vulnerablePaths)



    @staticmethod
    def verifySacrificialPiece(sacrificialPiece, quadrant, kingVulnerablePaths):
        for key in sacrificialPiece.moveset.verifiedMoveset.keys():
            updatedQuadrant = []
            for move in sacrificialPiece.moveset.verifiedMoveset[key]:
                if move in kingVulnerablePaths[quadrant]:
                    updatedQuadrant.append(move)
            sacrificialPiece.moveset.verifiedMoveset[key] = updatedQuadrant
    @staticmethod
    def getKingVulnerablePaths(kingPiece):
        """
        Gets the paths that the king could be put into a position of check. Returns these paths as a dict of lists
        of tuples.
        :param kingPiece:
        :return:
        """
        kingPiece.moveset.clearUnverifiedMoveset()

        # The queen unverified moveset is identical to the king's vulnerabilities
        kingPiece.moveset.queen()

        vulnerablePaths = kingPiece.moveset.unverifiedMoveset

        return vulnerablePaths


class CheckPiece:
    def __init__(self, checkPiece, checkKingPiece):
        self.piece = checkPiece
        self.checkedKing = checkKingPiece

        self.checkQuadrant = self.getCheckQuadrant()

    def getCheckQuadrant(self):
        pieceMoveset = self.piece.moveset.verifiedMoveset
        kingIndices = (self.checkedKing.xIndex, self.checkedKing.yIndex)

        checkQuadrant = None

        for quadrantKey in pieceMoveset.keys():
            if (self.checkedKing.xIndex, self.checkedKing.yIndex) in pieceMoveset[quadrantKey]:
                checkQuadrant = pieceMoveset[quadrantKey]

        if not checkQuadrant:
            raise Exception("The given ChessPiece does not put the king in check.")

        # Pop the king's position as a move the checked pieceSet could take to end check
        checkQuadrant.pop(checkQuadrant.index(kingIndices))

        # Knights cannot be blocked but checks by knights can end by capturing the knight
        if self.piece.name == "knight":
            checkQuadrant = [(self.piece.xIndex, self.piece.yIndex)]
        else:
            # Append the checkPiece's indices as a way to end check (via capture)
            checkQuadrant.append((self.piece.xIndex, self.piece.yIndex))

        return checkQuadrant

    def getBlockCheckPiece(self, piece):
        """
        Sets any moves the given ChessPiece object could take to block the self checkPiece. Assumes that the self piece
        currently has the opponent king in check. Returns a dict of empty lists if no block pieces exist.
        :param piece: ChessPiece object of the opponent
        :return: None
        """
        captureSet = piece.moveset.verifiedCaptureset

        blockMoves = {"up": [], "down": [], "left": [], "right": [],
                      "left-up": [], "right-up": [], "right-down": [], "left-down": []}

        # Separately add the forward movements of pawns
        if piece.name == "pawn":
            pawnBlocks = self.getPawnFwdBlock(piece)
            if pawnBlocks:
                blockMoves[pawnBlocks[0]] = pawnBlocks[1]

        for key in captureSet.keys():
            for move in captureSet[key]:

                # Handle pawn's conditional diagonal movement. Quadrant is not checked bc it is assumed only
                # diagonal movements would be found in a pawn's capture set
                if piece.name == "pawn":
                    if move == (self.piece.xIndex, self.piece.yIndex):
                        blockMoves[key].append(move)
                elif move in self.checkQuadrant:
                    blockMoves[key].append(move)

        # deleteme diagnostic
        print(f"=sacrificial piece: {piece.colorPrefix}{piece.name:<6}[{piece.num:}]"
              f"                                                 {blockMoves}")

        return blockMoves

    def getPawnFwdBlock(self, pawnPiece):
        """
        Since pawn forward movements cannot be found in its capture set and self.getBlockCheckPiece is based off of the
        capture set, a separate method is needed to get its blocking moves.
        :return: tuple of a string representing the quadrant and a list of valid blockmoves, or None if no block moves
        were found.
        """
        assert pawnPiece.name == "pawn", "Method only for pawns"
        blockMoves = []
        returnKey = None

        for key in ["up", "down"]:
            for move in pawnPiece.moveset.verifiedMoveset[key]:
                if move in self.checkQuadrant:
                    blockMoves.append(move)
                    returnKey = key

        if not returnKey:
            return None
        else:
            return (returnKey, blockMoves)