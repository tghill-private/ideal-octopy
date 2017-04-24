"""
Module KMLFormats.py

This module is to hold the strings to format for creating KML files.

Note that indentation is not required for KML files to be readable by
Google Earth, but is nice for human readability when KML files
need to be checked manually.

Used in module KML.py

KML Reference: https://developers.google.com/kml/documentation/kmlreference
"""

wind_arrow_height = 750 # same as OCO-2 data polygons
modis_time_fmt = '%Y-%m-%d'

oco2_header_description = """\
Viewer for OCO-2 L2 bias corrected Xco2 measurements.
Created from v7 Full data files.

MODIS Data:
http://map1.vis.earthdata.nasa.gov/twms-geo/kmlgen.cgi?layers=MODIS_Aqua_CorrectedReflectance_TrueColor&amp;time={time}
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
        <screenXY x="{x}" y="15" xunits="fraction" yunits="insetPixels"/>
        <rotationXY x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>
        <size x="{width}" y="{height}" xunits="fraction" yunits="fraction"/>
    </ScreenOverlay>
"""

Arrow_Format = """\
    <GroundOverlay>
        <name>{windsource} Wind Arrow</name>
            <description> Wind Information: {description}</description>
            <drawOrder>{draworder}</drawOrder>
            <Icon>
                <href>arrow_{arrow}.png</href>
                <viewBoundScale>0.75</viewBoundScale>
            </Icon>
            <altitude>0</altitude>
            <altitudeMode>clampedToGround</altitudeMode>
            <LatLonBox>
                <north>{N}</north>
                <south>{S}</south>
                <east>{E}</east>
                <west>{W}</west>
                <rotation>{rotation}</rotation>
            </LatLonBox>
    </GroundOverlay>
"""

Poly_Head ="""\
    <Style id="{style}">
        <PolyStyle>
            <color>{fillcolour}</color>
            <outline>{outline}</outline>
        </PolyStyle>
        <LineStyle>
            <color>{linecolour}</color>
        </LineStyle>
    </Style>
    <Placemark>
        <name>{style}</name>
"""

Poly_Body = """\
        <styleUrl>#{style}</styleUrl>
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
                    <color>{fillcolour}</color>
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

# Format with data name and data value
Data_Format = """\
                    <Data name="{name}"> 
                        <value>{value}</value>
                    </Data>'
"""

# Format with lon,lat,alt triples
polygon_coordinates = '        <coordinates>{coordinates}</coordinates>\n'

# .fomart(name, longitude, latitude)
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
        <name>{name}</name>
        <LookAt>
            <longitude>{lon}</longitude>
            <latitude>{lat}</latitude>
            <altitude>1000</altitude>
            <heading>0</heading>
            <tilt>0</tilt>
            <range>25000</range>
            <gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode>
        </LookAt>
        <styleUrl>#m_ylw-pushpin4</styleUrl>
        <Point>
            <gx:drawOrder>1</gx:drawOrder>
            <coordinates>{lon},{lat},0</coordinates>
        </Point>
    </Placemark>
"""

# Full File paths to create data for
paths =[('S31_xco2', 'S31 Corrected Xco2'),
        ('corrected_xco2','Corrected Xco2'),  ('partial_xco2','Partially Corrected Xco2'),
        ('retrieved_xco2','Raw Xco2'),  ('xco2_uncert','Xco2 Uncertainty'),
        ('retrieval_land_water_indicator','Land-Water Indicator'), ('retrieval_land_fraction','Land Fraction'),
        ('dp','dP'), ('reduced_chi_squared_o2_fph','Chi Squared O2 fph'), 
        ('reduced_chi_squared_strong_co2_fph','Chi Squared Strong CO2 fph'), 
        ('reduced_chi_squared_weak_co2_fph','Chi Squared Weak CO2 fph'), ('snr_o2_l1b','Signal-noise ratio O2'),
        ('snr_strong_co2_l1b','Signal-noise ratio Strong CO2'), ('snr_weak_co2_l1b','Signal-noise ratio weak CO2'),
        ('aerosol_1_aod','Aerosol 1 AOD'),('aerosol_1_type','Aerosol 1 Type'), 
        ('aerosol_2_aod','Aerosol 2 AOD'), ('aerosol_2_type','Aerosol 2 Type'),
        ('aerosol_3_aod','Aerosol 3 AOD'),('aerosol_3_type','Aerosol 3 Type'),
        ('aerosol_4_aod','Aerosol 4 AOD'), ('aerosol_4_type','Aerosol 4 Type'),
        ('aerosol_total_aod','Aerosol Total AOD'),('albedo_o2','Albedo O2'),
        ('albedo_strong_co2','Albedo Strong CO2'), ('albedo_weak_co2','Albedo Weak CO2'),
        ('retrieval_solar_zenith','Solar Zenith Angle'), ('retrieval_solar_azimuth','Solar Azimuth Angle'),
        ('retrieval_zenith','Viewing Zenith Angle'),('surface_pressure', 'Surface Pressure')]