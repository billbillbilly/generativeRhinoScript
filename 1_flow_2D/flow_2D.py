import rhinoscriptsyntax as rs
import random
import os
import math

# set the size of grid
x_number = rs.GetInteger(message="set the number of point on x direction", number=30)
y_number = rs.GetInteger(message="set the number of point on y direction",number=30)
# set interval
interval = rs.GetInteger(message="set the interval",number=6)
# generate a set of points
points = []
for i in range(1,x_number):
    for j in range(1,y_number):
        point = rs.CreatePoint(i*interval, j*interval, 0)
        addpoint = rs.AddPoint((i*interval, j*interval, 0))
        points += [point]

# indicate the number of curves that will be created
num_curves = rs.GetInteger(message="set the number of curves")
if num_curves == 1:
    # pick up some generated points to create a cerve
    selected_points = rs.GetObjects(message="select points", filter=1, group=False)
    curve_guid = rs.AddCurve(selected_points,3)
    # sample points along the curve
    curve_length = rs.CurveLength(curve_guid)
    curve_points_list = rs.DivideCurve(curve_guid, round(curve_length), False, True)
else:
    curve_points_list = []
    curve_endpoint = []
    n = 0
    while n < num_curves:
        selected_points = rs.GetObjects(message="select points", filter=1, group=False)
        curve_guid = rs.AddCurve(selected_points,3)
        curve_length = rs.CurveLength(curve_guid)
        points_along_curve = rs.DivideCurve(curve_guid, round(curve_length), False, True)
        curve_points_list += points_along_curve
        # collect end point of each curve
        curve_endpoint += points_along_curve[-1]
        n += 1

# create a set of circles
for i in points:
    # calculate min distance from the point to the curve
    min_distance = min(rs.Distance(i, curve_points_list))
    if min_distance > 3:
        # the radius of a circle is based on the distance from each point to the curve
        radius = math.sqrt(min_distance/4)
        if num_curves == 1:
            radius_change = rs.Distance(i, curve_points_list[-1])
        else:
            radius_change = min(rs.Distance(i, curve_endpoint))
        # the radius will be also infulenced by the distance from the point to the end points of curves
        radius -= 2*radius*radius/radius_change
        circle = rs.AddCircle(i, radius)
        for j in curve_points_list:
            distance = rs.Distance(i, j)
            # select the closest point on the curve
            if distance == min_distance:
                # find the index of current point on the curve
                this_point_index = curve_points_list.index(j)
                curve_distance = []
                closest_point = 0
                # find the closest point of the current point
                for p in curve_points_list:
                    if j != p:
                        curve_distance += [rs.Distance(j, p)]
                for p in curve_points_list:
                    if min(curve_distance) == rs.Distance(j, p):
                        closest_point = p
                # find the index of the closest point
                closest_point_index = curve_points_list.index(closest_point)
                # figure out the direction of the curve at each point
                if this_point_index > closest_point_index:
                    if (this_point_index+1) < len(curve_points_list):
                            if rs.Distance(j, curve_points_list[this_point_index+1]) < 2*min(curve_distance):
                                direction_line = rs.AddLine(j, curve_points_list[this_point_index+1])
                                translation = i - j
                            else:
                                direction_line = rs.AddLine(closest_point, j)
                                translation = i - closest_point
                    else:
                        direction_line = rs.AddLine(closest_point, j)
                        translation = i - closest_point
                elif this_point_index < closest_point_index:
                    direction_line = rs.AddLine(j, closest_point)
                    translation = i - j
                # assign this direction to the center point of circle
                rs.MoveObject(direction_line, translation)
                # extend the direction based on the distance from center point of circle to current point on the curve
                extened_direction_line = rs.ExtendCurveLength(direction_line, extension_type=0, side=1, length=min(curve_distance)*min(curve_distance)/min_distance)
                end_point = rs.CurveEndPoint(extened_direction_line)
                translation2 = end_point - i
                # move the circle to the end point of extended direction
                moved_circle = rs.MoveObject(circle, translation2)
                #rs.DeleteObject(direction_line)
