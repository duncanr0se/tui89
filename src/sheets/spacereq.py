
FILL = 8080  # Go with DUIM's 100 screens

sr_x = 0
sr_y = 1
sr_min = 0
sr_pref = 1
sr_max = 2

def xSpaceReqMax(space_req):
    return space_req[0][2]

def xSpaceReqDesired(space_req):
    return space_req[0][1]

def xSpaceReqMin(space_req):
    return space_req[0][0]

def ySpaceReqMax(space_req):
    return space_req[1][2]

def ySpaceReqDesired(space_req):
    return space_req[1][1]

def ySpaceReqMin(space_req):
    return space_req[1][0]

def combine_spacereqs(sr1, sr2):
    min_x = sr1[sr_x][sr_min] + sr2[sr_x][sr_min]
    pref_x = sr1[sr_x][sr_pref] + sr2[sr_x][sr_pref]
    max_x = sr1[sr_x][sr_max] + sr2[sr_x][sr_max]

    min_y = sr1[sr_y][sr_min] + sr2[sr_y][sr_min]
    pref_y = sr1[sr_y][sr_pref] + sr2[sr_y][sr_pref]
    max_y = sr1[sr_y][sr_max] + sr2[sr_y][sr_max]

    return ((min_x, pref_x, max_x), (min_y, pref_y, max_y))

def add_to_preferred(sr, adds):
    pref_x = sr[sr_x][sr_pref] + adds[sr_x]
    pref_y = sr[sr_y][sr_pref] + adds[sr_y]

    return ((sr[sr_x][sr_min], pref_x, sr[sr_x][sr_max]),
            (sr[sr_y][sr_min], pref_y, sr[sr_y][sr_max]))
