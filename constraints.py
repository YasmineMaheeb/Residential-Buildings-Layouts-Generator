from roomUtility import *


def roomConstraint(model, room, grid, domain):
    """initializes the room object with OR-Tools variables, and adds a constraint that ensures they match the grid"""

    minArea = room['minArea']
    minHeight = room['minHeight']
    minWidth = room['minWidth']

    gridW = len(grid)
    gridH = len(grid[0])

    for point in ['ax', 'ay', 'bx', 'by']:
        if room[point] is None:
            room[point] = model.NewIntVar(0, gridW - 1, room['val'] + point)

    ax = room['ax']
    ay = room['ay']
    bx = room['bx']
    by = room['by']
    print(minHeight)
    print(gridH)
    print()
    height = model.NewIntVar(minHeight, gridH, '')
    width = model.NewIntVar(minWidth, gridW, '')
    area = model.NewIntVar(minArea, gridH * gridW, '')

    room['area'] = area
    model.Add(height == by - ay + 1)
    model.Add(width == bx - ax + 1)
    model.AddMultiplicationEquality(area, [width, height])

    for rowIdx, row in enumerate(grid):
        for colIdx, cell in enumerate(row):
            # grid val == this room if and only if the index of this cell is inside the room
            matchCellToRoom(ax, ay, bx, by, cell, colIdx, model, room, rowIdx, domain)


def matchCellToRoom(ax, ay, bx, by, cell, colIdx, model, room, rowIdx, domain):
    inRoom = isAnd(model, [isBetween(model, rowIdx, ax, bx), isBetween(model, colIdx, ay, by)])

    model.Add(cell == domain.index(room['val'])).OnlyEnforceIf(inRoom)
    model.Add(cell != domain.index(room['val'])).OnlyEnforceIf(inRoom.Not())


def enforceComponencyConstraint(model, rooms):
    """Adds a Constraint that all rooms should be connected (i.e There is a path from each room to all other rooms)"""
    n = len(rooms)
    path = [None for y in range(n)]
    initial = []
    for x in range(n):
        path[x] = [None for y in range(n)]
        for y in range(n):
            path[x][y] = isAdjacent(model, x, y, rooms[x], rooms[y])
            initial.append(path[x][y])

    for k in range(n):
        for u in range(n):
            for v in range(n):
                b = model.NewBoolVar('')
                model.AddBoolAnd([path[u][k], path[k][v]]).OnlyEnforceIf(b)
                model.AddBoolOr([path[u][k].Not(), path[k][v].Not()]).OnlyEnforceIf(b.Not())
                b2 = model.NewBoolVar('')
                model.AddBoolOr([b, path[u][v]]).OnlyEnforceIf(b2)
                model.AddBoolAnd([b.Not(), path[u][v].Not()]).OnlyEnforceIf(b2.Not())
                path[u][v] = b2

    final = []
    for u in range(n):
        for v in range(n):
            final.append(path[u][v])

    model.AddBoolAnd(final)


def aptAdjacencyConstraint(model, apt, grid, domain):
    """adds a constraint that one corridor in apt must be adjacent to one hallway"""
    nextList = filter(lambda d: "xxx" in d, domain)
    boolVars = []
    corridors = filter(lambda x: "CR" in x['val'], apt)
    for room in corridors:
        for nextElem in nextList:
            upperX = model.NewIntVar(-1, len(grid), '')
            model.Add(upperX == room['ax'] - 1)

            lowerX = model.NewIntVar(-1, len(grid), '')
            model.Add(lowerX == room['bx'] + 1)

            rightY = model.NewIntVar(-1, len(grid[0]), '')
            model.Add(rightY == room['by'] + 1)

            leftY = model.NewIntVar(-1, len(grid[0]), '')
            model.Add(leftY == room['ay'] - 1)

            for rowIdx, row in enumerate(grid):
                for colIdx, cell in enumerate(row):
                    rowIsLower = isEqual(model, rowIdx, lowerX)
                    rowIsUpper = isEqual(model, rowIdx, upperX)
                    colIsLeft = isEqual(model, colIdx, leftY)
                    colIsRight = isEqual(model, colIdx, rightY)
                    inEdge = isOr(model, [
                        isAnd(model,
                              [isOr(model, [rowIsLower, rowIsUpper]), isBetween(model, colIdx, leftY + 1, rightY - 1)]),
                        isAnd(model,
                              [isOr(model, [colIsLeft, colIsRight]), isBetween(model, rowIdx, upperX + 1, lowerX - 1)])
                    ])

                    isAdjRoom = isEqual(model, cell, domain.index(nextElem))
                    boolVars.append(isAnd(model, [inEdge, isAdjRoom]))
    model.AddBoolOr(boolVars)


def roomAdjacencyConstraint(model, room, grid, domain):
    """adds a constraint the ensures that every room is adjacent to what it needs to be adjacent too,
    depending on the input."""
    split = room["val"].split("_")
    roomType = split[0]
    apt = split[1]
    adjDict = {"DN": ["K"], "K": ["D"], "MSB": ["D"], "DR": ["BD"], "MNB": ["BD", "D"]}
    if roomType in adjDict:
        nextList = adjDict[roomType]
    else:
        nextList = []

    if (roomType != "MNB" or split[2].startswith("#")) and roomType != "DR":
        nextList.append("CR")

    if split[2].startswith("#"):
        nextList.remove("BD")

    boolVars = [[] for nextElem in nextList]

    upperX = model.NewIntVar(-1, len(grid), '')
    model.Add(upperX == room['ax'] - 1)

    lowerX = model.NewIntVar(-1, len(grid), '')
    model.Add(lowerX == room['bx'] + 1)

    rightY = model.NewIntVar(-1, len(grid[0]), '')
    model.Add(rightY == room['by'] + 1)

    leftY = model.NewIntVar(-1, len(grid[0]), '')
    model.Add(leftY == room['ay'] - 1)

    for rowIdx, row in enumerate(grid):
        for colIdx, cell in enumerate(row):
            rowIsLower = isEqual(model, rowIdx, lowerX)
            rowIsUpper = isEqual(model, rowIdx, upperX)
            colIsLeft = isEqual(model, colIdx, leftY)
            colIsRight = isEqual(model, colIdx, rightY)
            inEdge = isOr(model, [
                isAnd(model,
                      [isOr(model, [rowIsLower, rowIsUpper]), isBetween(model, colIdx, leftY + 1, rightY - 1)]),
                isAnd(model,
                      [isOr(model, [colIsLeft, colIsRight]), isBetween(model, rowIdx, upperX + 1, lowerX - 1)])
            ])

            for elemIdx, nextElem in enumerate(nextList):
                assRoom = ""

                if roomType == "MNB" and nextElem == "BD":
                    assRoom = split[2]
                elif roomType == "DR":
                    assRoom = split[2]

                adjacentRooms = list(filter(
                    lambda x: (
                            (apt in x or "AP" not in x) and
                            (nextElem == x.split("_")[0]) and
                            (assRoom == "" or (len(x) > 1 and assRoom == x.split("_")[2]) or len(x) == 1)),
                    domain))
                if rowIdx == 0 and colIdx == 0:
                    print(f'{room["val"]} adj to one in {adjacentRooms}')

                for adjacentRoom in adjacentRooms:
                    # print(domain.index(adjacentRoom))
                    # print(type(cell))
                    isAdjRoom = isEqual(model, cell, domain.index(adjacentRoom))
                    boolVars[elemIdx].append(isAnd(model, [inEdge, isAdjRoom]))
                    # boolVars.append((inEdge))
    for boolVarList in boolVars:
        model.AddBoolOr(boolVarList)


def createRoom(val, minArea, minHeight=0, minWidth=0, ax=None, ay=None, bx=None, by=None):
    return {
        "val": val,
        "minArea": minArea,
        "minHeight": minHeight,
        "minWidth": minWidth,
        "ax": ax,
        "ay": ay,
        "bx": bx,
        "by": by
    }


def getCountSunRooms(model, apts, grid):
    """Returns an OR-Tools variable that holds the count of sun rooms"""
    boolVars = []
    for apt in apts:
        for room in apt:
            boolVars.append(isSunRoom(model, room, grid))
    return getSum(model, boolVars, len(grid) * len(grid[0]))


def aptOpenAreaConstraint(model, apt, onOpenArea, grid):
    """adds a constraint that ensures an apt is on an open area"""
    boolvars = []
    for room in apt:
        for key, value in onOpenArea.items():
            if value == 0:
                continue
            if key in ["bottom", "top"]:
                boolvars.append(isOnBorder(model, 0 if key == "top" else len(grid) - 1, True, room))
            else:
                boolvars.append(isOnBorder(model, 0 if key == "left" else len(grid[0]) - 1, False, room))
    model.AddBoolOr(boolvars)


def symmetricRooms(model, rooms):
    area = rooms[0]['area']
    for room in rooms:
        model.Add(area == room['area'])


# deprecated?
def symmetricApts(model, apts):
    numRooms = len(apts[0])
    for i in range(numRooms):
        symmetricRooms(model, [apt[i] for apt in apts])


def ensureGoldenRatio(model, room, mx):
    """Adds Constraint that the room follows the golden ratio (approximated ratio)"""
    x = model.NewIntVar(0, mx, '')
    y = model.NewIntVar(0, mx, '')
    model.Add(x == room['bx'] - room['ax'] + 1)
    model.Add(y == room['by'] - room['ay'] + 1)
    a = model.NewIntVar(0, mx, '')
    c = model.NewIntVar(0, mx, '')
    model.AddMinEquality(a, [x, y])
    model.AddMaxEquality(c, [x, y])
    model.Add(10 * c == 16 * a)


def getCountDistanceLessThan(model, roomTuples, maxVal):
    """Returns an OR-Tools variable hold the count of tuples in roomTuples that satisfy the condition"""
    boolVars = []
    for rooma, roomb, val in roomTuples:
        boolVars.append(isDistanceLessThan(model, rooma, roomb, val, maxVal))
    return getSum(model, boolVars, len(roomTuples))


def getCountDistanceGreaterThan(model, roomTuples, maxVal):
    """Returns an OR-Tools variable hold the count of tuples in roomTuples that satisfy the condition"""
    boolVars = []
    for rooma, roomb, val in roomTuples:
        boolVars.append(isDistanceGreaterThan(model, rooma, roomb, val, maxVal))
    return getSum(model, boolVars, len(roomTuples))


def getPairWiseDistanceBetWeenBedroom(model, rooms, maxVal):
    """Return an Int Variables that stores the distance between each pair of bedrooms
    max is equal to the maximum possible distance between any two pair of rooms (i.e height+width of floor)"""
    n = len(rooms)
    max2 = n * n * maxVal
    sumVal = model.NewIntVar(0, 0, '')
    for i in range(0, n):
        if isBedroom(rooms[i]):
            for j in range(i + 1, n):
                if isBedroom(rooms[j]):
                    newSum = model.NewIntVar(0, max2, '')
                    model.Add(newSum == sumVal + getDistance(model, rooms[i], rooms[j], maxVal))
                    sumVal = newSum
    return sumVal


def getPairWiseDistanceToBathRoom(model, rooms, maxVal):
    """Return an Int Variables that stores the distance between MainBathroom to all other rooms (Living room is
    multiplied by a factor of 2) max is equal to the maximum possible distance between any two pair of rooms
    (i.e height+width of floor)"""
    n = len(rooms)
    max2 = n * n * maxVal
    sumVal = model.NewIntVar(0, 0, '')
    for i in range(0, n):
        if isMainBathroom(rooms[i]):
            for j in range(0, n):
                if isMainBathroom(rooms[j]):
                    continue
                newSum = model.NewIntVar(0, max2, '')
                factor = 1
                if isLivingRoom(rooms[j]):
                    factor = 2
                model.Add(newSum == sumVal + factor * getDistance(model, rooms[i], rooms[j], maxVal))
                sumVal = newSum
    return sumVal


def sunRoomConstraint(model, room, grid):
    model.AddBoolAnd([isSunRoom(model, room, grid)])


def ensureEqualDistanceToElevator(model, apartments, elevatorRoom, maxVal):
    """Adds a constraint that the minimum distance between all apartments and the elevator room is equal."""
    last = None
    mxVar = model.NewIntVar(maxVal, maxVal, '')
    for ap in range(0, len(apartments)):
        distances = [mxVar]
        for room in apartments[ap]:
            distances.append(getDistance(model, room, elevatorRoom, maxVal))
        curMinDist = model.NewIntVar(0, maxVal, '')
        model.AddMinEquality(curMinDist, distances)
        if ap == 0:
            last = curMinDist
        else:
            model.Add(last == curMinDist)


def ensureApartmentSymmetry(model, apartment1, apartment2, midX):
    """Ensures that two apartments are symmetrical along the y-axis
    (MAKE SURE THAT THE ORDER IN THE LIST IS THE SAME)"""
    n = len(apartment1)
    for i in range(n):
        room1 = apartment1[i]
        room2 = apartment2[i]
        model.Add(room2['ay'] - midX == midX - room1['by'])
        model.Add(midX - room1['ay'] == room2['by'] - midX)
        model.Add(room2['ax'] == room1['ax'])
        model.Add(room2['bx'] == room1['bx'])
