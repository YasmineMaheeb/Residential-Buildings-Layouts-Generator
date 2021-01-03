from genericUtility import *


def getDistance(model, room1, room2, maxVal):
    """Returns an OR-Tools variable that holds the manhattan distance between the centers of room1 and room2"""
    d = model.NewIntVar(0, maxVal, '')

    midXRoom1 = getMid(model, maxVal, room1["ax"], room1["bx"])
    midYRoom1 = getMid(model, maxVal, room1["ay"], room1["by"])
    midXRoom2 = getMid(model, maxVal, room2["ax"], room2["bx"])
    midYRoom2 = getMid(model, maxVal, room2["ay"], room2["by"])

    diffX = model.NewIntVar(0, maxVal, '')
    diffY = model.NewIntVar(0, maxVal, '')

    model.Add(diffX == midXRoom1 - midXRoom2)
    model.Add(diffY == midYRoom1 - midYRoom2)

    absDiffX = model.NewIntVar(0, maxVal, '')
    absDiffY = model.NewIntVar(0, maxVal, '')

    model.AddAbsEquality(absDiffX, diffX)
    model.AddAbsEquality(absDiffY, diffY)

    model.Add(d == absDiffX + absDiffY)

    return d


def getMid(model, maxVal, pointa, pointb):
    """Returns an OR-Tools variable that holds the middle point between pointa and pointb"""
    sum = model.NewIntVar(0, maxVal, '')
    mid = model.NewIntVar(0, maxVal, '')
    model.Add(sum == (pointa + pointb))
    model.AddDivisionEquality(mid, sum, 2)
    return mid


def isBedroom(room):
    split = room["val"].split("_")
    type = split[0]
    return type == 'BD'


def isLivingRoom(room):
    split = room["val"].split("_")
    type = split[0]
    return type == 'LR'


def isMainBathroom(room):
    split = room["val"].split("_")
    type = split[0]
    return type == 'MSB'


def isDistanceLessThan(model, roomA, roomB, value, maxVal):
    """Returns a boolean Variable that specifies whether the distance between roomA and roomB is less than the value"""
    dist = getDistance(model, roomA, roomB, maxVal)
    b = model.NewBoolVar('')
    model.Add(dist < value).OnlyEnforceIf(b)
    model.Add(dist >= value).OnlyEnforceIf(b.Not())
    return b


def isDistanceGreaterThan(model, roomA, roomB, value, maxVal):
    """Returns a boolean Variable that specifies whether the distance between roomA and roomB is greater than the
    value """
    dist = getDistance(model, roomA, roomB, maxVal)
    b = model.NewBoolVar('')
    model.Add(dist > value).OnlyEnforceIf(b)
    model.Add(dist <= value).OnlyEnforceIf(b.Not())
    return b


def isOnBorder(model, border, isHorizontal, room):
    """Returns an OR-Tools variable that is true if room is on the specified border of the apartment"""
    if isHorizontal:
        return isOr(model, [isEqual(model, room['ax'], border), isEqual(model, room['bx'], border)])
    return isOr(model, [isEqual(model, room['ay'], border), isEqual(model, room['by'], border)])


def isSunRoom(model, room, grid):
    """Returns an OR-Tools variable that is true if room is on one of the borders of the apartment"""
    b1 = isOnBorder(model, 0, True, room)
    b2 = isOnBorder(model, 0, False, room)
    b3 = isOnBorder(model, len(grid) - 1, True, room)
    b4 = isOnBorder(model, len(grid[0]) - 1, False, room)
    return isOr(model, [b1, b2, b3, b4])


def isAdjacent(model, u, v, roomA, roomB):
    """Returns a boolean variable that specifies whether roomA is adjacent to roomB"""
    b = model.NewBoolVar('%i %i' % (u, v))
    if u == v:
        model.Add(b == True)
    else:
        b1 = between(model, roomA['ax'], roomA['ay'], roomB)
        b2 = between(model, roomA['bx'], roomA['by'], roomB)
        b1or2 = model.NewBoolVar('')
        model.AddBoolOr([b1, b2]).OnlyEnforceIf(b1or2)
        model.AddBoolAnd([b1.Not(), b2.Not()]).OnlyEnforceIf(b1or2.Not())
        b3 = isDiagonal(model, roomA, roomB)
        b = isAnd(model, [b1or2, b3.Not()])
    return b


def isDiagonal(model, roomA, roomB):
    """Returns a boolean variable that specifies whether roomA and roomB are diagonals to each other
    ROOMA is bounded by points (a,b,c,d) where a is the top left and the b is top right and so on
    similarly, ROOMB is bounded by points (e,f,g,h)"""
    ax = roomA['ax']
    ay = roomA['ay']
    dx = roomA['bx']
    dy = roomA['by']
    bx = ax
    by = dy
    cx = dx
    cy = ay
    ex = roomB['ax']
    ey = roomB['ay']
    hx = roomB['bx']
    hy = roomB['by']
    fx = ex
    fy = hy
    gx = hx
    gy = ey
    return isOr(model, [isbBRa(model, dx, dy, ex, ey),
                        isbBLa(model, cx, cy, fx, fy),
                        isbBRa(model, hx, hy, ax, ay),
                        isbBLa(model, gx, gy, bx, by)])


def isbBRa(model, ax, ay, bx, by):
    """Returns boolean variables that specifies point B is not Bottom Right Point A"""
    b1 = model.NewBoolVar('')
    model.Add(ax == bx - 1).OnlyEnforceIf(b1)
    model.Add(ax != bx - 1).OnlyEnforceIf(b1.Not())
    b2 = model.NewBoolVar('')
    model.Add(ay == by - 1).OnlyEnforceIf(b2)
    model.Add(ay != by - 1).OnlyEnforceIf(b2.Not())
    return isAnd(model, [b1, b2])


def isbBLa(model, ax, ay, bx, by):
    """Returns boolean variables that specifies point B is not Bottom Left Point A"""
    b1 = model.NewBoolVar('')
    model.Add(ax == bx - 1).OnlyEnforceIf(b1)
    model.Add(ax != bx - 1).OnlyEnforceIf(b1.Not())
    b2 = model.NewBoolVar('')
    model.Add(ay == by + 1).OnlyEnforceIf(b2)
    model.Add(ay != by + 1).OnlyEnforceIf(b2.Not())
    return isAnd(model, [b1, b2])


def between(model, px, py, roomQ):
    """Returns boolean variables that specifies if point p lies between roomQ"""
    b1 = model.NewBoolVar('')
    model.Add(roomQ['bx'] + 1 >= px).OnlyEnforceIf(b1)
    model.Add(roomQ['bx'] + 1 < px).OnlyEnforceIf(b1.Not())
    b2 = model.NewBoolVar('')
    model.Add(px >= roomQ['ax'] - 1).OnlyEnforceIf(b2)
    model.Add(px < roomQ['ax'] - 1).OnlyEnforceIf(b2.Not())
    b3 = model.NewBoolVar('')
    model.Add(roomQ['by'] + 1 >= py).OnlyEnforceIf(b3)
    model.Add(roomQ['by'] + 1 < py).OnlyEnforceIf(b3.Not())
    b4 = model.NewBoolVar('')
    model.Add(py >= roomQ['ay'] - 1).OnlyEnforceIf(b4)
    model.Add(py < roomQ['ay'] - 1).OnlyEnforceIf(b4.Not())
    b = model.NewBoolVar('')
    model.AddBoolAnd([b1, b2, b3, b4]).OnlyEnforceIf(b)
    model.AddBoolOr([b1.Not(), b2.Not(), b3.Not(), b4.Not()]).OnlyEnforceIf(b.Not())
    return b
