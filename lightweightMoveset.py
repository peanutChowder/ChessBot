from moveset import MoveSet

class MoveSetLightweight(MoveSet):

    def __init__(self, board):
        super().__init__("lightweight", None)

        self.board = board
        self.pieceName = None
        self.position = None
        self.colorPrefix = None
        self.startPos = None
        self.unMoved = None
        self.id = None

    def setPieceAttributes(self, pieceRepr):
        pieceAttrList = pieceRepr.split("-")

        self.colorPrefix = pieceAttrList[0]
        self.pieceName = pieceAttrList[1]
        self.id = pieceAttrList[2]
        self.unMoved = True if pieceAttrList[3] == "True" else False
        self.position = (pieceAttrList[4], pieceAttrList[5])

    def getLightweightMoves(self):
        self.clearMovesets()

        self.setUnverifiedMoveset()
        self.verifyMoveset()
        self.setCaptureset()

        return {"verifiedMoveset": self.verifiedMoveset, "verifiedCaptureset": self.verifiedCaptureset}

    def setCaptureset(self):
        for quadrant in self.unverifiedMoveset.keys():
            for tuplePosition in self.unverifiedMoveset[quadrant]:
                # fixme below
                if self.withinBoardBoundaries(tuplePosition):

                    # Fwd/bckwrd pawn movements are not possible captures
                    if self.pieceName == "pawn" and (quadrant == "up" or quadrant == "down"):
                        pass

                    # End movement as soon as a piece captures opponent piece
                    elif self.tileOccupiedByOpponent(tuplePosition) and not self.pieceName == "knight":
                        self.verifiedCaptureset[quadrant].append(tuplePosition)

                        # Set capturesets to go through king opponent pieces
                        if self.board.getPieceName(tuplePosition) != "king":
                            break
                        else:
                            # Do not go through self king piece
                            if self.tileOccupiedBySelf(tuplePosition):
                                break

                    # Pieces cannot move onto or through a piece containing their own color. However these pieces are
                    # protected
                    elif self.tileOccupiedBySelf(tuplePosition):
                        self.verifiedCaptureset[quadrant].append(tuplePosition)
                        break

                    # Check if each tile is not occupied by self
                    elif not self.tileOccupiedBySelf(tuplePosition):
                        self.verifiedCaptureset[quadrant].append(tuplePosition)

    def pawnOpponentVerification(self, pos, quadrant):
        if self.tileOccupiedBySelf(pos):
            raise Exception(self.pawnOpponentVerification.__name__,
                            "is meant for verification with tiles NOT containing self color pieces.")

        # handle forward movement
        if quadrant == "up" or quadrant == "down":
            # Pass for tiles already containing opponent piece
            if self.board[pos[0]][pos[1]]:
                pass

            # Ensure double steps do not step over an opponent piece
            elif abs(pos[1] - self.position[1]) == 2:
                if self.colorPrefix == "b_":
                    if not self.board[pos[0]][pos[1]]:
                        self.verifiedMoveset[quadrant].append(pos)

                elif self.colorPrefix == "w_":
                    if not self.board[pos[0]][pos[1]]:
                        self.verifiedMoveset[quadrant].append(pos)

            else:
                self.verifiedMoveset[quadrant].append(pos)

        # Append diagonal indices that contain opponent pieces
        elif self.board[pos[0]][pos[1]]:
            self.verifiedMoveset[quadrant].append(pos)

        elif self.enPassantValid(pos):
            self.verifiedMoveset[quadrant].append(pos)

    def enPassantValid(self, pos):
        assert self.pieceName == "pawn", "This method only applies to pawns."

        if self.colorPrefix == "w_" and self.position[1] == 3:
            adjacentTilePos = (pos[0], pos[1] + 1)
            # deleteme
            adjacentPiece = self.board[adjacentTilePos[0]][adjacentTilePos[1]]

            # Allow en passant if an opponent pawn is adjacent (left/right) and they have just performed a double step
            # TODO: recently removed:
            #   adjacentTileX == adjacentPiece.startPos[0]
            #   from elif clause. Thought it was redundant as it is covered by:
            #   self.chessBoard.game.recentDoublestep == adjacentPiece

            # TODO: need to adjust self.chessBoard.game. First need to rebuild the game obj into a lightweight form.`
            #   same goes for the next elif clause.
            if self.tileOccupiedByOpponent(adjacentTilePos) \
                    and self.board.getPieceName(adjacentTilePos) == "pawn" \
                    and self.chessBoard.game.recentDoublestep == adjacentPiece:
                return True

        elif self.colorPrefix == "b_" and self.position[1] == 4:
            adjacentTilePos = (pos[0], pos[1] - 1)
            # deleteme
            adjacentPiece = self.chessBoard.board[adjacentTilePos[0]][adjacentTilePos[1]].currentPiece

            # Allow en passant if an opponent pawn is adjacent (left/right) and they have just performed a double step
            if self.tileOccupiedByOpponent(adjacentTilePos) \
                    and self.board.getPieceName(adjacentTilePos) == "pawn" \
                    and self.chessBoard.game.recentDoublestep == adjacentPiece:
                return True

        return False

    def castlingValid(self):
        queensideCastling = True
        kingsideCastling = True

        if self.pieceName != "king" or not self.unMoved:
            pass
        else:
            leftRookPos = (0, self.position[1])
            rightRookPos = (7, self.position[1])
            for rookPos, castlingBool, startXIndex, maxXIndex in zip([leftRookPos, rightRookPos],
                                                                     [queensideCastling, kingsideCastling],
                                                                     [1, 5],
                                                                     [4, 7]):
                if self.board.getPieceName(rookPos) == "rook" and self.board.getPieceUnmoved(rookPos):
                    xIndex = startXIndex
                    while castlingBool and xIndex < maxXIndex:
                        if self.board[xIndex][self.position[1]]:
                            castlingBool = False
                        xIndex += 1
                    if castlingBool:
                        self.appendCastling(rookPos)

    def appendCastling(self, rookPos):
        if rookPos[0] == 0:
            self.verifiedMoveset["left"].append((2, self.position[1]))
        elif rookPos[0] == 7:
            self.verifiedMoveset["right"].append((6, self.position[1]))

    def tileOccupiedBySelf(self, pos):
        if self.board.getPieceColor(pos) == self.colorPrefix:
            return True
        else:
            return False

    def tileOccupiedByOpponent(self, pos):
        if self.board[pos[0]][pos[1]] and self.board.getPieceColor(pos) != self.colorPrefix:
            return True
        else:
            return False

