from __future__ import print_function

from ortools.sat.python import cp_model

from constraints import *
from solutionPrinter import SolutionPrinterWithLimit

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
        #[createRoom("K_AP1_1", minArea), createRoom("BD_AP1_1", minArea), createRoom("BD_AP1_2", minArea),
        # createRoom("CR_AP1_1", 1)],
        [createRoom("K_AP2_1", minArea), createRoom("K_AP2_2", minArea),
         createRoom("CR_AP2_1", 1), createRoom("CR_AP2_2", 1), createRoom("CR_AP2_3", 1),
         createRoom("DN_AP2_1", minArea), createRoom("BD_AP2_1", minArea), createRoom("DR_AP2_1", minArea),
         createRoom("MNB_AP2_#2", 1), createRoom("MNB_AP2_1", 1)],
        [createRoom("K_AP3_1", minArea), createRoom("K_AP3_2", minArea),
         createRoom("CR_AP3_1", 1), createRoom("CR_AP3_2", 1), createRoom("CR_AP3_3", 1),
         createRoom("DN_AP3_1", minArea), createRoom("BD_AP3_1", minArea), createRoom("DR_AP3_1", minArea),
         createRoom("MNB_AP3_#2", 1), createRoom("MNB_AP3_1", 1)]  # ,
        # [createRoom("BD_AP4_1", minArea), createRoom("MSB_AP4_1", minArea), createRoom("CR_AP4_1", 1)]
    ]

    corridors = [createRoom(f'xxxxxxxx{i}', 1)
                 for i in range(numberOfApartments)]
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
            if 'CR_' not in room['val']:
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
        enforceComponencyConstraint(model, list(
            filter(lambda room: 'CR' in room['val'], apt)))
        if (True):  # todo: input from user
            aptOpenAreaConstraint(model, apt, onOpenArea, grid)

    # sameTypeApts = [apartments[1], apartments[2]]
    # symmetricApts(model, sameTypeApts)
    ensureApartmentSymmetry(model, apartments[0], apartments[1], 4)

    model.Maximize(countSunRooms + countLessThan +
                   countGreaterThan - totalDistBedrooms - totalDistBathrooms)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.StatusName())
    solution_printer = SolutionPrinterWithLimit(10, grid, domain, apartments + [corridors],
                                                [countSunRooms, countLessThan, countGreaterThan, totalDistBedrooms,
                                                 totalDistBathrooms])
    solution_printer.printSolution(solver)
    # status = solver.SearchForAllSolutions(model, solution_printer)getCount
    # print(solver.StatusName())
