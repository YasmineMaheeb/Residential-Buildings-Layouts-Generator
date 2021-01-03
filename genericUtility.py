from ortools.sat.python.cp_model import LinearExpr


def isAnd(model, variables, name=None):
    """returns an OR-Tools variable that holds the result of logical and applied on variables"""
    if name is None:
        name = ''
    b = model.NewBoolVar(name)
    model.AddBoolAnd(variables).OnlyEnforceIf(b)
    model.AddBoolOr(list(map(lambda var: var.Not(), variables))).OnlyEnforceIf(b.Not())
    return b


def isOr(model, variables, name=None):
    """returns an OR-Tools variable that holds the result of logical or applied on variables"""
    if name is None:
        name = ''
    b = model.NewBoolVar(name)
    model.AddBoolOr(variables).OnlyEnforceIf(b)
    model.AddBoolAnd(list(map(lambda var: var.Not(), variables))).OnlyEnforceIf(b.Not())
    return b


def isBetween(model, variable, lowerbound, upperbound, name=None):
    """returns an OR-Tools variable that holds the result of lowerbound <= variable <= upperbound"""
    lowerbool = model.NewBoolVar('')
    model.Add(lowerbound <= variable).OnlyEnforceIf(lowerbool)
    model.Add(lowerbound > variable).OnlyEnforceIf(lowerbool.Not())

    upperbool = model.NewBoolVar('')
    model.Add(upperbound >= variable).OnlyEnforceIf(upperbool)
    model.Add(upperbound < variable).OnlyEnforceIf(upperbool.Not())

    return isAnd(model, [lowerbool, upperbool], name)


def isEqual(model, variable1, variable2, name=None):
    """returns an OR-Tools variable that holds the result of variable1 == variable2"""
    if name is None:
        name = ''
    equal = model.NewBoolVar(name)
    model.Add(variable1 == variable2).OnlyEnforceIf(equal)
    model.Add(variable1 != variable2).OnlyEnforceIf(equal.Not())
    return equal


def getSum(model, boolVars, maxVal):
    """returns an OR-Tools variable that holds the sum of boolVars"""
    count = model.NewIntVar(0, maxVal, '')
    model.Add(LinearExpr.Sum(boolVars) == count)
    return count
