from genericUtility import *


def getDistance(model, room1, room2, max):
    d = model.NewIntVar(0, max, '')

    midXRoom1 = getMid(model, max, room1["ax"], room1["bx"])
    midYRoom1 = getMid(model, max, room1["ay"], room1["by"])
    midXRoom2 = getMid(model, max, room2["ax"], room2["bx"])
    midYRoom2 = getMid(model, max, room2["ay"], room2["by"])

    diffX = model.NewIntVar(0, max, '')
    diffY = model.NewIntVar(0, max, '')

    model.Add(diffX == midXRoom1 - midXRoom2)
    model.Add(diffY == midYRoom1 - midYRoom2)

    absDiffX = model.NewIntVar(0, max, '')
    absDiffY = model.NewIntVar(0, max, '')

    model.AddAbsEquality(absDiffX, diffX)
    model.AddAbsEquality(absDiffY, diffY)

    model.Add(d == absDiffX + absDiffY)

    return d


def getMid(model, max, pointa, pointb):
    sum = model.NewIntVar(0, max, '')
    mid = model.NewIntVar(0, max, '')
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


# Returns a boolean Variable that specifies whether the distance between roomA and roomB is less than the value
def isDistanceLessThan(model, roomA, roomB, value, max):
    dist = getDistance(model, roomA, roomB, max)
    b = model.NewBoolVar('')
    model.Add(dist < value).OnlyEnforceIf(b)
    model.Add(dist >= value).OnlyEnforceIf(b.Not())
    return b


# Returns a boolean Variable that specifies whether the distance between roomA and roomB is greater than the value
def isDistanceGreaterThan(model, roomA, roomB, value, max):
    dist = getDistance(model, roomA, roomB, max)
    b = model.NewBoolVar('')
    model.Add(dist > value).OnlyEnforceIf(b)
    model.Add(dist <= value).OnlyEnforceIf(b.Not())
    return b


def isOnBorder(model, border, isHorizontal, room):
    if (isHorizontal):
        return isOr(model, [isEqual(model, room['ax'], border), isEqual(model, room['bx'], border)])
    return isOr(model, [isEqual(model, room['ay'], border), isEqual(model, room['by'], border)])


def isSunRoom(model, room, grid):
    b1 = isOnBorder(model, 0, True, room)
    b2 = isOnBorder(model, 0, False, room)
    b3 = isOnBorder(model, len(grid) - 1, True, room)
    b4 = isOnBorder(model, len(grid[0]) - 1, False, room)
    return isOr(model, [b1, b2, b3, b4])


# Returns a boolean variable that specifies whether roomA is adjacent to roomB
def isAdjacent(model, u, v, roomA, roomB):
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


# Returns a boolean variable that specifies whether roomA and roomB are diagonals to each other
# ROOMA is bounded by points (a,b,c,d) where a is the top left and the b is top right and so on
# similarily, ROOMB is bounded by points (e,f,g,h)
def isDiagonal(model, roomA, roomB):
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


# Returns boolean variables that specifies point B is not Bottom Right Point A
def isbBRa(model, ax, ay, bx, by):
    b1 = model.NewBoolVar('')
    model.Add(ax == bx - 1).OnlyEnforceIf(b1)
    model.Add(ax != bx - 1).OnlyEnforceIf(b1.Not())
    b2 = model.NewBoolVar('')
    model.Add(ay == by - 1).OnlyEnforceIf(b2)
    model.Add(ay != by - 1).OnlyEnforceIf(b2.Not())
    return isAnd(model, [b1, b2])


# Returns boolean variables that specifies point B is not Bottom Left Point A
def isbBLa(model, ax, ay, bx, by):
    b1 = model.NewBoolVar('')
    model.Add(ax == bx - 1).OnlyEnforceIf(b1)
    model.Add(ax != bx - 1).OnlyEnforceIf(b1.Not())
    b2 = model.NewBoolVar('')
    model.Add(ay == by + 1).OnlyEnforceIf(b2)
    model.Add(ay != by + 1).OnlyEnforceIf(b2.Not())
    return isAnd(model, [b1, b2])


# Returns boolean variables that specifies if point p lies between roomQ
def between(model, px, py, roomQ):
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
