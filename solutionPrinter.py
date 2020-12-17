from ortools.sat.python import cp_model


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
        if solver is not None:
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
