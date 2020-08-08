import numpy as np
from rdp import rdp, pldist


def distance(a, b):
    return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def distancePointLine(linea, lineb, a):
    if linea == lineb:
        return distance(a, linea)
    x_diff = linea[0] - lineb[0]
    y_diff = linea[1] - lineb[1]
    num = abs(y_diff*a[0] - x_diff * a[1] + linea[0] * lineb[1] - linea[1] * lineb[0])
    den = np.sqrt(y_diff ** 2 + x_diff ** 2)
    return num / den


def douglasPeucker(xpoints, ypoints, epsilon):
    maxDistance, index = 0.0, 0
    for x in range(1, len(xpoints) - 1):
        d = distancePointLine([xpoints[0], ypoints[0]], [xpoints[-1], ypoints[-1]], [xpoints[x], ypoints[x]])
        if d > maxDistance:
            index = x
            maxDistance = d
    if maxDistance > epsilon:
        leftResultsX, leftResultsY = douglasPeucker(xpoints[:index], ypoints[:index], epsilon)
        rightResultsX, rightResultsY = douglasPeucker(xpoints[index:], ypoints[index:], epsilon)
        resultsx, resultsy = leftResultsX + rightResultsX, leftResultsY + rightResultsY
    else:
        resultsx = [xpoints[0], xpoints[-1]]
        resultsy = [ypoints[0], ypoints[-1]]

    return resultsx, resultsy

print(douglasPeucker([1, 2, 3, 4, 5, 6, 7],[1, 4, 6, 3, 2, 1, 3], 500))
print(rdp([[1, 1], [2, 4], [3, 6], [4, 3], [5, 2], [6, 1], [7, 3]], epsilon=.1))