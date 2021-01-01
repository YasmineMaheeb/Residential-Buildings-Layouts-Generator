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
    divineProportion = "y" in input("Should we aim to allocate spaces with ratios following the divine proportion? ")

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
            curMinArea = input("Please enter minimum area for room number "+str(j+1)+":")
            curMinHeight = input("Please enter minimum height for room number "+str(j+1)+":")
            curMinWidth = input("Please enter minimum width for room number "+str(j+1)+":")
            curRooms.append(createRoom(curRoomName,curMinArea,curMinHeight,curMinWidth))
        apartments.append(curRooms)
    # print(apartments)all apartments have look on landscape view

    # minArea = 2
    # apartments = [
    #     [createRoom("K_AP1_1", minArea), createRoom("BD_AP1_1", minArea), createRoom("BD_AP1_2", minArea)],
    #     [createRoom("K_AP2_1", minArea), createRoom("K_AP2_2", minArea),
    #      createRoom("DN_AP2_1", minArea), createRoom("BD_AP2_1", minArea), createRoom("DR_AP2_1", minArea)],
    #     [createRoom("K_AP3_1", minArea), createRoom("K_AP3_2", minArea),
    #      createRoom("DN_AP3_1", minArea), createRoom("BD_AP3_1", minArea), createRoom("DR_AP3_1", minArea)],
    #     [createRoom("BD_AP4_1", minArea), createRoom("MSB_AP4_1", minArea)]
    # ]

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

    distLessThan = [(apartments[0][0], apartments[0][1], 6),
                    (apartments[1][0], apartments[1][1], 6)]

    distGreaterThan = []

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

    # sameTypeApts = [apartments[1], apartments[2]]
    # symmetricApts(model, sameTypeApts)

    midX = 4 #TODO change dynamically
    if (symmetricApartements):
        for pair in sameTypePairs:
            ensureApartmentSymmetry(model,apartments[pair[0]],apartments[pair[1]], midX)

    # if (divineProportion):


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
