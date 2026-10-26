- # **Lecture 2.0 Computational Geometry** - Origins and Usecases

2. Algorithmic Design
Design is described through a sequence of rules and operations.
The algorithm generates geometry by executing those rules.

3. Parametric Design
Geometry is controlled by parameters and relationships.
Changing a parameter updates the design while preserving those relationships.

4. What is Representation?
Nurbs, Meshes, Pointcloud, etc. --> how we visualize the data

## **Geomtry Fundamentals**
Global Coordinate System:
- To measure the Space --> Orgin (0,0,0)
  - We need at least 3 Coordinates to locate a point in Space  

### Point
- X,Y,Z compoonent

### Vector
- X,Y,Z compoonent
- Magnitude ||v||

Unit vector --> Length of 1 they giv a dirction ||v||=1

### Orthogonal Vectors:
- 2  Vectors define a Plane

### Plane
1. With 1 Point and X,Y Axes
2. With 1 Point, 1 Vector (Normal Vector) --> Plane perpendicular to Vector
3. Define 3 Points in Space

    Local Coordinate System: Differet from Global, Alligned somewhre In Space, using a Origin (o)

## 2D Geometry
## Lines Segmments
1. With 2 Points point p0, p1 
2. With 1 Point, unit Vector, Length
    - point p0, vector v, float l
 
3. Properties: length l ,direction vector, end points, point on the line with parameter t = [0,1]

## Circles
Also 3 possibilities
1. WITH POINT, X, Y AXES
2. WITH TWO POINTS, TANGENT VECTOR
3. WITH THREE POINTS --> interpolate

### Circle Properties:
    plane P ((float xo, float yo, float zo) 
    (float xx, float yx, float zx)
    (float xy, float yy, float zy))
    radius r
    

    point pt and
    tangent vector 𝒗
    with parameter 𝒕𝒕∈ [𝟎𝟎,𝟐𝟐𝟐]

### Freeform Curves
- smooth, but doesnt follow a basic definition

 - Bezier Curve: no local control--> start and end point and then a construct (polyline) as controlpoints (connected via mathematical function), without operating directly into the curve --> maintain the smoothness
- B-Spline Curve:  cant create a circle, contro, with control points (polyline) but introduce specific control points on the curve (Knots) --> cant create very basic geometry
- NURBS curve: control points knots AND weights --> can define all shapes (Circle, Line, Ellipse, Freeform, etc.)



## 3D Geomtry
## Topology: 
**How object are connected (u can stretch a Cube into a circle a cylinder, cone, but not into a torus bc. of the hole)**

**Torus vs other basic Geometries:**
- has negative curvature
- has a diffenrent topology than the 4 others (hole)
- still u cant covert a torus into an obj. with 2 holes


### Freeform NURBS Surfaces


## Transformations
1. **Affine:** Affine transformations such as rotation and 
translation preserve straight lines, 
parallelism, and the ratios of distances 
between points
2. **Non-Affine:** Non-affine transformations, such as 
projective or non-linear warping, do not 
preserve parallelism between lines.

--> Representated in Form of a Transormation Matrix
--> Each Transformation has a Matrix with a different Shape

Are non Commutative : A x B 'not equal to' B x A

