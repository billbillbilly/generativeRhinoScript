# This script consists of two part of functions: set up loft surface and generate
# surface structures over the surface from first part using surface vectors
# and point matrix. #

import rhinoscriptsyntax as rs
import random
import math

### 1. Create a loft surface ###
# Generate a set of points (point matrix)
def pointsetup(x_number, y_number, interval):
    points = {} # points dictionary for saving 3D points
    point_list = [] # points list for saving point id
    for i in range(1,x_number):
        for j in range(1,y_number):
            addpoint = rs.AddPoint((i*interval, j*interval, 0))
            points[(i,j)] = (i*interval, j*interval, 0)
            point_list += [addpoint]
    return points, point_list

# indicate how many of curves will be created based on created points matrix
# the curve(s) will be used as attract curve(s), where its divide points will be
# attract points. #
def attrcurvesetup(num_curves):
    curve_points_list = [] # for saving divide 3D points along the curve(s)
    curve_endpoint = [] # for saving endpoint(s) of curve(s)
    curveid_list = [] # for saving curve id
    if num_curves == 1: # only draw one curve
        # pick up some generated points to create a cerve
        selected_points = rs.GetObjects(message="select points to create curve(s)",
                                        filter=1, group=False)
        # curve id
        curve_guid = rs.AddCurve(selected_points,3)
        # sample points along the curve
        curve_length = rs.CurveLength(curve_guid)
        # divide curve by the length of curve
        curve_points_list = rs.DivideCurve(curve_guid, round(curve_length),
                                           False, True)
    else: # draw several curves
        n = 0
        while n < num_curves:
            selected_points = rs.GetObjects(message="select points to create a curve",
                                            filter=1, group=False)
            curve_guid = rs.AddCurve(selected_points,3)
            # sample points along the curve
            curve_length = rs.CurveLength(curve_guid)
            # divide curve by the length of curve
            points_along_curve = rs.DivideCurve(curve_guid, round(curve_length),
                                                False, True)
            curve_points_list += points_along_curve
            # collect end point of each curve
            curve_endpoint += points_along_curve[-1]
            # save curve ids
            curveid_list += [curve_guid]
            n += 1
    # Delete cure(s) in rhino space
    if curveid_list != []:
        rs.DeleteObjects(curveid_list)
    else:
        rs.DeleteObject(curve_guid)
    return curve_points_list, curve_endpoint

# Create loft surface based on point matrix. #
# The elevations of 3D points in the matrix will be incresed based on
# the shortest distances from themselves to the points on the curve(s) #
# Section curves will generated from the elevated points in each row.
# Loft surfsace will be created by section curves.
def loftsurf(points, num_curves, curve_points_list, curve_endpoint, x_number,
             y_number, interval):
    curve_cluster = [] # for saving curve sections for loft surface
    for i in range(1,x_number):
        point_cluster = [] # for saving 3D points in
        for j in range(1,y_number):
            pt = points[(i,j)]
            # Calculate min distance from the point to the curve
            min_distance = min(rs.Distance(pt, curve_points_list))
            # The height of a point is based on the shortest distance from each
            # point in matrix to the curve(s). #
            # There are two height modification solutions down below
            # The longer the distance the point is
            # from the enpoint, the higher the elevation #
            h1 = min_distance/1.5
            h2 = math.sqrt(min_distance/2)
            # Calculate minimumn distance from endpoint to the point in the matrix
            # This vaiable will be used to elevate points in the matrix
            if num_curves == 1: # if there only one curve as input
                h_change = rs.Distance(pt, curve_points_list[-1])
            else: # if there more than one curve used as input
                h_change = min(rs.Distance(pt, curve_endpoint))
            # if this vaiable (distance) is shorter than 1, we just plus 1
            if h_change <= 1:
                h_change += 1
            if min_distance > 2*interval: # We set up a buffer along the curve(s),
                                          # where some points will not be elevated so much. #
                                          # The longer the distance the point is
                                          # from the enpoint, the lower the
                                          # elevation of the point. #
                # This height is affected by the distance from the point to the
                # endpoints of curves. #
                h1 -= 1.5*h1**2/h_change
                point_cluster += [(points[(i,j)][0], points[(i,j)][1], h1)]
            else:
                h2 -= h2**2/h_change
                # Save the elevated points in the same row in the list
                # within this loop. #
                point_cluster += [(points[(i,j)][0], points[(i,j)][1], h2)]
        # Create section curves
        section_curve = rs.AddCurve(point_cluster)
        # Save the sections in the list
        curve_cluster += [section_curve]
    # Create loft surface by section curves
    loft_surface = rs.AddLoftSrf(curve_cluster)
    # Delete the sections
    rs.DeleteObjects(curve_cluster)
    return loft_surface, curve_points_list

# A wraped up function for generating loft surface based on comtumized point matrix
def srfsetup():
    # Set the size of matrix
    x_number = rs.GetInteger(message="set the number of point on x direction",
                             number=30)
    y_number = rs.GetInteger(message="set the number of point on y direction",
                             number=30)
    # Set interval (size of unit in the matrix)
    interval = rs.GetInteger(message="set the interval", number=5)
    # Number of attract curves to be created
    num_curves = rs.GetInteger(message="set the number of curves")
    # Set up points matrix
    points, point_list = pointsetup(x_number, y_number, interval)
    # Sample attract points along the curve(s)
    curve_points_list, curve_endpoint = attrcurvesetup(num_curves)
    loft_surface, curve_points_list = loftsurf(points, num_curves,
                                               curve_points_list,
                                               curve_endpoint, x_number,
                                               y_number, interval)
    rs.DeleteObjects(point_list)
    return loft_surface, curve_points_list, interval

### 2.Create structure based on the loft surface ###
# Get domains and set up steps of uv
def surf_uv_stepsetup(surface, u_number, v_number):
    u_domain = rs.SurfaceDomain(surface, 0)
    v_domain = rs.SurfaceDomain(surface, 1)
    u_step = (u_domain[1]-u_domain[0])/u_number
    v_step = (v_domain[1]-v_domain[0])/v_number
    return u_domain, v_domain, u_step, v_step

# Set up point matrix based on uv steps
def surf_uv_pointsetup(surface, u_number, v_number, u_domain, v_domain, u_step,
                       v_step, curve_points_list):
    uvpoints = {} # Save points on the surface
    uvvectors = {} # Save points created by suface normal(vectors)
    for i in range(u_number+1):
        for j in range(v_number+1):
            u = u_domain[0] + i*u_step
            v = v_domain[0] + j*v_step
            # Get uv points on surface
            uvpoints[(i,j)] = rs.EvaluateSurface(surface, u, v)
            # Get vectors based on uv coordinates on surface
            uv_vector = rs.SurfaceNormal(surface, (u,v))
            # Calculate shortest distance for each uv point to the curve(s)
            min_distance = min(rs.Distance(uvpoints[(i,j)], curve_points_list))
            # Unitize the vectors
            uv_vector = rs.VectorUnitize(uv_vector)
            # This factor is used to rescale vectors
            factor = math.sqrt(min_distance)/2
            if factor <= 1:
                factor += 1 # We keep the factor always larger than 1
            # Scale the vector
            # The longer the distance the point is from the curve(s),
            # the larger the vector #
            uv_vector = rs.VectorScale(uv_vector, factor)
            # Create the vector points above the surface
            uvvectors[(i,j)] = rs.PointAdd(uv_vector, uvpoints[(i,j)])
            #rs.AddPoint(uvvectors[(i,j)])
    return uvpoints, uvvectors

# set up point matrix based on uv steps using points along the curve(s)
# as attract points
def attr_uv_pointsetup(surface, u_number, v_number, u_domain, v_domain, u_step,
                       v_step, curve_points_list):
    uvpoints = {} # Save points on the surface
    uvattrpoints = {} # Save attracted points on the surface
    uv_unit_vectors = {}
    uvvectors = {} # Save points created by suface normal(vectors)
    # Get uv points on surface
    for i in range(u_number+1):
        for j in range(v_number+1):
            u = u_domain[0] + i*u_step
            v = v_domain[0] + j*v_step
            uvpoints[(i,j)] = rs.EvaluateSurface(surface, u, v)
    # create point attracted by the closest points on curve(s)
    for i in range(u_number+1):
        for j in range(v_number+1):
            # keep the edge points
            if i == 0 or i == u_number:
                uvattrpoints[(i,j)] = uvpoints[(i,j)]
            elif j == 0 and j == v_number:
                uvattrpoints[(i,j)] = uvpoints[(i,j)]
            else:
                # Calculate shortest distance for each uv point to the curve(s)
                distance = min(rs.Distance(uvpoints[(i,j)], curve_points_list))
                for each in curve_points_list:
                    # Find out the closest point on the curve(s)
                    if rs.Distance(uvpoints[(i,j)], each) == distance:
                        # Create the vector between uv point on surface and
                        # closest point on curve(s). #
                        attr_vector = rs.VectorCreate(each, uvpoints[(i,j)])
                        if distance < 1:
                            distance += 1
                        # This factor is used to rescale the vector
                        # The longer the distance the point is from the curve(s),
                        # the less the vector gets reduced. #
                        factor = math.sqrt(distance)/distance
                        attr_vector = rs.VectorScale(attr_vector, factor)
                        # Add vector to uv point
                        attr_pt = rs.PointAdd(attr_vector, uvpoints[(i,j)])
                        # Create the attracted point on surface
                        uvattrpoints[(i,j)] = rs.BrepClosestPoint(surface, attr_pt)[0]

    for i in range(u_number+1):
        for j in range(v_number+1):
            # Get vectors based on attracted points on surface
            uv = rs.SurfaceClosestPoint(surface, uvattrpoints[(i,j)])
            uv_vector = rs.SurfaceNormal(surface, (uv[0],uv[1]))
            # Calculate shortest distance from the attracted point to curve(s)
            min_distance = min(rs.Distance(uvattrpoints[(i,j)], curve_points_list))
            # Unitize the vector
            uv_vector = rs.VectorUnitize(uv_vector)
            # This factor is used to rescale vector
            # The longer distance from attracted point to curve(s),
            # the larger the vector is. (the higher the point is)#
            factor = math.sqrt(min_distance)/1.5
            if factor < 1:
                factor += 1
            uv_vector = rs.VectorScale(uv_vector, factor)
            uvvectors[(i,j)] = rs.PointAdd(uv_vector, uvattrpoints[(i,j)])
            #rs.AddPoint(uvvectors[(i,j)])
    uvpoints = uvattrpoints
    return uvpoints, uvvectors

# Generate surface based on point matrix
def structure_generator(uvpoints, uvvectors, curve_points_list, u_number,
                        v_number, interval):
    # Count row number
    count1 = 0
    for i in range(u_number+1):
        # count column number
        count2 = 0
        for j in range(v_number+1):
            if i > 0 and j > 0:
                # Calculate this count factor for recognizing units
                count = abs(count1 - count2)
                # Create a buffer along the curve(s), where we only generate the surface
                # based on four point. #
                if min(rs.Distance(uvpoints[(i,j)], curve_points_list)) <= 2*interval:
                    # Count column number
                    count2 += 1
                    rs.AddSrfPt((uvpoints[(i,j)], uvpoints[(i,j-1)],
                                 uvpoints[(i-1,j-1)], uvpoints[(i-1,j)]))
                else: # There are two suface structure solutions, which will be
                      # alternatively applied to units of point matrix. #
                    # if the count factor can be divided by 2
                    if (count % 2) == 0:
                        # Count column number
                        count2 += 1
                        # A list of points in a unit
                        pt_cluster = [uvpoints[(i,j)], uvpoints[(i,j-1)],
                                      uvpoints[(i-1,j-1)], uvpoints[(i-1,j)]]
                        # A list of heights of the points above
                        h = [uvpoints[(i,j)][2], uvpoints[(i,j-1)][2],
                             uvpoints[(i-1,j-1)][2], uvpoints[(i-1,j)][2]]
                        pt = None
                        # Find out the lowest point
                        for k in pt_cluster:
                            if k[2] == min(h):
                                pt = k
                        # Generate 3D surface
                        # The longer distance from attracted point to curve(s),
                        # the thicker the 3D surface is. #
                        if pt == uvpoints[(i,j)]:
                            new_pt = (pt[0], pt[1], uvvectors[(i,j)][2])
                            srf = rs.AddSrfPt((new_pt, uvpoints[(i,j-1)],
                                         uvpoints[(i-1,j-1)], uvpoints[(i-1,j)]))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                            # infill surfaces
                            srf = rs.AddSrfPt((pt, uvpoints[(i,j-1)], new_pt))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                            srf = rs.AddSrfPt((pt, new_pt, uvpoints[(i-1,j)]))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))

                        elif pt == uvpoints[(i,j-1)]:
                            new_pt = (pt[0], pt[1], uvvectors[(i,j-1)][2])
                            srf = rs.AddSrfPt((uvpoints[(i,j)], new_pt,
                                         uvpoints[(i-1,j-1)], uvpoints[(i-1,j)]))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                            # infill surfaces
                            srf = rs.AddSrfPt((pt, uvpoints[(i,j)], new_pt))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                            srf = rs.AddSrfPt((pt, new_pt, uvpoints[(i-1,j-1)]))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))

                        elif pt == uvpoints[(i-1,j-1)]:
                            new_pt = (pt[0], pt[1], uvvectors[(i-1,j-1)][2])
                            srf = rs.AddSrfPt((uvpoints[(i,j)], uvpoints[(i,j-1)],
                                         new_pt, uvpoints[(i-1,j)]))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                            # infill surfaces
                            srf = rs.AddSrfPt((pt, uvpoints[(i-1,j)], new_pt))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                            srf = rs.AddSrfPt((pt, new_pt, uvpoints[(i,j-1)]))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))

                        elif pt == uvpoints[(i-1,j)]:
                            new_pt = (pt[0], pt[1], uvvectors[(i-1,j)][2])
                            srf = rs.AddSrfPt((uvpoints[(i,j)], uvpoints[(i,j-1)],
                                         uvpoints[(i-1,j-1)], new_pt))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                            # infill surfaces
                            srf = rs.AddSrfPt((pt, uvpoints[(i-1,j-1)], new_pt))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                            srf = rs.AddSrfPt((pt, new_pt, uvpoints[(i,j)]))
                            m_index = rs.AddMaterialToObject(srf)
                            rs.MaterialColor(m_index, (255,255,255))
                    # if the count factor can not be divided by 2
                    else:
                        # Count column number
                        count2 += 1
                        # Create bottom curve based on uv points in a unit on surface
                        bottom_curve = rs.AddCurve([uvpoints[(i,j)], uvpoints[(i,j-1)],
                                                    uvpoints[(i-1,j-1)], uvpoints[(i-1,j)],
                                                    uvpoints[(i,j)]], 1)
                        # Create up curve based on vector points in a unit above surface
                        up_curve = rs.AddCurve([uvvectors[(i,j)], uvvectors[(i,j-1)],
                                                uvvectors[(i-1,j-1)], uvvectors[(i-1,j)],
                                                uvvectors[(i,j)]], 1)
                        # Get the spatial centroid of vector points in a unit above surface
                        mid_pt = ((uvvectors[(i,j)][0]+uvvectors[(i-1,j-1)][0])/2,
                                 (uvvectors[(i,j)][1]+uvvectors[(i-1,j-1)][1])/2,
                                 (uvvectors[(i,j)][2]+uvvectors[(i-1,j-1)][2])/2)
                        # Calculate the shortest distance from the centroid to curve(s)
                        mid_distance = min(rs.Distance(mid_pt, curve_points_list))
                        # This factor is used to scale and rotate up curve
                        factor = math.sqrt(mid_distance)/mid_distance
                        # A list of points in a unit
                        pts = [uvpoints[(i,j)], uvpoints[(i,j-1)],
                               uvpoints[(i-1,j-1)], uvpoints[(i-1,j)]]
                        # Scale up curve
                        rs.ScaleObject(up_curve, mid_pt,
                                       ((1-factor)/(interval/2),
                                        (1-factor)/(interval/2), 0.4))
                        # Get control points of up curve
                        pt_c = rs.CurvePoints(up_curve)
                        # Save the distance from each point of
                        # those four points in a unit to curve(s). #
                        distance = []
                        # Get transilation
                        target = None # Target is where the up curve will be moved to
                        origin = None # Origin of the up curve
                        # Find the target point (furthest point to the attract curve(s))
                        for p in pts:
                            distance += [rs.Distance(p, curve_points_list)]
                        for p in pts:
                            if rs.Distance(p, curve_points_list) == max(distance):
                                if p == uvpoints[(i,j)]:
                                    target = uvvectors[(i,j)]
                                elif p == uvpoints[(i,j-1)]:
                                    target = uvvectors[(i,j-1)]
                                elif p == uvpoints[(i-1,j-1)]:
                                    target = uvvectors[(i-1,j-1)]
                                else:
                                    target = uvvectors[(i-1,j)]
                        # Use the closest point of control points of up curve
                        # to target point as origin. #
                        for p in pt_c:
                            if min(rs.Distance(target, pt_c)) == rs.Distance(target, p):
                                origin = p
                        # Make the centroid of vector points in a unit a 3D point
                        mid_pt = rs.CreatePoint(mid_pt)
                        # Calculate the transilation
                        translation = target - origin
                        # Move the up curve backward gainst the curve(s)
                        rs.MoveObject(up_curve, translation)
                        # Also move the controid
                        rs.MoveObject(mid_pt, translation)
                        # Rotate the moved up curve
                        rs.RotateObject(up_curve, mid_pt, 50*factor)
                        # Generate loft surface by up curve and bottom curve
                        srf = rs.AddLoftSrf((up_curve, bottom_curve))
                        m_index = rs.AddMaterialToObject(srf)
                        rs.MaterialColor(m_index, (255,255,255))
                        # Delete the up curve and bottom curve
                        rs.DeleteObject(up_curve)
                        rs.DeleteObject(bottom_curve)
        count1 += 1

# Final wraped up function
def main():
    surface, curve_points_list, interval = srfsetup()
    u_number = rs.GetInteger(message="set the number of point on u direction",
                             number=20)
    v_number = rs.GetInteger(message="set the number of point on v direction",
                             number=20)
    # Select a structure type
    structure_type = 2
    while structure_type != 0 and structure_type != 1:
        structure_type = rs.GetInteger(message="choose structure type, only type 0 or 1",
                                       number=0)
    u_domain, v_domain, u_step, v_step = surf_uv_stepsetup(surface, u_number, v_number)
    if structure_type == 0:
        uvpoints, uvvectors = surf_uv_pointsetup(surface, u_number, v_number,
                                                 u_domain, v_domain, u_step, v_step,
                                                 curve_points_list)
    else:
        uvpoints, uvvectors = attr_uv_pointsetup(surface, u_number, v_number,
                                                 u_domain, v_domain, u_step, v_step,
                                                 curve_points_list)
    structure_generator(uvpoints, uvvectors, curve_points_list, u_number,
                        v_number, interval)
    rs.DeleteObject(surface)

# Run
main()
