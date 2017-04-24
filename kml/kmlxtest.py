import KML

map = KML.KML()
# style = KML.LineStyle(id = 'MyStyleId')

# ls = KML.LineString('-122.364383,37.824664,0 -122.364152,37.824322,0', style=style)

# map.add_object(ls)

# map.write('test.kml')

lats = [30,31,31,30,30]
lons = [-110, -110, -111, -111, -110]
alts = [100,110,200,310,100]
vs = zip(lons, lats)

vouter = [ (-77.05788457660967,38.87253259892824,100),
        (-77.05465973756702,38.87291016281703,100 ),
        (-77.05315536854791,38.87053267794386,100 ),
        (-77.05552622493516,38.868757801256,100),
        (-77.05844056290393,38.86996206506943,100),
        (-77.05788457660967,38.87253259892824,100)][::-1]

vinner = [ (-77.05668055019126,38.87154239798456,100 ),
            (-77.05542625960818,38.87167890344077,100) ,
            (-77.05485125901024,38.87076535397792,100 ),
            (-77.05577677433152,38.87008686581446,100 ),
            (-77.05691162017543,38.87054446963351,100 ),
            (-77.05668055019126,38.87154239798456,100)][::-1]

couter = KML.Coord(vouter)
cinner = KML.Coord(vinner)

chouter = KML.Coord(vouter, convex_hull=True)
chinner = KML.Coord(vinner, convex_hull=True)
            
pstyle = KML.PolyStyle('Style1', fillcolour='ffff00ff',
                            linecolour='ffaaffaa', linewidth=2)



la = KML.LookAt(lon=-77.05536878047577,
                lat = 38.8662703048300,
                heading = 0,
                tilt = 55,
                range = 800)
                
p = KML.Polygon(couter, innerBoundary=cinner, name = 'Test Pentagon', description = 'Put Description Here', style = pstyle, extrude=1, LookAt = la)
print p.args.name
p2 = KML.Polygon(chouter, innerBoundary=chinner, name = 'Test Pentagon CH', description = 'With Convex Hull order', style = pstyle)
print p2.args.name

print id(p.args.name)
print id(p2.args.name)

print p==p2
print p is p2

go = KML.GroundOverlay(north=37.83234,
                        east=-122.373033,
                        south=37.832122,
                        west=-122.373724,
                        href="http://www.google.com/intl/en/images/logo.gif",
                        rotation=45,)
map.add_object(go)

map.add_object(p)
map.add_object(p2)

so = KML.ScreenOverlay("http://www.google.com/intl/en/images/logo.gif")
map.add_object(so)
map.write('test.kml')