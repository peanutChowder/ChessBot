class MoveSets:
    """
    Object that gets legal chess moves within the given piece's (via getMoves) position. Ultimately returns a list
    of tuples via a method of possible moves.

    The SAME instance is used for all ChessPiece
    objects so be careful to reset common attributes after each MoveSets use.

    Multi step refers to chess pieces that at certain times can indirectly move more than one tile in a turn.
        - i.e. bishop, queen, pawn (double step), rook
        - knight is excluded as its multi-tile step is considered a direct move. This is due to its move

    Note that subsequent references to non-verified implies: Indices are not confirmed to be within board range nor
    conforming to chess rules. E.g. even if pawn cannot move diagonal according to rules, the diagonal indices are still
    included.
    Verification occurs in three stages:
        1. Moves are verified to be within chess board boundaries with self.withinBoardBoundaries
        2. Moves are verified to conform to movement rules - e.g. two pieces cannot simultaneously occupy one tile
        3. Moves are verified in terms of game flow. Occurs in Game object. E.g. check, en passant, etc.

    :var self.nonVerifiedMoves: dict containing ALL possible moves. Chess board boundaries and other
    movement rules are not considered. Each key will often be referred to as a quadrant, which is a general direction
    of movement.
    :var self.verifiedMoves: dict containing the FULLY verified moves. All moves in this dict are completely legal in
    the current turn
    :var self.pieceMovesets: dictionary of strings and their function pointer counterparts.
    :var self.position: tuple of the current piece's indices
    :var self.colorPrefix: string of the current piece's color prefix
    """
    def __init__(self, chessBoard, gameObj):
        """
        :param chessBoard: ChessBoard object. Used to reference the Tile objects within ChessBoard.board
        """
        self.nonVerifiedMoves = {"up": [], "down": [], "left": [], "right": [],
                                 "left-up": [], "right-up": [], "right-down": [], "left-down": []}
        self.verifiedMoves = {"up": [], "down": [], "left": [], "right": [],
                                 "left-up": [], "right-up": [], "right-down": [], "left-down": []}
        self.chessBoard = chessBoard
        self.gameObject = gameObj
        self.pieceMovesets = {"pawn": self.pawn, "rook": self.rook, "knight": self.knight,
                              "bishop": self.bishop, "queen": self.queen, "king": self.king}
        self.pieceName = None
        self.position = None
        self.colorPrefix = None
        self.startPos = None
        self.unMoved = None

    def clearMovesets(self):
        self.nonVerifiedMoves = {"up": [], "down": [], "left": [], "right": [],
                                 "left-up": [], "right-up": [], "right-down": [], "left-down": []}
        self.verifiedMoves = {"up": [], "down": [], "left": [], "right": [],
                              "left-up": [], "right-up": [], "right-down": [], "left-down": []}

    def getMoves(self, name, colorPrefix, position, startPos, unMoved):
        self.setNonVerifiedMoves(name, colorPrefix, position, startPos, unMoved)

        self.verifyMoveset()

        self.setTileValidMove(True)

    def setNonVerifiedMoves(self, name, colorPrefix, position, startPos, unMoved):
        """
        Helper function for getting verified moves. Sets the non verified moves for most pieces. Some pieces s/a
        bishop, rook will be partially verified.
        :param name: string name of the chess piece
        :param colorPrefix: string prefix of the piece's color
        :param position: tuple of the piece's indices on the board
        :param startPos: bool of whether the piece has ever moved
        :return: None
        """
        assert name in self.pieceMovesets, "The string name of the given piece was not found in the moveset dictionary."

        self.pieceName = name
        self.position = position
        self.colorPrefix = colorPrefix
        self.startPos = startPos
        self.unMoved = unMoved

        self.pieceMovesets[name]()

    def setTileValidMove(self, value):
        """
        Sets the value of each index within self.verifiedMoves by retrieving the tile associated with the index and
        setting its value.
        Additionally calls another method to clear self.verifiedMoves and self.nonVerifiedMoves if value is False. It is
        assumed that if all valid moves are to be reset, so should the moveset lists.
        :param value: bool of the desired value
        :return: None
        """
        assert type(value) == bool

        for quadrant in self.verifiedMoves.keys():
            for indexTuple in self.verifiedMoves[quadrant]:
                self.chessBoard.board[indexTuple[0]][indexTuple[1]].validMove = value

        if not value:
            self.clearMovesets()

    def getCaptureMoveset(self, name, colorPrefix, position, startPos, unMoved):
        """
        Sister function of getMoves. Uses self.nonVerifiedMoves temporarily but calls self.setTileValidMove(False) to
        clear the moveset lists. Returns a list of capture moves for external handling (Refer to Game object)

            Criterion for capture moves:
            - Any tile (empty or occupied regardless of color) that an opposing piece could occupy within the current
            turn AND the current piece could capture the next turn

        e.g. A rook immediately left to a self-color pawn will have a dict that recognizes the pawn as a valid move.
        This is to capture the possibility that the enemy king takes the pawn, and immediately becomes in check.
        :return:
        """
        captureMoveset = {"up": [], "down": [], "left": [], "right": [],
                          "left-up": [], "right-up": [], "right-down": [], "left-down": []}
        self.setNonVerifiedMoves(name, colorPrefix, position, startPos, unMoved)

        for quadrant in self.nonVerifiedMoves.keys():
            for tuplePosition in self.nonVerifiedMoves[quadrant]:
                if self.withinBoardBoundaries(tuplePosition):

                    # Catch and discard pawn forward movements
                    if self.pieceName == "pawn" and (quadrant == "up" or quadrant == "down"):
                        pass

                    # Identical to verifyMoveset. Stop appending after piece reaches opposing piece
                    elif self.tileOccupiedByOpponent(tuplePosition) and not self.pieceName == "knight":
                        captureMoveset[quadrant].append(tuplePosition)
                        break

                    # Pieces can move onto a tile occupied by their color but not past it. Identical to above elif
                    elif self.tileOccupiedBySelf(tuplePosition) and not self.pieceName == "knight":
                        captureMoveset[quadrant].append(tuplePosition)
                        break

                    # Append move if tile is unoccupied
                    elif not self.tileOccupiedBySelf(tuplePosition):
                        captureMoveset[quadrant].append(tuplePosition)

        self.setTileValidMove(False)
        return captureMoveset


    def verifyMoveset(self):
        """
        Appends all verified moves from self.nonVerifiedMoves to self.verifiedMoves. Verification is in terms of
        movement only, turn-based moves are not verified (e.g. en passant can still be performed even if opponent took
        double step two turns ago). Endgame conditions are also not verified (check/checkmate/stalemate).
        Moves are categorized by quadrant direction. Knight movements are considered diagonal.
        :return: None
        """
        if self.pieceName == "king" and self.unMoved:
            # Check if castling is possible. If so, call the method that appends the moves
            self.castlingValid()

        for quadrant in self.nonVerifiedMoves.keys():
            for tuplePosition in self.nonVerifiedMoves[quadrant]:
                if self.withinBoardBoundaries(tuplePosition):

                    # Handle pawn forward and diagonal movement w.r.t. opponent pieces, IGNORE self pieces
                    if self.pieceName == "pawn" and not self.tileOccupiedBySelf(tuplePosition):
                        self.pawnOpponentVerification(tuplePosition, quadrant)

                    # End movement as soon as a piece captures opponent piece
                    elif self.tileOccupiedByOpponent(tuplePosition) and not self.pieceName == "knight":
                        self.verifiedMoves[quadrant].append(tuplePosition)
                        break

                    # Pieces cannot move onto or past a piece containing their own color. Exception: knight can move over
                    elif self.tileOccupiedBySelf(tuplePosition) and not self.pieceName == "knight":
                        break

                    # Check if each tile is not occupied by self
                    elif not self.tileOccupiedBySelf(tuplePosition):
                        self.verifiedMoves[quadrant].append(tuplePosition)

    def checkTileInCheck(self, tuplePosition):
        """
        Checks if an otherwise valid by the king could leave him in check. Only meant to be called for king pieces.
        :param tuplePosition: tuple of the tile to check
        :return: bool of whether or not the given tuple would leave the king in check
        """
        assert self.pieceName == "king", "Method should only be called on the king piece"

        if tuplePosition in self.gameObject.bothCaptureMovesets[self.gameObject.opponentColor]:
            return True
        else:
            return False

    def pawnOpponentVerification(self, pos, quadrant):
        """
        Separate method to verify pawn movement as it has multiple criterion for diagonal/forward movement. Verifies
        forward movement is not blocked by opponent pieces and diagonal movement that requires opponent pieces.
        Does not verify: boundaries, blocked by self.
        :param pos: tuple of indices for a possibly legal move. Assumes pos is NOT OCCUPIED by SELF
        :param quadrant: str of the quadrant category the tuple falls under
        :return: None
        """
        possiblePiece = self.chessBoard.board[pos[0]][pos[1]].currentPiece
        if possiblePiece and possiblePiece.colorPrefix == self.colorPrefix:
            raise Exception(self.pawnOpponentVerification.__name__,
                            "is meant for verification with tiles NOT containing self color pieces.")

        # handle forward movement
        if quadrant == "up" or quadrant == "down":
            # Pass for tiles already containing opponent piece
            if possiblePiece:
                pass

            # Ensure double steps do not step over an opponent piece
            elif abs(pos[1] - self.position[1]) == 2:
                if self.colorPrefix == "b_":
                    if not self.chessBoard.board[pos[0]][pos[1] - 1].currentPiece:
                        self.verifiedMoves[quadrant].append(pos)

                elif self.colorPrefix == "w_":
                    if not self.chessBoard.board[pos[0]][pos[1] + 1].currentPiece:
                        self.verifiedMoves[quadrant].append(pos)

            else:
                self.verifiedMoves[quadrant].append(pos)

        # Append diagonal indices that contain opponent pieces
        elif possiblePiece:
            self.verifiedMoves[quadrant].append(pos)

        elif self.enPassantValid(pos):
            self.verifiedMoves[quadrant].append(pos)

    def enPassantValid(self, pos):
        """
        Evaluates whether the current user can perform the en passant move.
        :param pos: tuple of a possibly legal move. Assumes the tuple is a DIAGONAL MOVE.
        :return: bool of whether the user may perform en passant
        """
        assert self.pieceName == "pawn", "This method only applies to pawns."

        if self.colorPrefix == "w_" and self.position[1] == 3:
            adjacentTilePos = (pos[0], pos[1] + 1)
            adjacentPiece = self.chessBoard.board[adjacentTilePos[0]][adjacentTilePos[1]].currentPiece

            if self.tileOccupiedByOpponent(adjacentTilePos) and adjacentPiece.xIndex == adjacentPiece.startPos[0] \
                    and adjacentPiece.name == "pawn":
                return True

        elif self.colorPrefix == "b_" and self.position[1] == 4:
            adjacentTilePos = (pos[0], pos[1] - 1)
            adjacentPiece = self.chessBoard.board[adjacentTilePos[0]][adjacentTilePos[1]].currentPiece

            if self.tileOccupiedByOpponent(adjacentTilePos) and adjacentPiece.xIndex == adjacentPiece.startPos[0] \
                    and adjacentPiece.name == "pawn":
                return True
        return False

    def castlingValid(self):
        """
        Check if castling is possible given the current piece positions. However, does NOT check legality w.r.t. check.
        That should be checked in the Game object.
        If castling is valid the appropriate function to append the verified move is called
        :return: None
        """

        queensideCastling = True
        kingsideCastling = True
        kingPiece = self.chessBoard.board[self.position[0]][self.position[1]].currentPiece

        if not (kingPiece.name == "king" and kingPiece.unMoved):
            pass
        else:
            leftRookPiece = self.chessBoard.board[0][self.position[1]].currentPiece
            rightRookPiece = self.chessBoard.board[7][self.position[1]].currentPiece
            for rookPiece, castlingBool, startXIndex, maxXIndex in zip([leftRookPiece, rightRookPiece],
                                                                     [queensideCastling, kingsideCastling],
                                                                     [1, 5],
                                                                     [4, 7]):
                if rookPiece and rookPiece.unMoved:
                    xIndex = startXIndex
                    while castlingBool and xIndex < maxXIndex:
                        if self.chessBoard.board[xIndex][self.position[1]].currentPiece:
                            castlingBool = False
                        xIndex += 1
                    if castlingBool:
                        self.appendCastling(rookPiece)

    def appendCastling(self, rookPiece):
        if rookPiece.xIndex == 0:
            self.verifiedMoves["left"].append((2, self.position[1]))
        elif rookPiece.xIndex == 7:
            self.verifiedMoves["right"].append((6, self.position[1]))

    def tileOccupiedBySelf(self, pos):
        """
        Step 2.a verification. Ensures that the given tile indices are not already occupied by a friendly piece.
        :param pos: tuple of indices X, Y for the chessBoard.board list
        :return: boolean of whether the given tile indices are occupied by a friendly piece
        """
        chessPiece = self.chessBoard.board[pos[0]][pos[1]].currentPiece

        if chessPiece and self.colorPrefix == chessPiece.colorPrefix:
            return True
        else:
            return False

    def tileOccupiedByOpponent(self, pos):
        """
        Nearly exact opposite of self.tileOccupiedBySelf. Duplicate was required to test for cases where the tile was
        not occupied by self nor the opponent.
        :param pos: tuple of indices X, Y of a chess Piece w.r.t. the chess board
        :return:
        """
        chessPiece = self.chessBoard.board[pos[0]][pos[1]].currentPiece

        if chessPiece and self.colorPrefix != chessPiece.colorPrefix:
            return True
        else:
            return False

    @staticmethod
    def withinBoardBoundaries(pos):
        """
        First step verification. Ensures the indices are at least within board boundaries
        :param pos: tuple of indices X, Y for the chess board
        :return: boolean of whether the given tuple is within board boundaries
        """
        for index in pos:
            if index > 7 or index < 0:
                return False
        return True

    def isSameColor(self, otherPiece):
        """
        Required to ensure that pieces do not land on tiles already containing the same color. The converse, however, is
        allowed. i.e. black pieces can capture by landing on white, but cannot land on its own color. Exceptions**
        :param otherPiece:
        :return:
        """
        return self.colorPrefix == otherPiece.colorPrefix

    def pawn(self):
        """
        Appends the non-verified moveset of pawns. Distinguishes between white/black pawns as they are directional
        pieces.
        :return: None
        """
        if self.colorPrefix == "b_":
            incrementDirection = 1
            strDirection = "down"
        elif self.colorPrefix == "w_":
            incrementDirection = -1
            strDirection = "up"
        else:
            raise Exception("Prefix given to MoveSets object does not match hard code.")

        # Appends forward position
        forwardSquareY = self.position[1] + incrementDirection
        self.nonVerifiedMoves[strDirection].append((self.position[0], forwardSquareY))
        # Append double step
        if self.position == self.startPos:
            self.nonVerifiedMoves[strDirection].append((self.position[0], forwardSquareY + incrementDirection))

        # Appends the diagonal positions the pawn could possibly take
        self.nonVerifiedMoves[f"left-{strDirection}"].append((self.position[0] - 1, forwardSquareY))
        self.nonVerifiedMoves[f"right-{strDirection}"].append((self.position[0] + 1, forwardSquareY))

    def rook(self):
        """
        Appends partially verified (boundary-wise) moveset of rooks. Continue statements used to exclude its current
        position.
        Partial verification done since an arbitrary stop number in the loop had to be chosen anyways.
        :return: None
        """
        # Appending the horizontal moves
        leftIterable = range(self.position[0] - 1, -1, -1)
        rightIterable = range(self.position[0] + 1, 8)

        for leftX in leftIterable:
            self.nonVerifiedMoves["left"].append((leftX, self.position[1]))
        for rightX in rightIterable:
            self.nonVerifiedMoves["right"].append((rightX, self.position[1]))

        # Appending the vertical moves
        upIterable = range(self.position[1] - 1, -1, -1)
        downIterable = range(self.position[1] + 1, 8)

        for upY in upIterable:
            self.nonVerifiedMoves["up"].append((self.position[0], upY))
        for downY in downIterable:
            self.nonVerifiedMoves["down"].append((self.position[0], downY))


    def knight(self):
        """
        Appends the non-verified moveset of a knight. Evaluates moves on a clockwise basis, beginning with quadrant
        left-up. Cyc
        :return: None
        """
        # Offsets are clockwise, beginning with left-up
        offsetDirections = [[(-2, 1), (-1, 2)], [(1, 2), (2, 1)],
                            [(2, -1), (1, -2)], [(-1, -2), (-2, -1)]]
        directionNames = ["left-up", "right-up",
                          "right-down", "left-down"]
        currentX, currentY = self.position[0], self.position[1]

        for quadrant, quadrantName in zip(offsetDirections, directionNames):
            for move in quadrant:
                self.nonVerifiedMoves[quadrantName].append((currentX + move[0], currentY + move[1]))

    def bishop(self):
        """
        Appends partially verified moveset of a bishop (will always be in bounds). Nested for loops more difficult to
        maintain, so kept 4 adjacent ones for readability.
        :return: None
        """
        currentX = self.position[0]
        currentY = self.position[1]

        for x, y in zip(range(currentX - 1, -1, -1), range(currentY - 1, -1, -1)):
            self.nonVerifiedMoves["left-up"].append((x, y))

        for x, y in zip(range(currentX + 1, 8), range(currentY + 1, 8)):
            self.nonVerifiedMoves["right-down"].append((x, y))

        for x, y in zip(range(currentX + 1, 8), range(currentY - 1, -1, -1)):
            self.nonVerifiedMoves["right-up"].append((x, y))

        for x, y in zip(range(currentX - 1, -1, -1), range(currentY + 1, 8)):
            self.nonVerifiedMoves["left-down"].append((x, y))

    def queen(self):
        """
        Lmao don't even know if this will work in practice but in theory it should
        :return: None
        """
        self.rook()
        self.bishop()

    def king(self):
        """
        Appends non-verified moveset of a king. Movement tuples hardcoded for readability, other implementations
        introduced unnecessary complexity.
        :return:
        """
        x = self.position[0]
        y = self.position[1]

        quadrantMoves = [(x - 1, y), (x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
                 (x + 1, y), (x + 1, y + 1), (x, y + 1), (x - 1, y + 1)]
        quadrantNames = ["left", "left-up", "up", "right-up",
                         "right", "right-down", "down", "left-down"]

        for move, moveQuadrant in zip(quadrantMoves, quadrantNames):
            self.nonVerifiedMoves[moveQuadrant].append(move)
