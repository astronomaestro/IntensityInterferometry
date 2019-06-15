import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, GeocentricTrueEcliptic, Angle
import astroquery
ar = np.array
import json
from astropy.io import fits, ascii
import os
from astroquery.vizier import Vizier
Vizier.ROW_LIMIT = -1
from astropy.coordinates import get_sun

class IItelescope():
    def __init__(self, telLat, telLon, telElv, time, steps):

        self.Bews = []
        self.Bnss = []
        self.Buds = []


        self.telLat = telLat * u.deg
        self.telLon = telLon * u.deg
        self.telElv = telElv * u.m
        self.tel_loc = EarthLocation(lat=telLat * u.deg, lon=telLon * u.deg, height=telElv * u.m)



        self.observable_times = None
        self.sidereal_times = None
        self.star_degs = None
        self.time_info = None

        self.time_info = Time(time, location=self.tel_loc)
        self.delta_time = np.linspace(-12, 12, steps) * u.hour

        self.telFrame = AltAz(obstime=self.time_info + self.delta_time, location=self.tel_loc)

        #get indicies for when sky is dark
        from astropy.coordinates import get_sun
        self.sunaltazs = get_sun(self.delta_time+self.time_info).transform_to(self.telFrame)
        dark_times = np.where((self.sunaltazs.alt < -15*u.deg))
        self.dark_times = self.telFrame.obstime.sidereal_time('apparent')[dark_times]


    def add_baseline(self, Bew, Bns, Bud):
        self.Bews.append(Bew)
        self.Bnss.append(Bns)
        self.Buds.append(Bud)

    def star_track(self, ra=None, dec=None, star_name=None, sunangle=-15, veritas_ang=20):
        if star_name:
            starToTrack = SkyCoord.from_name(star_name)
            self.ra = starToTrack.ra
            self.dec = starToTrack.dec
        else:
            self.ra = ra
            self.dec = dec
            starToTrack = SkyCoord(ra=ra, dec=dec)


        starLoc = starToTrack.transform_to(self.telFrame)


        sky_ind = np.where((self.sunaltazs.alt < -15*u.deg) & (starLoc.alt > 20*u.deg))[0]
        observable_times = self.delta_time[sky_ind]


        self.observable_times = observable_times
        self.sidereal_times = self.telFrame.obstime.sidereal_time('apparent')[sky_ind] - starToTrack.ra
        self.star_degs = starLoc.alt.to("deg")[sky_ind]



    def make_gaia_query(self, mag_range=(1, 6), ra_range=(30, 100), dec_range=(30, 100)):
        columns = ['N', 'RAJ2000','DEJ2000','Gmag','BPmag, "RPmag','Teff','Rad','Lum','Plx']
        v = Vizier(columns=columns)
        v.ROW_LIMIT = -1
        print("Retrieving Catalogue")
        result = v.query_constraints(catalog="I/345/gaia2",
                                     RPmag='>%s & <%s' %(mag_range[0], mag_range[1]),
                                     RAJ2000=">%s & <%s"%(ra_range[0], ra_range[1]),
                                     DEJ2000='>%s & <%s'%(dec_range[0], dec_range[1]))
        asdf=123

        good_vals = np.where(~np.isnan(result[0]['Rad']))

        self.gaia = result[0][good_vals]


        # if from_database:
        #
        #     gaia_query = "select " \
        #                  "gaia_source.source_id, gaia_source.ra, gaia_source.dec, gaia_source.parallax, gaia_source.phot_g_mean_mag, " \
        #                  "gaia_source.teff_val, gaia_source.radius_val, gaia_source.lum_val " \
        #                  "from gaiadr2.gaia_source " \
        #                  "where (gaiadr2.gaia_source.ra >=%s and gaiadr2.gaia_source.ra <=%s " \
        #                  "and gaiadr2.gaia_source.dec >=%s and gaiadr2.gaia_source.dec <=%s " \
        #                  "and gaiadr2.gaia_source.phot_g_mean_mag >=%s and gaiadr2.gaia_source.phot_g_mean_mag <=%s)"\
        #                  %(ra_range[0], ra_range[1], dec_range[0], dec_range[1], mag_range[0], mag_range[1])
        #
        #
        #     job = Gaia.launch_job(gaia_query, output_file="observableStars.xml", dump_to_file=True)
        #     result = job.get_results()
        #     asd=123

    def make_cadars_query(self, from_database=True, mag_range=(1, 6), ra_range=(30, 100), dec_range=(30, 100), load_vizier=True):
        columns = ['N', 'Type','Id1', 'Method', 'Lambda', 'UD', 'e_UD', 'LD', 'e_LD', 'RAJ2000', 'DEJ2000', 'Vmag', 'Kmag']
        v = Vizier()
        v.ROW_LIMIT = -1
        print("Retrieving Catalogue")
        result = v.query_constraints(catalog="II/224",
                                     Vmag='>%s & <%s' %(mag_range[0], mag_range[1]),
                                     RAJ2000=">%s & <%s"%(ra_range[0], ra_range[1]),
                                     DEJ2000='>%s & <%s'%(dec_range[0], dec_range[1]))

        good_val = np.where(~np.isnan(result[0]['Diam']))
        self.cedars = result[0][good_val]
        asdf=123


    def make_charm2_query(self, mag_range=(1, 6), ra_range=(30, 100), dec_range=(30, 100)):
        columns = ['N', 'Type','Id1', 'Method', 'Lambda', 'UD', 'e_UD', 'LD', 'e_LD', 'RAJ2000', 'DEJ2000', 'Vmag', 'Kmag']
        v = Vizier(columns=columns)
        v.ROW_LIMIT = -1
        print("Retrieving Catalogue")
        local_dat = [d for d in os.listdir() if '.dat' in d]

        result = v.query_constraints(catalog="J/A+A/431/773",
                                     Bmag='>%s & <%s' %(mag_range[0], mag_range[1]),
                                     RAJ2000=">%s & <%s"%(ra_range[0], ra_range[1]),
                                     DEJ2000='>%s & <%s'%(dec_range[0], dec_range[1]))
        good_val = np.where(~np.isnan(result[0]['UD']))
        self.charm2 = result[0][good_val]

    def make_jmmc_query(self, mag_range=(1, 6), ra_range=(30, 100), dec_range=(30, 100)):
        columns = ['RAJ2000','DEJ2000','2MASS','Tessmag','Teff','R*','M*','logg','Dis','Gmag','Vmag']
        v = Vizier()
        v.ROW_LIMIT = -1
        print("Retrieving Catalogue")
        local_dat = [d for d in os.listdir() if '.dat' in d]

        result = v.query_constraints(catalog="II/346/jsdc_v2",
                                     Bmag='>%s & <%s' %(mag_range[0], mag_range[1]),
                                     RAJ2000=">%s & <%s"%(ra_range[0], ra_range[1]),
                                     DEJ2000='>%s & <%s'%(dec_range[0], dec_range[1]))
        good_val = np.where(~np.isnan(result[0]['Dis']))
        self.jmmc = result[0][good_val]

    def bright_star_cat(self, ra_range=(30, 100), dec_range=(30, 100)):
        from astroquery.vizier import Vizier
        Vizier.ROW_LIMIT = -1
        bs_cat = Vizier.get_catalogs("V/50")[0]
        RAJ2000 = Angle(bs_cat["RAJ2000"], u.hourangle)
        DEJ2000 = Angle(bs_cat["DEJ2000"], u.deg)
        viewable_stars = np.where((RAJ2000 > ra_range[0] * u.hourangle) & (RAJ2000 < ra_range[1] * u.hourangle) &
                                  (DEJ2000 > dec_range[0] * u.deg) & (DEJ2000 < dec_range[1] * u.deg))
        self.BS_stars = bs_cat[viewable_stars]

        adf=12312

    def make_tess_query(self, mag_range=(1, 6), ra_range=(0, 360), dec_range=(-90, 90)):
        print("Retrieving Catalogue")


        columns = ['RAJ2000','DEJ2000','TIC','2MASS','Tessmag','Teff','R*','M*','logg','Dist','Gmag','Vmag']
        v = Vizier(columns=columns)
        v.ROW_LIMIT = -1

        result = v.query_constraints(catalog="J/AJ/156/102",
                                     Tessmag='>%s & <%s' %(mag_range[0], mag_range[1]),
                                     RAJ2000=">%s & <%s"%(ra_range[0], ra_range[1]),
                                     DEJ2000='>%s & <%s'%(dec_range[0], dec_range[1]))
        good_val = np.where(~np.isnan(result[0]['R_']))

        self.tess = result[0][good_val]
        #
        #
        # result = v.query_constraints(catalog="J/AJ/156/102", Tessmag='<%s'%mag_range[1],
        #                                   RAJ2000='>%s & <%s'%(ra_range[0], ra_range[1]),
        #                                   DEJ2000='>%s & <%s'%(dec_range[0], dec_range[1]))
        # print(result[0][np.where(result[0]['_2MASS'] == '05474538-0940105')])
        # angular_diam =(((result[0]['R_']).to('m') / (result[0]['Dist']).to('m'))*u.rad).to("arcsec")
        # viewable_stars = np.where((RAJ2000 > ra_range[0] * u.hourangle) & (RAJ2000 < ra_range[1] * u.hourangle) &
        #                           (DEJ2000 > dec_range[0] * u.deg) & (DEJ2000 < dec_range[1] * u.deg))
        # self.TESS_stars = tessCat[low_mind][viewable_stars]

    def download_vizier_cat(self, cat, name):
        from astroquery.vizier import Vizier
        Vizier.ROW_LIMIT = -1
        catalog = Vizier.find_catalogs(cat)
        cata = Vizier.get_catalogs(catalog.keys())
        ascii.write(cata, "%s.dat"%(name))

    def ra_dec_diam_getter(self, tel, star):
        if tel.upper() == "CEDARS":
            ra = Angle(star["RAJ2000"], 'hourangle')
            dec = Angle(star["DEJ2000"], 'deg')
            ang_diam = star["Diam"] * u.arcsec
        elif tel.upper() == "JMMC":
            ra = Angle(star["RAJ2000"], 'hourangle')
            dec = Angle(star["DEJ2000"], 'deg')
            ang_diam = star["UDDB"]/1000 * u.arcsec
        elif tel.upper() == "CHARM2":
            ra = Angle(star["RAJ2000"], 'hourangle')
            dec = Angle(star["DEJ2000"], 'deg')
            ang_diam = star["UD"]/1000 * u.arcsec
        elif tel.upper() == "TESS":
            ra = Angle(star["RAJ2000"], 'hourangle')
            dec = Angle(star["DEJ2000"], 'deg')
            dist= star['Dist']*u.parsec
            diam= star['R_']*u.solRad
            ang_diam = (((diam.to('m')/dist.to('m')))*u.rad).to('arcsec')
        elif tel.upper() == "GAIA":
            ra = Angle(star["RAJ2000"], 'hourangle')
            dec = Angle(star["DEJ2000"], 'deg')
            dist = 1/(star['Plx']/1000)*u.parsec
            diam= star['Rad']*u.solRad
            ang_diam = (((diam.to('m')/dist.to('m')))*u.rad).to('arcsec')

        return ra,dec,ang_diam
