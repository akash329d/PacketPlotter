def nonZeroMean(arr):
    """Takes the mean of an array not counting None or 0 values."""
    total = 0
    count = 0
    for x in arr:
        if x is not None and x != 0:
            total, count = total + x, count + 1
    count = 1 if count == 0 else count
    return round(total / count, 2)


def averageArray(array, sliceSize, zeroThreshold, noneThreshold):
    """Averages array over sliceSize timesteps, if the % of zeroes for a specific timestep is lower than
    threshold, the value is set to 0. If the % of None's for a specific timestep is lower than threshold, the value
    is set to None. Return array size will be len(array)//sliceSize"""
    if sliceSize == 1:
        return array

    def averageHelper(i):
        zeroCount = array[i: i + sliceSize].count(0)
        noneCount = array[i: i + sliceSize].count(None)
        if noneCount / sliceSize > noneThreshold:
            return None
        if zeroCount / sliceSize > zeroThreshold:
            return 0
        return nonZeroMean(array[i: i + sliceSize])

    return [averageHelper(i) for i in range(0, len(array), sliceSize)]