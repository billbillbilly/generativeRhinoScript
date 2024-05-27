import rhinoscriptsyntax as rs
import random
import os

# draw a set of random curves
xCoordinates = 0 # x coordinate of start point
yCoordinates = 0 # y coordinate of start point
xChange = range(4, 10, 2) # random increase vlaue for x coordiantes
yChange = range(-6, 13, 1) # random swag value for y coordinates
xTemp = 0 # used for
step = 0 # used for indicating the number of curves
moveDistance = 0 # deistance between each curve
curveList = [] # list of curves

while step <= 4: # generate 5 curves
    points = [] # list of points
    for i in range(0, 11, 1): # generate 12 points for each curve
        xCoordinates += random.choice(xChange)
        yCoordinates = (random.choice(yChange)+moveDistance)
        point = rs.CreatePoint(xCoordinates, yCoordinates, 0)
        points += [point]
    curve = rs.AddCurve(points,3)
    curveList += [curve]
    step += 1
    xCoordinates = 0
    moveDistance = step*20 # there is 20 between each curve

# generate close curves with the line structrues
scaleCurve = range(-12, 26, 1) # this set of values allows close curves to expand and then shrink
scaleCurve.pop(12) # remove 0
centerLine = rs.AddLine(rs.CurveStartPoint(curveList[0]), rs.CurveEndPoint(curveList[-1])) # diagonal
lineDomain = rs.CurveDomain(centerLine)
curvesCneter = rs.EvaluateCurve(centerLine, lineDomain[1]/2) # center point of the diagonal, which is also the center point of the whole structure
for i in curveList: # read each curve
    currentIndex = curveList.index(i) # get the index of current curve in the list of curves
    nextIndex = currentIndex + 1 # get the index of the next curve to call the next curve
    if currentIndex < curveList.index(curveList[-1]): # stop at the last second curve
        curve_points1 = rs.AddPoints(rs.DivideCurve(i, 10, False, True)) # get points on current curve
        curve_points2 = rs.AddPoints(rs.DivideCurve(curveList[nextIndex], 10, False, True)) # get points on the next curve
        for j in curve_points1:
            thisPointIndex = curve_points1.index(j)
            nextPointIndex = thisPointIndex + 1
            if thisPointIndex < curve_points1.index(curve_points1[-1]): # get edit points for each close curve
                thisPoint1 = curve_points1[thisPointIndex]
                nextPoint1 = curve_points1[nextPointIndex]
                thisPoint2 = curve_points2[thisPointIndex]
                nextPoint2 = curve_points2[nextPointIndex]
                shape = rs.AddCurve((thisPoint1,thisPoint2,nextPoint2,nextPoint1, thisPoint1))
                center = rs.CurveAreaCentroid(shape)[0] # the conter point of each curve
                centerZ = 0 # define the height of the close cirve
                centerChange = range(-3, 7, 1) ## swag range for rough surface
                #centerChange = range(-12, 25, 1) ## swag range for smooth surface
                shapeList = []
                rotation = 0 # the overall rotation
                for each in range(0, 24, 1): # generate 24 layers of close curves
                    centerX = center[0] + random.choice(centerChange) # randomly swag cneter points
                    centerY = center[1] + random.choice(centerChange) # randomly swag cneter points
                    #centerX = center[0] + centerChange[each]/3 # ragularly swag center points
                    #centerY = center[1] + centerChange[each]/3 # ragularly swag center points
                    centerZ += 10 # elevate the curves
                    rotation += 10 # rotate the conter ponit based on overall center point
                    newCenter = rs.CreatePoint(centerX, centerY, centerZ) # the new center point for generating curves
                    rs.RotateObject(newCenter, curvesCneter, rotation, None, False) # overally rotate the conter ponit
                    translation = newCenter - center
                    scaled_duplicate = rs.ScaleObject(shape, center, (abs(scaleCurve[each]/6),abs(scaleCurve[each]/11),1))
                    scaled_duplicate = rs.RotateObject(shape, center, each*10, None, False)
                    copyedShape = rs.CopyObject(scaled_duplicate, translation)
                    shapeList += [copyedShape]
                    rs.RotateObject(shape, center, -each*10, None, False)
                    rs.ScaleObject(shape, center, (1/abs(scaleCurve[each]/6),1/abs(scaleCurve[each]/11),1))
                rs.AddLoftSrf(shapeList)
