from __future__ import print_function

import sys

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import LinearExpr


class SolutionPrinterWithLimit(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions to out problem."""

    def __init__(self, limit, grid, domain, apartments, extra_vars=[]):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__grid = grid
        self.__domain = domain
        self.__apartments = apartments
        self.__solution_count = 0
        self.__solution_limit = limit
        self.__extra_vars = extra_vars

    def on_solution_callback(self):
        self.__solution_count += 1
        self.printSolution()

        if self.__solution_count >= self.__solution_limit:
            print('Stop search after %i solutions' % self.__solution_limit)
            self.StopSearch()

    def printSolution(self, solver=None):
        if(solver is not None):
            self.Value = solver.Value
        for row in self.__grid:
            for cell in row:
                print(self.__domain[self.Value(cell)], end=(" " * (10 - len(self.__domain[self.Value(cell)]))))
            print()
        print()
        for apt in self.__apartments:
            for room in apt:
                print(room['val'])
                print(
                    f'a:({self.Value(room["ax"])},{self.Value(room["ay"])}), b:({self.Value(room["bx"])},{self.Value(room["by"])})')
                print()
        for var in self.__extra_vars:
            print(f'{var} {self.Value(var)}')
        print('****')

    def solution_count(self):
        return self.__solution_count


def isAnd(model, variables, name=None):
    if name is None:
        name = ''
    b = model.NewBoolVar(name)
    model.AddBoolAnd(variables).OnlyEnforceIf(b)
    model.AddBoolOr(list(map(lambda var: var.Not(), variables))).OnlyEnforceIf(b.Not())
    return b


def isOr(model, variables, name=None):
    if name is None:
        name = ''
    b = model.NewBoolVar(name)
    model.AddBoolOr(variables).OnlyEnforceIf(b)
    model.AddBoolAnd(list(map(lambda var: var.Not(), variables))).OnlyEnforceIf(b.Not())
    return b


def isBetween(model, variable, lowerbound, upperbound, name=None):
    lowerbool = model.NewBoolVar('')
    model.Add(lowerbound <= variable).OnlyEnforceIf(lowerbool)
    model.Add(lowerbound > variable).OnlyEnforceIf(lowerbool.Not())

    upperbool = model.NewBoolVar('')
    model.Add(upperbound >= variable).OnlyEnforceIf(upperbool)
    model.Add(upperbound < variable).OnlyEnforceIf(upperbool.Not())

    return isAnd(model, [lowerbool, upperbool], name)


def isEqual(model, variable1, variable2, name=None):
    if name is None:
        name = ''
    equal = model.NewBoolVar(name)
    model.Add(variable1 == variable2).OnlyEnforceIf(equal)
    model.Add(variable1 != variable2).OnlyEnforceIf(equal.Not())
    return equal


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


def roomConstraint(model, room, grid):
    # room =
    # {
    #   'ax':, 'ay':, \\ x and y are the or tool variables representing point a
    #   'bx':, 'by':,
    #   'val': \\ val is the val that is assigned on the grid for this room
    # }

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
            matchCellToRoom(ax, ay, bx, by, cell, colIdx, model, room, rowIdx)


def matchCellToRoom(ax, ay, bx, by, cell, colIdx, model, room, rowIdx):
    inRoom = isAnd(model, [isBetween(model, rowIdx, ax, bx), isBetween(model, colIdx, ay, by)])

    model.Add(cell == domain.index(room['val'])).OnlyEnforceIf(inRoom)
    model.Add(cell != domain.index(room['val'])).OnlyEnforceIf(inRoom.Not())


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


# Adds a Constraint that all rooms should be connected (i.e There is a path from each room to all other rooms)
def enforceComponencyConstraint(model, rooms):
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
    nextList = filter(lambda d: "xxx" in d, domain)
    boolVars = []
    for room in apt:
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
    split = room["val"].split("_")
    type = split[0]
    apt = split[1]
    dict = {"DN": ["K"], "K": ["D"], "MSB": ["D"], "DR": ["BD"], "MNB": ["BD", "D"]}
    if type not in dict: return

    nextList = dict[type]

    for nextElem in nextList:
        assRoom = ""

        if (type == "MNB"):
            assRoom = split[2]
            if (assRoom.startswith("#")): return
        elif (type == "DR"):
            assRoom = split[2]

        adjacentRooms = list(filter(
            lambda x: (
                    (apt in x or "AP" not in x) and
                    (nextElem == x.split("_")[0]) and
                    (assRoom == "" or (len(x) > 1 and assRoom == x.split("_")[2]) or len(x) == 1)),
            domain))

        print(f'{room["val"]} adj to one in {adjacentRooms}')

        boolVars = []

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

                for adjacentRoom in adjacentRooms:
                    # print(domain.index(adjacentRoom))
                    # print(type(cell))
                    isAdjRoom = isEqual(model, cell, domain.index(adjacentRoom))
                    boolVars.append(isAnd(model, [inEdge, isAdjRoom]))
                    # boolVars.append((inEdge))
        model.AddBoolOr(boolVars)


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


def getCountSunRooms(model, apts, grid):
    boolVars = []
    for apt in apts:
        for room in apt:
            boolVars.append(isSunRoom(model, room, grid))
    return getSum(model, boolVars, len(grid) * len(grid[0]))


def aptOpenAreaConstraint(model, apt, onOpenArea, grid):
    boolvars = []
    for room in apt:
        for key, value in onOpenArea.items():
            if value == 0:
                continue
            if key in ["bottom", "top"]:
                boolvars.append(isOnBorder(model, 0 if key == "top" else len(grid) - 1, True, room))
            else:
                boolvars.append(isOnBorder(model, 0 if key == "left" else len(grid[0]) - 1, True, room))
    model.AddBoolOr(boolvars)


def symmetricRooms(model, rooms):
    area = rooms[0]['area']
    for room in rooms:
        model.Add(area == room['area'])


def symmetricApts(model, apts):
    numRooms = len(apts[0])
    for i in range(numRooms):
        symmetricRooms(model, [apt[i] for apt in apts])


# Adds Constraint that the room follows the golden ratio (approximated ratio)
def ensureGoldenRatio(model, room, mx):
    x = model.NewIntVar(0, mx, '')
    y = model.NewIntVar(0, mx, '')
    model.Add(x == room['bx'] - room['ax'] + 1)
    model.Add(y == room['by'] - room['ay'] + 1)
    a = model.NewIntVar(0, mx, '')
    c = model.NewIntVar(0, mx, '')
    model.AddMinEquality(a, [x, y])
    model.AddMaxEquality(c, [x, y])
    model.Add(10 * c == 16 * a)


# Returns a boolean Variable that specifies whether the distance between roomA and roomB is greater than the value
def isDistanceGreaterThan(model, roomA, roomB, value, max):
    dist = getDistance(model, roomA, roomB, max)
    b = model.NewBoolVar('')
    model.Add(dist > value).OnlyEnforceIf(b)
    model.Add(dist <= value).OnlyEnforceIf(b.Not())
    return b


# Returns a boolean Variable that specifies whether the distance between roomA and roomB is less than the value
def isDistanceLessThan(model, roomA, roomB, value, max):
    dist = getDistance(model, roomA, roomB, max)
    b = model.NewBoolVar('')
    model.Add(dist < value).OnlyEnforceIf(b)
    model.Add(dist >= value).OnlyEnforceIf(b.Not())
    return b

def getCountDistanceLessThan(model, roomTuples, max):
    boolVars = []
    for rooma, roomb, val in roomTuples:
        boolVars.append(isDistanceLessThan(model, rooma, roomb, val, max))
    return getSum(model, boolVars, len(roomTuples))

def getCountDistanceGreaterThan(model, roomTuples, max):
    boolVars = []
    for rooma, roomb, val in roomTuples:
        boolVars.append(isDistanceGreaterThan(model, rooma, roomb, val, max))
    return getSum(model, boolVars, len(roomTuples))


def getSum(model, boolVars, max):
    count = model.NewIntVar(0, max, '')
    model.Add(LinearExpr.Sum(boolVars) == count)
    return count


def isBedroom(room):
    split = room["val"].split("_")
    type = split[0]
    return type=='BD'

def isLivingRoom(room):
    split = room["val"].split("_")
    type = split[0]
    return type=='LR'

def isMainBathroom(room):
    split = room["val"].split("_")
    type = split[0]
    return type=='MSB'

# Return an Int Variables that stores the distance between each pair of bedrooms
# max is equal to the maximum possible distance between any two pair of rooms (i.e height+width of floor)
def getPairWiseDistanceBetWeenBedroom(model,rooms , max):
    n = len(rooms)
    max2 = n*n*max;
    sum = model.NewIntVar(0,0,'')
    for i in range(0,n):
        if isBedroom(rooms[i]):
            for j in range(i+1,n):
                if isBedroom(rooms[j]):
                    newSum = model.NewIntVar(0,max2,'')
                    model.Add(newSum==sum+getDistance(model,rooms[i],rooms[j],max))
                    sum = newSum
    return sum

# Return an Int Variables that stores the distance between MainBathroom to all other rooms (Living room is multiplied by a factor of 2)
# max is equal to the maximum possible distance between any two pair of rooms (i.e height+width of floor)
def getPairWiseDistanceToBathRoom(model,rooms , max):
    n = len(rooms)
    max2 = n*n*max;
    sum = model.NewIntVar(0,0,'')
    for i in range(0,n):
        if isMainBathroom(rooms[i]):
            for j in range(0,n):
                if isMainBathroom(rooms[j]):
                    continue
                newSum = model.NewIntVar(0,max2,'')
                factor = 1
                if isLivingRoom(rooms[j]):
                    factor = 2
                model.Add(newSum==sum+factor*getDistance(model,rooms[i],rooms[j],max))
                sum = newSum
    return sum



def sunRoomConstraint(model, room, grid):
    model.AddBoolAnd([isSunRoom(model, room, grid)])


if __name__ == "__main__":
    model = cp_model.CpModel()
    numberOfApartments = int(input("Enter number of apartments: "))
    widthOfBuilding = int(input("Enter width of building(rows): "))
    lengthOfBuilding = int(input("Enter height of building(cols): "))

    onOpenArea = {
        "left": 0, "right": 0, "top": 1, "bottom": 0
    }
    domain = ['D']

    minArea = 2
    apartments = [
        [createRoom("K_AP1_1", minArea), createRoom("BD_AP1_1", minArea), createRoom("BD_AP1_2", minArea)],
        [createRoom("K_AP2_1", minArea), createRoom("K_AP2_2", minArea),
         createRoom("DN_AP2_1", minArea), createRoom("BD_AP2_1", minArea), createRoom("DR_AP2_1", minArea)],
        [createRoom("K_AP3_1", minArea), createRoom("K_AP3_2", minArea),
         createRoom("DN_AP3_1", minArea), createRoom("BD_AP3_1", minArea), createRoom("DR_AP3_1", minArea)],
        [createRoom("BD_AP4_1", minArea), createRoom("MSB_AP4_1", minArea)]
    ]

    corridors = [createRoom(f'xxxxxxxx{i}', 1) for i in range(numberOfApartments)]
    corridors += [createRoom("ELR", 1), createRoom("SW", 1)]

    rooms = [room for apartment in apartments for room in apartment]
    rooms = map(lambda room: room['val'], rooms)
    domain += rooms

    rooms = map(lambda room: room['val'], corridors)
    domain += rooms

    grid = []
    for i in range(widthOfBuilding):
        col = [model.NewIntVar(0, len(domain) - 1, '(' + str(i) + ',' + str(j) + ')')
               for j in range(lengthOfBuilding)]
        grid += [col]

    print(grid)

    for corridor in corridors:
        roomConstraint(model, corridor, grid)

    for apIdx, ap in enumerate(apartments):
        for roomIdx, room in enumerate(ap):
            roomConstraint(model, room, grid)
            if ('SN_' in room['val']):
                sunRoomConstraint(model, room, grid)
            roomAdjacencyConstraint(model, room, grid, domain)

    enforceComponencyConstraint(model, corridors)

    max = len(grid) + len(grid[0])
    countSunRooms = getCountSunRooms(model, apartments, grid)

    distLessThan = [(apartments[0][0],apartments[0][1],6),
                    (apartments[1][0],apartments[1][1],6)]


    distGreaterThan = []

    countLessThan = getCountDistanceLessThan(model, distLessThan, max)
    countGreaterThan = getCountDistanceGreaterThan(model, distGreaterThan, max)

    totalDistBedrooms = getSum(model, [getPairWiseDistanceBetWeenBedroom(model, apt, max) for apt in apartments], max*(len(grid)*len(grid[0])**2))
    totalDistBathrooms = getSum(model, [getPairWiseDistanceToBathRoom(model, apt, max) for apt in apartments], max*(len(grid)*len(grid[0])**2))

    for apt in apartments:
        aptAdjacencyConstraint(model, apt, grid, domain)
        enforceComponencyConstraint(model, apt)
        if (True):  # todo: input from user
            aptOpenAreaConstraint(model, apt, onOpenArea, grid)

    sameTypeApts = [apartments[1], apartments[2]]
    symmetricApts(model, sameTypeApts)

    model.Maximize(countSunRooms + countLessThan + countGreaterThan - totalDistBedrooms - totalDistBathrooms)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.StatusName())
    solution_printer = SolutionPrinterWithLimit(10, grid, domain, apartments+[corridors], [countSunRooms, countLessThan, countGreaterThan, totalDistBedrooms, totalDistBathrooms])
    solution_printer.printSolution(solver)
    #status = solver.SearchForAllSolutions(model, solution_printer)getCount
    #print(solver.StatusName())
