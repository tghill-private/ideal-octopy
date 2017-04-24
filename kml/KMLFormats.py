"""
Module KMLFormats.py

This module is to hold the strings to format for creating KML files.

Note that indentation is not required for KML files to be readable by
Google Earth, but is nice for human readability when KML files
need to be checked manually.

Used in module KML.py (/home/tim/PythonModules/KML)

KML Reference: https://developers.google.com/kml/documentation/kmlreference
"""

file_header = """\
<?xml version="1.0" encoding="UTF-8"?>
<kml>
    <Document>
        <name>{name}</name>
        <description>{description}</description>
"""

file_footer = """\
    </Document>
</kml>
"""

folder_header = """\
    <Folder>
        <name>{name}</name>
            <description>{description}</description>
"""

folder_footer = """\
    </Folder>
"""

LineString = """\
    <Placemark>
        <name>{name}</name>
        <description>{description}</description>
        {styletag}\
        <LineString>
            <extrude>{extrude}</extrude>
            <tesselate>{tesselate}</tesselate>
            <coordinates>{coordinates}</coordinates>
        </LineString>
    </Placemark>
"""

LineStyle = """\
    <Style id="{id}">
        <LineStyle>
            <color>{colour}</color>
            <width>{width}</width>
        </LineStyle>
    </Style>
"""

StyleUrl = """\
        <styleUrl>#{url}</styleUrl>
"""

PolyStyle = """\
    <Style id="{style}">
        <PolyStyle>
            <color>{fillcolour}</color>
        </PolyStyle>
        <LineStyle>
            <color>{linecolour}</color>
            <width>{linewidth}</width>
        </LineStyle>
    </Style>
"""

Polygon = """\
    <Placemark>
        <name>{name}</name>
{data}\
{LookAt}\
        <description>{description}</description>
{styleUrl}\
        <Polygon>
            <altitudeMode>{altitudeMode}</altitudeMode>
            <tessellate>{tessellate}</tessellate>
            <extrude>{extrude}</extrude>
{outerBoundary}\
{innerBoundary}\
        </Polygon>
    </Placemark>
"""

OuterBoundary = """\
            <outerBoundaryIs>
                <LinearRing>
                    <coordinates>{coordinates}</coordinates>
                </LinearRing>
            </outerBoundaryIs>
"""

InnerBoundary = """\
            <innerBoundaryIs>
                <LinearRing>
                    <coordinates>{coordinates}</coordinates>
                </LinearRing>
            </innerBoundaryIs>
"""
      
Data_Header = """\
            <ExtendedData>
"""
              
Data_Footer = """\
            </ExtendedData>
"""

# Format with data name and data value
Data_Format = """\
                <Data name="{name}"> 
                    <value>{value}</value>
                </Data>
"""

coordinates = """\
    <coordinates>{coordinates}<coordinates>
"""

# .fomart(name, longitude, latitude)
placemark = """\
<Placemark>
        <name>{name}</name>
        {LookAt}\
        {styleUrl}\
        <Point>
            <gx:drawOrder>1</gx:drawOrder>
            <coordinates>{lon},{lat},{altitude}</coordinates>
        </Point>
    </Placemark>
"""

LookAt = """\
        <LookAt>
            <longitude>{lon}</longitude>
            <latitude>{lat}</latitude>
            <altitude>{altitude}</altitude>
            <heading>{heading}</heading>
            <tilt>{tilt}</tilt>
            <range>{range}</range>
            <altitudeMode>{altitudeMode}</altitudeMode>
        </LookAt>
"""

IconStyle = """\
<Style id="{id}">
        <IconStyle>
            <scale>1.3</scale>
            <Icon>
                {icon}
            </Icon>
            <hotSpot x="{x}" y="{y}" xunits="{xunits}" yunits="{yunits}"/>
        </IconStyle>
    </Style>
"""

GroundOverlay = """\
    <GroundOverlay>
        <name>{name}</name>
        <color>{colour}</color>
        <description>{description}</description>
{data}\
        <drawOrder>{drawOrder}</drawOrder>
        <Icon>
            <href>{href}</href>
            <viewBoundScale>{viewBoundScale}</viewBoundScale>
        </Icon>
        <LatLonBox>
          <north>{north}</north>
          <south>{south}</south>
          <east>{east}</east>
          <west>{west}</west>
          <rotation>{rotation}</rotation>
        </LatLonBox>
    </GroundOverlay>
"""

ScreenOverlay = """\
    <ScreenOverlay>
        <name>{name}</name>
        <description>{description}</description>
        <Icon>
            <href>{href}</href>
        </Icon>
        <overlayXY x="{xOverlay}" y="{yOverlay}" xunits="{xunitsOverlay}" yunits="{yunitsOverlay}"/>
        <screenXY x="{xScreen}" y="{yScreen}" xunits="{xunitsScreen}" yunits="{yunitsScreen}"/>
        <rotationXY x="{xRotation}" y="{yRotation}" xunits="{xunitsRotation}" yunits="{yunitsRotation}"/>
        <rotation>{rotation}</rotation>
        <size x="{xsize}" y="{ysize}" xunits="{xunits}" yunits="{yunits}"/>
    </ScreenOverlay>
"""