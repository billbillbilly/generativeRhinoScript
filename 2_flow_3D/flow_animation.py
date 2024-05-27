import rhinoscriptsyntax as rs
import Rhino as rh
import random
import os
import math

# generate a set of points
def pointsetup(x_number, y_number, interval):
    points = {}
    point_list = []
    for i in range(1,x_number):
        for j in range(1,y_number):
            point = rs.AddPoint((i*interval, j*interval, 0))
            point_list += [point]
            points[(i, j)] = (i*interval, j*interval, 0)
    return points, point_list

# get points along multiple curves
def pointsoncurve(num_curves):
    curve_points_dic = {}
    n = 0
    while n < num_curves:
        curve_points_list = []
        selected_points = rs.GetObjects(message="select points", filter=1, group=False)
        curve_guid = rs.AddCurve(selected_points,3)
        curve_length = rs.CurveLength(curve_guid)
        points_along_curve = rs.DivideCurve(curve_guid, round(curve_length), False, True)
        curve_points_list += points_along_curve
        curve_points_dic[n] = curve_points_list
        rs.DeleteObject(curve_guid)
        n += 1
    return curve_points_dic

def animate(folder, sequence_num):
    f_path = folder + "{}.png".format(int(sequence_num))
    rs.Command("_-ViewCaptureToFile " + f_path + " _Enter")

def main():
    # set the size of grid
    x_number = rs.GetInteger(message="set the number of point on x direction")
    y_number = rs.GetInteger(message="set the number of point on y direction")
    # set interval
    interval = rs.GetInteger(message="set the interval")
    # indicate the number of curves that will be created
    num_curves = rs.GetInteger(message="set the number of curves")

    points, point_list = pointsetup(x_number, y_number, interval)
    curve_points_dic = pointsoncurve(num_curves)

    save_folder = '/Users/yangxiaohao/Desktop/RhinoScript/animation/'

    for cur in curve_points_dic:
            stream = curve_points_dic[cur]
            #newpoints = {}
            for frame in stream:
                newpoints = {}
                for i in range(1,x_number):
                    for j in range(1,y_number):
                        # calculate min distance from the point to the curve
                        min_distance = min(rs.Distance(points[i,j], stream))
                        if rs.Distance(points[(i,j)], frame) < interval*interval/2:
                            for each in stream:
                                distance = rs.Distance(points[(i,j)], each)
                                # select the closest point on the curve
                                if distance == min_distance and min_distance != 0:
                                    # find the index of current point on the curve
                                    this_pt_index = stream.index(each)
                                    curve_distance = []
                                    nearest_pt = None
                                    this_pt = rs.CreatePoint(points[(i,j)])
                                    if this_pt_index > 0:
                                        nearest_pt_index = this_pt_index - 1
                                        nearest_pt = stream[nearest_pt_index]
                                        # figure out the direction of the curve at each point
                                        direction_line = rs.AddLine(nearest_pt, each)
                                        translation = this_pt - nearest_pt
                                    else:
                                        nearest_pt_index = this_pt_index + 1
                                        nearest_pt = stream[nearest_pt_index]
                                        # figure out the direction of the curve at each point
                                        direction_line = rs.AddLine(each, nearest_pt)
                                        translation = this_pt - each
                                    rs.DeleteObject(rs.AddPoint(this_pt))
                                    # assign this direction to the center point of circle
                                    rs.MoveObject(direction_line, translation)
                                    # extend the direction based on the distance from point to current point on the curve
                                    extened_direction_line = rs.ExtendCurveLength(direction_line, extension_type=0, side=1,
                                                                                  length=math.sqrt(x_number)/(min_distance+1)+
                                                                                  math.sqrt(x_number)/(rs.Distance(points[(i,j)], frame)+1))
                                    end_point = rs.CurveEndPoint(extened_direction_line)
                                    rs.DeleteObject(direction_line)
                                    rs.DeleteObject(extened_direction_line)
                        # elevate point
                        else:
                            end_point = None
                        if min_distance > math.sqrt(x_number)*math.sqrt(interval)/2:
                            # the elevation of a point is based on the distance from each point to the curve
                            hight = min_distance
                            _change = rs.Distance(points[(i,j)], stream[-1])
                            hight = hight*math.sqrt(x_number)/math.sqrt(rs.Distance(points[(i,j)], frame)) - hight*math.sqrt(x_number)/_change
                            if end_point != None:
                                newpoints[i,j] = (end_point[0], end_point[1], hight/2)
                            else:
                                newpoints[i,j] = (points[(i,j)][0], points[(i,j)][1], hight/2)
                        else:
                            if end_point != None:
                                newpoints[i,j] = (end_point[0], end_point[1], math.sqrt(x_number)/(rs.Distance(points[(i,j)], frame)+1))
                            else:
                                newpoints[i,j] = (points[(i,j)][0], points[(i,j)][1], math.sqrt(x_number)*2/(rs.Distance(points[(i,j)], frame)+1))
                        if min_distance < math.sqrt(x_number)*math.sqrt(interval)/2+interval**2 and min_distance > math.sqrt(x_number)*math.sqrt(interval)/2:
                            if end_point != None:
                                newpoints[i,j] = (end_point[0], end_point[1], hight/2+math.sqrt(x_number)*2/(rs.Distance(points[(i,j)], frame)+1))
                            else:
                                newpoints[i,j] = (points[(i,j)][0], points[(i,j)][1], hight/2+math.sqrt(x_number)*2/(rs.Distance(points[(i,j)], frame)+1))
                vertices = []
                faceVertices = []
                vertices_1 = 0
                vertices_2 = 1
                vertices_3 = 2
                vertices_4 = 3
                for i in range(1,x_number):
                    for j in range(1,y_number):
                        if i > 1 and j > 1:
                            pt1 = rh.Geometry.Point3d(newpoints[i-1,j-1][0],newpoints[i-1,j-1][1],newpoints[i-1,j-1][2])
                            pt2 = rh.Geometry.Point3d(newpoints[i,j-1][0],newpoints[i,j-1][1],newpoints[i,j-1][2])
                            pt3 = rh.Geometry.Point3d(newpoints[i,j][0],newpoints[i,j][1],newpoints[i,j][2])
                            pt4 = rh.Geometry.Point3d(newpoints[i-1,j][0],newpoints[i-1,j][1],newpoints[i-1,j][2])
                            vertices += [pt1, pt2, pt3, pt4]
                            faceVertices += [(vertices_1,vertices_2,vertices_3,vertices_4)]
                            vertices_1 += 4
                            vertices_2 += 4
                            vertices_3 += 4
                            vertices_4 += 4

                mesh_frame = rs.AddMesh(vertices, faceVertices)
                animate(save_folder, stream.index(frame))
                rs.DeleteObject(mesh_frame)
                #p = rs.AddPoints(list(newpoints.values()))
    rs.DeleteObjects(point_list)


main()
