from __future__ import print_function

from ortools.sat.python import cp_model

from constraints import *
from solutionPrinter import SolutionPrinterWithLimit

if __name__ == "__main__":
    model = cp_model.CpModel()
    numberOfApartments = int(input("Enter number of apartments: "))
    widthOfBuilding = int(input("Enter width of building(rows): "))
    lengthOfBuilding = int(input("Enter height of building(cols): "))
    print("You will be asked some questions answer by y/n")
    isOpenWall = [0,0,0,0]
    for i in range(4):
        isOpenWall[i] = "y" in input("is the wall number "+ str(i+1)+ " on an open area: ")

    onOpenArea = {
        "left": isOpenWall[0], "right": isOpenWall[1], "top": isOpenWall[2], "bottom": isOpenWall[3]
    }

    domain = ['D']

    allApartmentsOnOpenArea = "y" in input("Should all apartments have look on landscape view? ")
    allEqualDistanceToElev = "y" in input("Should all apartments be of an equal distance to the elevators unit? ")
    symmetricApartements = "y" in input("Should apartments of same type be symmetric? ")

    divPropRooms = []
    sameTypePairs = []
    numberOfPairs = int(input("Please enter number of same type apartment pairs: "))
    for i in range(numberOfPairs):
        print("Pair number "+str(i+1))
        x = int(input("Please enter id (1 indexed) of first apartment in the pair: ")) -1
        y = int(input("Please enter id (1 indexed) of second apartment in the pair: ")) -1
        sameTypePairs.append([x,y])

    apartments = []
    for i in range (numberOfApartments):
        numberOfRooms = int(input("Please enter the number of rooms of apartment number "+str(i+1)+": "))
        curRooms = []
        for j in range(numberOfRooms):
            curRoomName = input("Please enter room code for room number "+str(j+1)+":")
            curMinArea = int(input("Please enter minimum area for room number "+str(j+1)+":"))
            curMinHeight = int(input("Please enter minimum height for room number "+str(j+1)+":"))
            curMinWidth = int(input("Please enter minimum width for room number "+str(j+1)+":"))
            curRoom = createRoom(curRoomName,curMinArea,curMinHeight,curMinWidth)
            curRooms.append(curRoom)

            divineProportion = "y" in input(
                "Should we aim to allocate spaces with ratios following the divine proportion for this room? ")
            if (divineProportion): divPropRooms.append(curRoom)

        apartments.append(curRooms)


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


    for corridor in corridors:
        roomConstraint(model, corridor, grid, domain)

    for apIdx, ap in enumerate(apartments):
        for roomIdx, room in enumerate(ap):
            roomConstraint(model, room, grid, domain)
            if 'SN_' in room['val']:
                sunRoomConstraint(model, room, grid)
            roomAdjacencyConstraint(model, room, grid, domain)

    enforceComponencyConstraint(model, corridors)

    max = len(grid) + len(grid[0])
    countSunRooms = getCountSunRooms(model, apartments, grid)

    distLessThan = []
    numberDistanceLessThanPairs = int(
        input("Please enter the number of room pairs for which you want to specify distance less than: "))

    for i in range(numberDistanceLessThanPairs):
        apartmentId = int(input("please enter apartment Id (1 indexed) for the pair number " +str(i+1)+": "))-1
        x = int(input("please enter room Id (1 indexed) for the first room: "))-1
        y = int(input("please enter room Id (1 indexed) for the second room: "))-1
        d = int(input("please enter the distance: "))
        distLessThan.append((apartments[apartmentId][x],apartments[apartmentId][y],d))

    distGreaterThan = []
    numberDistanceGreaterThanPairs = int(
        input("Please enter the number of room pairs for which you want to specify distance greater than: "))

    for i in range(numberDistanceGreaterThanPairs):
        apartmentId = int(input("please enter apartment Id (1 indexed) for the pair number " + str(i + 1)+": ")) - 1
        x = int(input("please enter room Id (1 indexed) for the first room: ")) - 1
        y = int(input("please enter room Id (1 indexed) for the second room: ")) - 1
        d = int(input("please enter the distance: "))
        distGreaterThan.append((apartments[apartmentId][x], apartments[apartmentId][y],d))

    countLessThan = getCountDistanceLessThan(model, distLessThan, max)
    countGreaterThan = getCountDistanceGreaterThan(model, distGreaterThan, max)

    totalDistBedrooms = getSum(model, [getPairWiseDistanceBetWeenBedroom(model, apt, max) for apt in apartments],
                               max * (len(grid) * len(grid[0]) ** 2))
    totalDistBathrooms = getSum(model, [getPairWiseDistanceToBathRoom(model, apt, max) for apt in apartments],
                                max * (len(grid) * len(grid[0]) ** 2))

    for apt in apartments:
        aptAdjacencyConstraint(model, apt, grid, domain)
        enforceComponencyConstraint(model, apt)
        if (allApartmentsOnOpenArea):
            aptOpenAreaConstraint(model, apt, onOpenArea, grid)



    midX = lengthOfBuilding //2 
    if (symmetricApartements):
        for pair in sameTypePairs:
            ensureApartmentSymmetry(model,apartments[pair[0]],apartments[pair[1]], midX)


    if (allEqualDistanceToElev):
        ensureEqualDistanceToElevator(model,apartments,corridors[numberOfApartments],widthOfBuilding+lengthOfBuilding)

    for room in divPropRooms:
        ensureGoldenRatio(model, room, widthOfBuilding+lengthOfBuilding)

    model.Maximize(countSunRooms + countLessThan + countGreaterThan - totalDistBedrooms - totalDistBathrooms)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.StatusName())
    solution_printer = SolutionPrinterWithLimit(10, grid, domain, apartments + [corridors],
                                                [countSunRooms, countLessThan, countGreaterThan, totalDistBedrooms,
                                                 totalDistBathrooms])
    solution_printer.printSolution(solver)
    # status = solver.SearchForAllSolutions(model, solution_printer)getCount
    # print(solver.StatusName())
