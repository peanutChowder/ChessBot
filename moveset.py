class MoveSet:
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
    chessBoard = None
    @classmethod
    def setChessBoard(cls, board):
        cls.chessBoard = board

    def __init__(self, piece):
        """

        """
        self.unverifiedMoveset = {"up": [], "down": [], "left": [], "right": [],
                                 "left-up": [], "right-up": [], "right-down": [], "left-down": []}

        self.verifiedMoveset = {"up": [], "down": [], "left": [], "right": [],
                                 "left-up": [], "right-up": [], "right-down": [], "left-down": []}
        self.verifiedCaptureset = {"up": [], "down": [], "left": [], "right": [],
                              "left-up": [], "right-up": [], "right-down": [], "left-down": []}

        self.pieceMovesets = {"pawn": self.pawn, "rook": self.rook, "knight": self.knight,
                              "bishop": self.bishop, "queen": self.queen, "king": self.king}
        self.protectedPieces = []

        self.pieceName = piece.name
        self.position = (piece.xIndex, piece.yIndex)
        self.colorPrefix = piece.colorPrefix
        self.startPos = piece.startPos
        self.unMoved = piece.unMoved
        self.id = piece.num

        self.checkingKing = False

    def __getitem__(self, key):
        if key == "unverifiedMoveset":
            return self.unverifiedMoveset
        elif key == "verifiedMoveset":
            return self.verifiedMoveset
        else:
            raise Exception("Invalid key provided for moveset getter")

    def __str__(self):
        return f"{self.colorPrefix}{self.pieceName}[{self.id}]"

    def __len__(self):
        length = 0
        for key in self.verifiedMoveset:
            length += len(self.verifiedMoveset[key])

        return length

    def getListifiedCaptureset(self):
        """
        Gets the list version of verifiedCaptureset. Move positions are no longer differentiated by quadrant and all kept
        together.
        :return: list of the verified moves
        """
        listVerifiedMoves = []

        for key in self.verifiedCaptureset.keys():
            listVerifiedMoves += self.verifiedCaptureset[key]

        return listVerifiedMoves

    def updatePosition(self, newPos):
        """
        Since the position is passed by value in __init__, we must call this method after every successful piece move
        :return: None
        """
        self.position = newPos

    def clearUnverifiedMoveset(self):
        self.unverifiedMoveset = {"up": [], "down": [], "left": [], "right": [],
                                  "left-up": [], "right-up": [], "right-down": [], "left-down": []}

    def clearMovesets(self):
        """
        Clears all sets for the next use. Prevents double-appending sets to the moveset dicts.
        :return: None
        """
        self.unverifiedMoveset = {"up": [], "down": [], "left": [], "right": [],
                                 "left-up": [], "right-up": [], "right-down": [], "left-down": []}
        self.verifiedMoveset = {"up": [], "down": [], "left": [], "right": [],
                              "left-up": [], "right-up": [], "right-down": [], "left-down": []}
        self.verifiedCaptureset = {"up": [], "down": [], "left": [], "right": [],
                              "left-up": [], "right-up": [], "right-down": [], "left-down": []}
        self.protectedPieces = []

    def getMoves(self):
        print(" ========================================================\n"
              "                      NAME: ", self.pieceName)
        self.clearMovesets()

        self.setUnverifiedMoveset()
        self.verifyMoveset()
        self.setCaptureset()

        print(f"getMoves called on ======================================{self}:\n"
              f"    verified: {self.verifiedMoveset}\n"
              f"    protected: {self.protectedPieces}\n"
              f"    capture: {self.verifiedCaptureset}")


    def setUnverifiedMoveset(self):
        self.pieceMovesets[self.pieceName]()

    def setTileValidMove(self, value):
        """
        Sets the value of each index within self.verifiedMoveset by retrieving the tile associated with the index and
        setting its value.
        Additionally calls another method to clear self.verifiedMoveset and self.nonVerifiedMoves if value is False. It is
        assumed that if all valid moves are to be reset, so should the moveset lists.
        :param value: bool of the desired value
        :return: None
        """
        assert type(value) == bool

        for quadrant in self.verifiedMoveset.keys():
            for indexTuple in self.verifiedMoveset[quadrant]:
                self.chessBoard.board[indexTuple[0]][indexTuple[1]].validMove = value

    def setCaptureset(self):
        for quadrant in self.unverifiedMoveset.keys():
            for tuplePosition in self.unverifiedMoveset[quadrant]:
                if self.withinBoardBoundaries(tuplePosition):

                    # Fwd/bckwrd pawn movements are not possible captures
                    if self.pieceName == "pawn" and (quadrant == "up" or quadrant == "down"):
                        pass

                    # End movement as soon as a piece captures opponent piece
                    elif self.tileOccupiedByOpponent(tuplePosition) and not self.pieceName == "knight":
                        self.verifiedCaptureset[quadrant].append(tuplePosition)

                        # Set capturesets to go through king opponent pieces
                        if self.chessBoard.board[tuplePosition[0]][tuplePosition[1]].currentPiece.name != "king":
                            break
                        else:
                            king = self.chessBoard.board[tuplePosition[0]][tuplePosition[1]].currentPiece
                            if king.colorPrefix == self.colorPrefix:
                                break

                    # Pieces cannot move onto or through a piece containing their own color. However these pieces are
                    # protected
                    elif self.tileOccupiedBySelf(tuplePosition) and not self.pieceName == "knight":
                        self.verifiedCaptureset[quadrant].append(tuplePosition)
                        break

                    # Check if each tile is not occupied by self
                    elif not self.tileOccupiedBySelf(tuplePosition):
                        self.verifiedCaptureset[quadrant].append(tuplePosition)

    def verifyMoveset(self):
        """
        Appends all verified moves from self.unverifiedMoveset to self.verifiedMoveset. Verification is in terms of
        movement only, turn-based moves are not verified (e.g. en passant can still be performed even if opponent took
        double step two turns ago). Endgame conditions are also not verified (check/checkmate/stalemate).
        Moves are categorized by quadrant direction. Knight movements are considered diagonal.
        :return: None
        """
        if self.pieceName == "king" and self.unMoved:
            # Check if castling is possible. If so, call the method that appends the moves
            self.castlingValid()

        for quadrant in self.unverifiedMoveset.keys():
            for tuplePosition in self.unverifiedMoveset[quadrant]:
                if self.withinBoardBoundaries(tuplePosition):

                    # Handle pawn forward and diagonal movement w.r.t. opponent pieces, IGNORE self pieces
                    if self.pieceName == "pawn" and not self.tileOccupiedBySelf(tuplePosition):
                        self.pawnOpponentVerification(tuplePosition, quadrant)

                    # End movement as soon as a piece captures opponent piece
                    elif self.tileOccupiedByOpponent(tuplePosition) and not self.pieceName == "knight":
                        self.verifiedMoveset[quadrant].append(tuplePosition)
                        break

                    # Pieces cannot move onto or through a piece containing their own color. However these pieces are
                    # protected
                    elif self.tileOccupiedBySelf(tuplePosition) and not self.pieceName == "knight":
                        self.protectedPieces.append(tuplePosition)
                        break

                    # Check if each tile is not occupied by self
                    elif not self.tileOccupiedBySelf(tuplePosition):
                        self.verifiedMoveset[quadrant].append(tuplePosition)

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
                        self.verifiedMoveset[quadrant].append(pos)

                elif self.colorPrefix == "w_":
                    if not self.chessBoard.board[pos[0]][pos[1] + 1].currentPiece:
                        self.verifiedMoveset[quadrant].append(pos)

            else:
                self.verifiedMoveset[quadrant].append(pos)

        # Append diagonal indices that contain opponent pieces
        elif possiblePiece:
            self.verifiedMoveset[quadrant].append(pos)

        elif self.enPassantValid(pos):
            self.verifiedMoveset[quadrant].append(pos)

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

            # Allow en passant if an opponent pawn is adjacent (left/right) and they have just performed a double step
            if self.tileOccupiedByOpponent(adjacentTilePos) and adjacentPiece.xIndex == adjacentPiece.startPos[0] \
                    and adjacentPiece.name == "pawn" and self.chessBoard.game.recentDoublestep == adjacentPiece:
                return True

        elif self.colorPrefix == "b_" and self.position[1] == 4:
            adjacentTilePos = (pos[0], pos[1] - 1)
            adjacentPiece = self.chessBoard.board[adjacentTilePos[0]][adjacentTilePos[1]].currentPiece

            # Allow en passant if an opponent pawn is adjacent (left/right) and they have just performed a double step
            if self.tileOccupiedByOpponent(adjacentTilePos) and adjacentPiece.xIndex == adjacentPiece.startPos[0] \
                    and adjacentPiece.name == "pawn" and self.chessBoard.game.recentDoublestep == adjacentPiece:
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
            self.verifiedMoveset["left"].append((2, self.position[1]))
        elif rookPiece.xIndex == 7:
            self.verifiedMoveset["right"].append((6, self.position[1]))

    def tileOccupiedBySelf(self, pos):
        """
        Step 2.a verification. Ensures that the given tile indices are not already occupied by a friendly piece.
        :param pos: tuple of indices X, Y for the chessBoard.board list`
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
        self.unverifiedMoveset[strDirection].append((self.position[0], forwardSquareY))
        # Append double step
        if self.position == self.startPos:
            self.unverifiedMoveset[strDirection].append((self.position[0], forwardSquareY + incrementDirection))

        # Appends the diagonal positions the pawn could possibly take
        self.unverifiedMoveset[f"left-{strDirection}"].append((self.position[0] - 1, forwardSquareY))
        self.unverifiedMoveset[f"right-{strDirection}"].append((self.position[0] + 1, forwardSquareY))

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
            self.unverifiedMoveset["left"].append((leftX, self.position[1]))
        for rightX in rightIterable:
            self.unverifiedMoveset["right"].append((rightX, self.position[1]))

        # Appending the vertical moves
        upIterable = range(self.position[1] - 1, -1, -1)
        downIterable = range(self.position[1] + 1, 8)

        for upY in upIterable:
            self.unverifiedMoveset["up"].append((self.position[0], upY))
        for downY in downIterable:
            self.unverifiedMoveset["down"].append((self.position[0], downY))

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
                self.unverifiedMoveset[quadrantName].append((currentX + move[0], currentY + move[1]))

    def bishop(self):
        """
        Appends partially verified moveset of a bishop (will always be in bounds). Nested for loops more difficult to
        maintain, so kept 4 adjacent ones for readability.
        :return: None
        """
        currentX = self.position[0]
        currentY = self.position[1]

        for x, y in zip(range(currentX - 1, -1, -1), range(currentY - 1, -1, -1)):
            self.unverifiedMoveset["left-up"].append((x, y))

        for x, y in zip(range(currentX + 1, 8), range(currentY + 1, 8)):
            self.unverifiedMoveset["right-down"].append((x, y))

        for x, y in zip(range(currentX + 1, 8), range(currentY - 1, -1, -1)):
            self.unverifiedMoveset["right-up"].append((x, y))

        for x, y in zip(range(currentX - 1, -1, -1), range(currentY + 1, 8)):
            self.unverifiedMoveset["left-down"].append((x, y))

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
            self.unverifiedMoveset[moveQuadrant].append(move)
