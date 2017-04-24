"""
Module KMLFormats.py

This module is to hold the strings to format for creating KML files.

Note that indentation is not required for KML files to be readable by
Google Earth, but is nice for human readability when KML files
need to be checked manually.

Used in module KML.py (/home/tim/PythonModules/KML)

KML Reference: https://developers.google.com/kml/documentation/kmlreference
"""

modis_time_fmt = '%Y-%m-%d'

oco2_header_description = """\
Viewer for OCO-2 L2 bias corrected Xco2 measurements.
Created from v7 Full data files.

MODIS Data:
http://map1.vis.earthdata.nasa.gov/twms-geo/kmlgen.cgi?layers=MODIS_Aqua_CorrectedReflectance_TrueColor&amp;time={0}
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
      
scale = """\
    <ScreenOverlay id="feat_9640">
        <name>Color Scale</name>
          <description>{description}</description>
            <Icon id="link_0">
                <href>{cbar}</href>
            </Icon>
        <overlayXY x="0" y="1" xunits="fraction" yunits="fraction"/>
        <screenXY x="15" y="15" xunits="pixels" yunits="insetPixels"/>
        <rotationXY x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>
        <size x="{width}" y="{height}" xunits="fraction" yunits="fraction"/>
    </ScreenOverlay>
"""

Arrow_Format = """\
    <GroundOverlay>
        <name>{0} Wind Arrow</name>
            <description> Wind Information: {1}</description>
            <drawOrder>{8}</drawOrder>
            <Icon>
                <href>arrow_{7}.png</href>
                <viewBoundScale>0.75</viewBoundScale>
            </Icon>
            <altitude>0</altitude>
            <altitudeMode>clampedToGround</altitudeMode>
            <LatLonBox>
                <north>{2}</north>
                <south>{3}</south>
                <east>{4}</east>
                <west>{5}</west>
                <rotation>{6}</rotation>
            </LatLonBox>
    </GroundOverlay>
"""

Poly_Head ="""\
    <Style id="{name}">
        <PolyStyle>
            <color>{fill_color}</color>
            <outline>{outline}</outline>
        </PolyStyle>
        <LineStyle>
            <color>{line_color}</color>
        </LineStyle>
    </Style>
    <Placemark>
        <name>{name}</name>
"""

Poly_Body = """\
        <styleUrl>#{name}</styleUrl>
            <Polygon>
                <altitudeMode>relativeToGround</altitudeMode>
                <tessellate>1</tessellate>
                <outerBoundaryIs>
                    <LinearRing>
"""
Poly_Foot = """\
                    </LinearRing>
                </outerBoundaryIs>
                <PolyStyle>
                    <color>{color}</color>
                </PolyStyle>
            </Polygon>
    </Placemark>
"""
      
Data_Header = """\
                <ExtendedData>
"""
              
Data_Footer = """\
                </ExtendedData>
"""

Data_Format = """\
                    <Data name="{name}"> 
                        <value>{value}</value>
                    </Data>'
"""

polygon_coordinates = '        <coordinates>{coord}</coordinates>\n'

placemark = \
""" <Style id="s_ylw-pushpin_hl2">
        <IconStyle>
            <scale>1.3</scale>
            <Icon>
                <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
            </Icon>
            <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
        </IconStyle>
    </Style>
    <Style id="s_ylw-pushpin4">
        <IconStyle>
            <scale>1.1</scale>
            <Icon>
                <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
            </Icon>
            <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
        </IconStyle>
    </Style>
    <StyleMap id="m_ylw-pushpin4">
        <Pair>
            <key>normal</key>
            <styleUrl>#s_ylw-pushpin4</styleUrl>
        </Pair>
        <Pair>
            <key>highlight</key>
            <styleUrl>#s_ylw-pushpin_hl2</styleUrl>
        </Pair>
    </StyleMap>
    <Placemark>
        <name>{0}</name>
        <LookAt>
            <longitude>{1}</longitude>
            <latitude>{2}</latitude>
            <altitude>1000</altitude>
            <heading>0</heading>
            <tilt>0</tilt>
            <range>25000</range>
            <gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode>
        </LookAt>
        <styleUrl>#m_ylw-pushpin4</styleUrl>
        <Point>
            <gx:drawOrder>1</gx:drawOrder>
            <coordinates>{1},{2},0</coordinates>
        </Point>
    </Placemark>
"""