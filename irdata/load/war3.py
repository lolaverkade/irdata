import collections
import datetime
import zipfile
import re
from os import path

import sqlalchemy as sa
import yaml

from irdata import csv2
from irdata import model
from irdata.load import utils

def load_war3(src):
    """ Load COW War Data v. 3 """

    def _dates(row, n):
        y = model.War3Date()
        y.war_no = row['war_no']
        y.spell_no = n
        y.yr_beg = row['yr_beg%d' % n]
        y.mon_beg = row['mon_beg%d' % n]
        y.day_beg = row['day_beg%d' % n]
        y.yr_end = row['yr_end%d' % n]
        y.mon_end = row['mon_end%d' % n]
        y.day_end = row['day_end%d' % n]
        return y

    session = model.SESSION()
    reader = csv2.DictReader(src, encoding='latin1')
    reader.fieldnames = [utils.camel2under(x) for x in reader.fieldnames]

    war_cols = [x.name for x in model.War3.__table__.c]
    war_date_cols = [x.name for x in model.War3Date.__table__.c]
    for row in reader:
        for k,v in row.iteritems():
            row[k] = utils.replmiss(v, lambda x: x in ("-999", "-888"))
        ## Inter-state war does not have a war_type
        if 'war_type' not in row.keys():
            row['war_type'] = 1
        row['oceania'] = row['oceania'] if row['oceania'] else False
        session.add(model.War3(**utils.subset(row, war_cols)))
        ## Dates
        date1 = model.War3Date(war_no = row['war_no'],
                               spell_no = 1)
        for k in ('yr_beg', 'mon_beg', 'day_beg'):
            setattr(date1, k, row["%s1" % k])
        session.add(_dates(row, 1))
        if row['yr_beg2']:
            session.add(_dates(row, 2))
    session.commit()

def load_war3_partic(src):
    """ Load COW War Data v. 3, Participants """

    def _dates(row, n):
        y = model.War3ParticDate()
        y.war_no = row['war_no']
        y.state_num = row['state_num']
        y.partic_no = row['partic_no']
        y.spell_no = n
        y.yr_beg = row['yr_beg%d' % n]
        y.mon_beg = row['mon_beg%d' % n]
        y.day_beg = row['day_beg%d' % n]
        y.yr_end = row['yr_end%d' % n]
        y.mon_end = row['mon_end%d' % n]
        y.day_end = row['day_end%d' % n]
        return y

    session = model.SESSION()
    reader = csv2.DictReader(src, encoding='latin1')
    reader.fieldnames = [utils.camel2under(x) for x in reader.fieldnames]
    war_cols = [x.name for x in model.War3Partic.__table__.c]
    war_date_cols = [x.name for x in model.War3ParticDate.__table__.c]
    cnt = collections.Counter()
    for row in reader:
        ## Account for multiple country-war participations
        key = (row['war_no'], row['state_num'])
        cnt[key] += 1
        row['partic_no'] = cnt[key]
        ## replace missing values
        for k,v in row.iteritems():
            row[k] = utils.replmiss(v, lambda x: x in ("-999", "-888"))
        session.add(model.War3Partic(**utils.subset(row, war_cols)))
        ## Dates
        date1 = model.War3ParticDate(war_no = row['war_no'],
                                     spell_no = 1)
        for k in ('yr_beg', 'mon_beg', 'day_beg'):
            setattr(date1, k, row["%s1" % k])
        session.add(_dates(row, 1))
        if row['yr_beg2']:
            session.add(_dates(row, 2))
    session.commit()

def load_all(data, external):
    """ Load all COW War Data v. 3 (Inter-, Intra-, and Extra-State)"""
    utils.load_enum_from_yaml(open(path.join(data, "war3_enum.yaml"), 'r'))
    load_war3(open(path.join(external, "www.correlatesofwar.org/cow2 data/WarData/InterState/Inter-State Wars (V 3-0).csv"), 'r'))
    load_war3_partic(open(path.join(external, "www.correlatesofwar.org/cow2 data/WarData/InterState/Inter-State War Participants (V 3-0).csv"), 'r'))
    load_war3(open(path.join(external, "www.correlatesofwar.org/cow2 data/WarData/IntraState/Intra-State Wars (V 3-0).csv"), 'r'))
    load_war3_partic(open(path.join(external, "www.correlatesofwar.org/cow2 data/WarData/IntraState/Intra-State War Participants (V 3-0).csv"), 'r'))
    load_war3(open(path.join(external, "www.correlatesofwar.org/cow2 data/WarData/ExtraState/Extra-State Wars (V 3-0).csv"), 'r'))
    load_war3_partic(open(path.join(external, "www.correlatesofwar.org/cow2 data/WarData/ExtraState/Extra-State War Participants (V 3-0).csv"), 'r'))

    