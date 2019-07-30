import requests
from requests import Session
import multiprocessing as mp
import time
import random
import pyodbc

class Game:
    def __init__(self, homeTeamId, awayTeamId, date, gameStart, gameId):
        self.homeTeamId = homeTeamId
        self.awayTeamId = awayTeamId
        self.date = date
        self.gameStart = gameStart
        self.gameId = gameId

class Listing:
    def __init__(self, listingId, price, sectionId, sectionName, sectionNumber, seatCount, gameId, tickets):
        self.listingId = listingId
        self.price = price
        self.sectionId = sectionId
        self.sectionName = sectionName
        self.sectionNumber = sectionNumber
        self.seatCount = seatCount
        self.gameId = gameId
        self.tickets = tickets

class Ticket:
    def __init__(self, listingId, seatRow, seatNumber = None):
        self.listingId = listingId
        self.seatNumber = seatNumber
        self.seatRow = seatRow

randomTimings = [.01, .02, .03]

def connect():
    server = 'ticket-tracker.database.windows.net'
    database = 'Ticket Tracker'
    username = 'nmolby'
    password = 'Il0veMicr0s0ft'
    driver = '{ODBC Driver 17 for SQL Server}'
    cnxn = pyodbc.connect(
        'DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    cursor = cnxn.cursor()
    cursor.fast_executemany = True
    return cnxn, cursor

def getTeamIds(cursor):
    teamDict = {}
    cursor.execute("SELECT * FROM Teams")
    row = cursor.fetchone()
    while row:
        teamDict[row[0]] = row[1]
        row = cursor.fetchone()
    return teamDict

def getGamesPastNow(cursor):
    from datetime import datetime
    currentTime = datetime.utcnow()
    date = f"{currentTime.year}-{currentTime.month:02d}-{currentTime.day:02d}"
    currentTime = f"{currentTime.hour:02d}:{currentTime.minute:02d}:{currentTime.second:02d}"
    games = []

    cursor.execute(f"SELECT * FROM [Games] WHERE date > '{date}' UNION SELECT * FROM [Games] WHERE date = '{date}' AND game_start >= '{currentTime}'")
    row = cursor.fetchone()
    while row:
        game = Game(row[1], row[2], row[3], row[4], row[0])
        games.append(game)
        row = cursor.fetchone()
    return games

def getGames(teamId):
    params = (
        ('shstore', '1'),
        ('status', 'active |contingent'),
        ('spellCheck', 'true'),
        ('boostByCategory', 'true'),
        ('lang', 'true'),
        ('includeNonEventEntities', 'true'),
        ('edgeControlEnabled', 'true'),
        ('sourceId', '0 |1 |4001 |5001'),
        ('parking', 'false'),
        ('excludeFromRadius', 'false'),
        ('geoExpansion', 'true'),
        ('start', '0'),
        ('sort', 'eventDateLocal asc'),
        ('reRankBy', 'relevance'),
        ('improvedRelevancy', 'true'),
        ('eventType', 'main'),
        ('performerRole', 'homeTeam'),
        ('performerId', teamId),
    )

    headers = {
        'cookie': 'bff-activity=eaa1be29-551b-45f6-8e27-27e0ffa78c0a; SH_VI=d5d23139387a4046a12055161a0feaee; SH6_USER_PREF=%7B%22location%22%3A%7B%22geoNameId%22%3A4926563%2C%22city%22%3A%22South%20Bend%22%2C%22stateCode%22%3A%22IN%22%2C%22state%22%3A%22Indiana%22%2C%22countryCode%22%3A%22US%22%2C%22country%22%3A%22United%20States%22%2C%22latitude%22%3A41.68338%2C%22longitude%22%3A-86.25001%2C%22key%22%3A4926563%2C%22name%22%3A%22South%20Bend%2C%20IN%22%7D%7D; AKA_A2=A; ak_bmsc=A0B712FEB0F7550FC7373B342F8609F8173EE3B7005D00007905365D84AD6527~pls3kE3JuXUKGT+/T1L5dbrlqyZpBGM8h5qQp24fsDqakf+2d8RzA8oUv8dCyMYRbYylT/VXIU8rA2fqyihvmWuBalaFwVuQdvC2ijm3s5LW+lTzPO74dbwwf0SkqMTjQ8mjFgFx7Kw/hvZOgw5ZXAx8H/aRq9VzwQQaOsOiZ2TdkmTaITpbO8x5fahBgtUWRnDWDHTGhN7LmppBAVbXW6yz/8NluJpyHokTDokBmp0gk=; bm_sz=AF4E9010F179FFA791EBC167BDBA98B5~YAAQt+M+F2KAxd9rAQAAg2MFGwRnxdZuYxvCbW3BN9AH9HyHWOXpp8yHZmmcZ8VGbJJyQmD+rrdYylYxclxZJxXb3CYIuG7VMqrRjlO+t6+PWfyhEzDQ7xE5I1cB+3RiIluF8xwwnFQGxRbobeN9W/on2OSQze+t45GDwTYIZtYJps5NC8WRD7uhyKDVyJgB; _sim_si=744916ED-4F2E-4E47-BE71-DB3C05F1B046; _sim_uuid=BAC8BBFA-3C1A-4FAD-9A47-B53728E732B7; S_ACCT=stubhub%2Cstubhubglobal; _sim_li=YjQzYWQ5NWMtMDZmNS00MWM3LTk0M2UtODk0MjhhNjcwNzM2LmxvY2FsLDk4LjIyMy4yMzguNQ==; s_ecid=MCMID%7C83456816773556929564510389092603171315; AMCVS_1AEC46735278551A0A490D45%40AdobeOrg=1; AMCV_1AEC46735278551A0A490D45%40AdobeOrg=-1303530583%7CMCIDTS%7C18100%7CMCMID%7C83456816773556929564510389092603171315%7CMCAID%7CNONE%7CMCOPTOUT-1563828635s%7CNONE%7CvVersion%7C3.3.0; D_IID=714EB4A1-F4F6-3D6D-89CA-1A7EDECFCFF9; D_UID=2C0A5867-8D5D-38AB-9FAE-0FACA631F2EC; D_ZID=E5B05652-B3ED-3393-89BF-ED55AD5DB2C6; D_ZUID=F9B7094E-BD82-366F-A12A-4752BBA8E8D4; D_HID=4965CBA5-2B21-3841-86AB-9463B588832D; D_SID=98.223.238.5:yQQOZ392CHGU3UyLpkya8ESvCgGLCILEzgJHCTt8s5A; akacd_PCF_Prod=1563824103~rv=32~id=57f6e0b31187ae01b5c409dc6f7e4655; SH_AT=1XNOHCPxzhOmYfQsadRFfX%2FOMRCZ0KKzhzQg%2BzAtaxxW5pfv1Rx11KOIF7aMprwAi1zTpPFp2RZGReU5sKeZrDtPT322C9hLSzkANlrvaac%3D; DC=lvs01; S_ACCT=stubhub; SH_VI=d5d23139387a4046a12055161a0feaee; TLTHID=2DB5295EACB710AC048BB801C1813758; TLTSID=2DB5295EACB710AC048BB801C1813758; SH_BAU=%7B%22id%22%3A%221563824737.387a4046a1205516%22%2C%22key%22%3A%22EguJDGSwZkRx2w0D8RvmEvXKVm%2BvAq5J%2BdnOAfxBNss%3D%22%2C%22algorithm%22%3A%22sha256%22%7D; bm_sv=702870A87CEA67083DE52AD5AE64CED5~wEuMV0iJorCB1vJb5HV5Zdyi1N7ruepk+8lhie2ndmSXvxK3vS9dDoJ+aRYISusOaJIRpg19n8jTzKWtFs9hwF5d+Fd/da1J7L8oRN3OuC57EMMVpsE0AT0A/QXsQxNpKd++iJWynjVEFArbE0DWDQ7T6SDQHboU2zFxpI1iAz8=; _abck=08AF3A1204CEBF73A0579964DE827B4C~0~YAAQt+M+FwHKxd9rAQAAIJgrGwLX5qDngzRHIUukLgUYvVp0ZrZpJEg5Atgl8Y0ufUPwPn1lzq3s3FRnmQpP4Ugt7F3RkvTL8HtnnuyjTGW/f2BBL88NTY0c+LqKXv2Ox6tpgDnE+2+8lZ4XTbt9bJldMIRcge6Y0pbutPLDmIv7TVJsHH/HXi46fi/a7uJPueAfqK3hjD/msV5q/AV1w6AsjENGfFbgpzg/wVCzpJ0MXR7/g6jmULf6HSKOHzIPbiq84pmQF9T/dJN3NnltsfSeWja5b54sfNOKWxSUax13BktupjX0kCTn~-1~-1~-1; s_sess=%20s_cpc%3D0%3B%20s_sq%3D%3B%20s_cc%3Dtrue%3B%20s_ptc%3D0.01%255E%255E0.00%255E%255E0.00%255E%255E0.06%255E%255E0.47%255E%255E0.03%255E%255E0.96%255E%255E0.04%255E%255E1.55%3B%20s_tp%3D747%3B%20s_ppv%3DUE%25253A%252520Event%252520Details%25253A%252520Toggle%252520Splitscreen%25253A%252520FilterView%252C97%252C97%252C722%3B; s_tps=1852; s_pvs=11156; s_pers=%20s_dfa%3Dstubhub%252Cstubhubglobal%7C1563825633931%3B%20s_vs%3D1%7C1563825740531%3B%20gpv_v9%3DUE%253A%2520Event%2520Details%253A%2520Toggle%2520Splitscreen%253A%2520FilterView%7C1563825740534%3B%20s_nr%3D1563823940538-New%7C1597951940538%3B',
        'accept-encoding': 'gzip, deflate, br',
        'com-stubhub-dye-path': 'b6f68a2b93314168988edb2fcbc4cecd,0a0687fbc1274294adcc27e50ebfc02e',
        'accept-language': 'en-us',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'content-type': 'application/json',
        'accept': 'application/json',
        'referer': 'https://www.stubhub.com/cleveland-indians-tickets/performer/4882/',
        'authority': 'www.stubhub.com',
        'x-requested-with': 'XMLHttpRequest',
        'x-distil-ajax': 'yyqvbuqewxtcufrxveb',
    }

    response = requests.get('https://www.stubhub.com/bfx/api/search/catalog/events/v3', headers=headers,
                            params=params).json()
    games = []
    gameCount = response["numFound"]
    for listingStart in range(0, gameCount, 10):
        games.extend(getGamesByStart(listingStart, teamId))
    return games

def addGamesToTable(games: list, cursor):
    sql = "INSERT INTO [GAMES] ([game_id],[home_team_id],[away_team_id],[date], [game_start]) VALUES "
    for game in games:
        sql += f"('{game.gameId}', '{game.homeTeamId}', '{game.awayTeamId}', '{game.date}', '{game.gameStart}'),"
    cursor.execute(sql[:-1])
    cursor.commit()

def getGamesByStart(listingStart, teamId):

    params = (
        ('shstore', '1'),
        ('status', 'active |contingent'),
        ('spellCheck', 'true'),
        ('boostByCategory', 'true'),
        ('lang', 'true'),
        ('includeNonEventEntities', 'true'),
        ('edgeControlEnabled', 'true'),
        ('sourceId', '0 |1 |4001 |5001'),
        ('parking', 'false'),
        ('excludeFromRadius', 'false'),
        ('geoExpansion', 'true'),
        ('start', listingStart),
        ('sort', 'eventDateLocal asc'),
        ('reRankBy', 'relevance'),
        ('improvedRelevancy', 'true'),
        ('eventType', 'main'),
        ('performerRole', 'homeTeam'),
        ('performerId', teamId),
    )

    headers = {
        'cookie': 'bff-activity=eaa1be29-551b-45f6-8e27-27e0ffa78c0a; SH_VI=d5d23139387a4046a12055161a0feaee; SH6_USER_PREF=%7B%22location%22%3A%7B%22geoNameId%22%3A4926563%2C%22city%22%3A%22South%20Bend%22%2C%22stateCode%22%3A%22IN%22%2C%22state%22%3A%22Indiana%22%2C%22countryCode%22%3A%22US%22%2C%22country%22%3A%22United%20States%22%2C%22latitude%22%3A41.68338%2C%22longitude%22%3A-86.25001%2C%22key%22%3A4926563%2C%22name%22%3A%22South%20Bend%2C%20IN%22%7D%7D; AKA_A2=A; ak_bmsc=A0B712FEB0F7550FC7373B342F8609F8173EE3B7005D00007905365D84AD6527~pls3kE3JuXUKGT+/T1L5dbrlqyZpBGM8h5qQp24fsDqakf+2d8RzA8oUv8dCyMYRbYylT/VXIU8rA2fqyihvmWuBalaFwVuQdvC2ijm3s5LW+lTzPO74dbwwf0SkqMTjQ8mjFgFx7Kw/hvZOgw5ZXAx8H/aRq9VzwQQaOsOiZ2TdkmTaITpbO8x5fahBgtUWRnDWDHTGhN7LmppBAVbXW6yz/8NluJpyHokTDokBmp0gk=; bm_sz=AF4E9010F179FFA791EBC167BDBA98B5~YAAQt+M+F2KAxd9rAQAAg2MFGwRnxdZuYxvCbW3BN9AH9HyHWOXpp8yHZmmcZ8VGbJJyQmD+rrdYylYxclxZJxXb3CYIuG7VMqrRjlO+t6+PWfyhEzDQ7xE5I1cB+3RiIluF8xwwnFQGxRbobeN9W/on2OSQze+t45GDwTYIZtYJps5NC8WRD7uhyKDVyJgB; _sim_si=744916ED-4F2E-4E47-BE71-DB3C05F1B046; _sim_uuid=BAC8BBFA-3C1A-4FAD-9A47-B53728E732B7; S_ACCT=stubhub%2Cstubhubglobal; _sim_li=YjQzYWQ5NWMtMDZmNS00MWM3LTk0M2UtODk0MjhhNjcwNzM2LmxvY2FsLDk4LjIyMy4yMzguNQ==; s_ecid=MCMID%7C83456816773556929564510389092603171315; AMCVS_1AEC46735278551A0A490D45%40AdobeOrg=1; AMCV_1AEC46735278551A0A490D45%40AdobeOrg=-1303530583%7CMCIDTS%7C18100%7CMCMID%7C83456816773556929564510389092603171315%7CMCAID%7CNONE%7CMCOPTOUT-1563828635s%7CNONE%7CvVersion%7C3.3.0; D_IID=714EB4A1-F4F6-3D6D-89CA-1A7EDECFCFF9; D_UID=2C0A5867-8D5D-38AB-9FAE-0FACA631F2EC; D_ZID=E5B05652-B3ED-3393-89BF-ED55AD5DB2C6; D_ZUID=F9B7094E-BD82-366F-A12A-4752BBA8E8D4; D_HID=4965CBA5-2B21-3841-86AB-9463B588832D; D_SID=98.223.238.5:yQQOZ392CHGU3UyLpkya8ESvCgGLCILEzgJHCTt8s5A; akacd_PCF_Prod=1563824103~rv=32~id=57f6e0b31187ae01b5c409dc6f7e4655; SH_AT=1XNOHCPxzhOmYfQsadRFfX%2FOMRCZ0KKzhzQg%2BzAtaxxW5pfv1Rx11KOIF7aMprwAi1zTpPFp2RZGReU5sKeZrDtPT322C9hLSzkANlrvaac%3D; DC=lvs01; S_ACCT=stubhub; SH_VI=d5d23139387a4046a12055161a0feaee; TLTHID=2DB5295EACB710AC048BB801C1813758; TLTSID=2DB5295EACB710AC048BB801C1813758; SH_BAU=%7B%22id%22%3A%221563824737.387a4046a1205516%22%2C%22key%22%3A%22EguJDGSwZkRx2w0D8RvmEvXKVm%2BvAq5J%2BdnOAfxBNss%3D%22%2C%22algorithm%22%3A%22sha256%22%7D; bm_sv=702870A87CEA67083DE52AD5AE64CED5~wEuMV0iJorCB1vJb5HV5Zdyi1N7ruepk+8lhie2ndmSXvxK3vS9dDoJ+aRYISusOaJIRpg19n8jTzKWtFs9hwF5d+Fd/da1J7L8oRN3OuC57EMMVpsE0AT0A/QXsQxNpKd++iJWynjVEFArbE0DWDQ7T6SDQHboU2zFxpI1iAz8=; _abck=08AF3A1204CEBF73A0579964DE827B4C~0~YAAQt+M+FwHKxd9rAQAAIJgrGwLX5qDngzRHIUukLgUYvVp0ZrZpJEg5Atgl8Y0ufUPwPn1lzq3s3FRnmQpP4Ugt7F3RkvTL8HtnnuyjTGW/f2BBL88NTY0c+LqKXv2Ox6tpgDnE+2+8lZ4XTbt9bJldMIRcge6Y0pbutPLDmIv7TVJsHH/HXi46fi/a7uJPueAfqK3hjD/msV5q/AV1w6AsjENGfFbgpzg/wVCzpJ0MXR7/g6jmULf6HSKOHzIPbiq84pmQF9T/dJN3NnltsfSeWja5b54sfNOKWxSUax13BktupjX0kCTn~-1~-1~-1; s_sess=%20s_cpc%3D0%3B%20s_sq%3D%3B%20s_cc%3Dtrue%3B%20s_ptc%3D0.01%255E%255E0.00%255E%255E0.00%255E%255E0.06%255E%255E0.47%255E%255E0.03%255E%255E0.96%255E%255E0.04%255E%255E1.55%3B%20s_tp%3D747%3B%20s_ppv%3DUE%25253A%252520Event%252520Details%25253A%252520Toggle%252520Splitscreen%25253A%252520FilterView%252C97%252C97%252C722%3B; s_tps=1852; s_pvs=11156; s_pers=%20s_dfa%3Dstubhub%252Cstubhubglobal%7C1563825633931%3B%20s_vs%3D1%7C1563825740531%3B%20gpv_v9%3DUE%253A%2520Event%2520Details%253A%2520Toggle%2520Splitscreen%253A%2520FilterView%7C1563825740534%3B%20s_nr%3D1563823940538-New%7C1597951940538%3B',
        'accept-encoding': 'gzip, deflate, br',
        'com-stubhub-dye-path': 'b6f68a2b93314168988edb2fcbc4cecd,0a0687fbc1274294adcc27e50ebfc02e',
        'accept-language': 'en-us',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'content-type': 'application/json',
        'accept': 'application/json',
        'referer': 'https://www.stubhub.com/cleveland-indians-tickets/performer/4882/',
        'authority': 'www.stubhub.com',
        'x-requested-with': 'XMLHttpRequest',
        'x-distil-ajax': 'yyqvbuqewxtcufrxveb',
    }

    someGames = []
    response = requests.get('https://www.stubhub.com/bfx/api/search/catalog/events/v3', headers=headers,
                            params=params).json()
    gamesJson = response["events"]
    for game in gamesJson:
        gameId = game["id"]
        homeTeamId = game["performers"][0]["id"]
        awayTeamId = 0
        bothTeams = game["performersCollection"]
        for team in bothTeams:
            if team["id"] != homeTeamId:
                awayTeamId = team["id"]
        date = str(game["eventDateUTC"]).split('T')[0]
        gameStart = str(game["eventDateUTC"]).split('T')[1].split('+')[0]
        newGame = Game(homeTeamId, awayTeamId, date, gameStart, gameId)
        someGames.append(newGame)
    return someGames

def getListingsParallel(eventId, pool: mp.Pool):

    headers = {
        'cookie': 'bff-activity=eaa1be29-551b-45f6-8e27-27e0ffa78c0a; SH_VI=d5d23139387a4046a12055161a0feaee; SH6_USER_PREF=%7B%22location%22%3A%7B%22geoNameId%22%3A4926563%2C%22city%22%3A%22South%20Bend%22%2C%22stateCode%22%3A%22IN%22%2C%22state%22%3A%22Indiana%22%2C%22countryCode%22%3A%22US%22%2C%22country%22%3A%22United%20States%22%2C%22latitude%22%3A41.68338%2C%22longitude%22%3A-86.25001%2C%22key%22%3A4926563%2C%22name%22%3A%22South%20Bend%2C%20IN%22%7D%7D; AKA_A2=A; ak_bmsc=A0B712FEB0F7550FC7373B342F8609F8173EE3B7005D00007905365D84AD6527~pls3kE3JuXUKGT+/T1L5dbrlqyZpBGM8h5qQp24fsDqakf+2d8RzA8oUv8dCyMYRbYylT/VXIU8rA2fqyihvmWuBalaFwVuQdvC2ijm3s5LW+lTzPO74dbwwf0SkqMTjQ8mjFgFx7Kw/hvZOgw5ZXAx8H/aRq9VzwQQaOsOiZ2TdkmTaITpbO8x5fahBgtUWRnDWDHTGhN7LmppBAVbXW6yz/8NluJpyHokTDokBmp0gk=; bm_sz=AF4E9010F179FFA791EBC167BDBA98B5~YAAQt+M+F2KAxd9rAQAAg2MFGwRnxdZuYxvCbW3BN9AH9HyHWOXpp8yHZmmcZ8VGbJJyQmD+rrdYylYxclxZJxXb3CYIuG7VMqrRjlO+t6+PWfyhEzDQ7xE5I1cB+3RiIluF8xwwnFQGxRbobeN9W/on2OSQze+t45GDwTYIZtYJps5NC8WRD7uhyKDVyJgB; _sim_si=744916ED-4F2E-4E47-BE71-DB3C05F1B046; _sim_uuid=BAC8BBFA-3C1A-4FAD-9A47-B53728E732B7; S_ACCT=stubhub%2Cstubhubglobal; _sim_li=YjQzYWQ5NWMtMDZmNS00MWM3LTk0M2UtODk0MjhhNjcwNzM2LmxvY2FsLDk4LjIyMy4yMzguNQ==; s_ecid=MCMID%7C83456816773556929564510389092603171315; AMCVS_1AEC46735278551A0A490D45%40AdobeOrg=1; AMCV_1AEC46735278551A0A490D45%40AdobeOrg=-1303530583%7CMCIDTS%7C18100%7CMCMID%7C83456816773556929564510389092603171315%7CMCAID%7CNONE%7CMCOPTOUT-1563828635s%7CNONE%7CvVersion%7C3.3.0; D_IID=714EB4A1-F4F6-3D6D-89CA-1A7EDECFCFF9; D_UID=2C0A5867-8D5D-38AB-9FAE-0FACA631F2EC; D_ZID=E5B05652-B3ED-3393-89BF-ED55AD5DB2C6; D_ZUID=F9B7094E-BD82-366F-A12A-4752BBA8E8D4; D_HID=4965CBA5-2B21-3841-86AB-9463B588832D; D_SID=98.223.238.5:yQQOZ392CHGU3UyLpkya8ESvCgGLCILEzgJHCTt8s5A; akacd_PCF_Prod=1563824103~rv=32~id=57f6e0b31187ae01b5c409dc6f7e4655; SH_AT=1XNOHCPxzhOmYfQsadRFfX%2FOMRCZ0KKzhzQg%2BzAtaxxW5pfv1Rx11KOIF7aMprwAi1zTpPFp2RZGReU5sKeZrDtPT322C9hLSzkANlrvaac%3D; DC=lvs01; S_ACCT=stubhub; SH_VI=d5d23139387a4046a12055161a0feaee; TLTHID=2DB5295EACB710AC048BB801C1813758; TLTSID=2DB5295EACB710AC048BB801C1813758; SH_BAU=%7B%22id%22%3A%221563824737.387a4046a1205516%22%2C%22key%22%3A%22EguJDGSwZkRx2w0D8RvmEvXKVm%2BvAq5J%2BdnOAfxBNss%3D%22%2C%22algorithm%22%3A%22sha256%22%7D; bm_sv=702870A87CEA67083DE52AD5AE64CED5~wEuMV0iJorCB1vJb5HV5Zdyi1N7ruepk+8lhie2ndmSXvxK3vS9dDoJ+aRYISusOaJIRpg19n8jTzKWtFs9hwF5d+Fd/da1J7L8oRN3OuC57EMMVpsE0AT0A/QXsQxNpKd++iJWynjVEFArbE0DWDQ7T6SDQHboU2zFxpI1iAz8=; _abck=08AF3A1204CEBF73A0579964DE827B4C~0~YAAQt+M+FwHKxd9rAQAAIJgrGwLX5qDngzRHIUukLgUYvVp0ZrZpJEg5Atgl8Y0ufUPwPn1lzq3s3FRnmQpP4Ugt7F3RkvTL8HtnnuyjTGW/f2BBL88NTY0c+LqKXv2Ox6tpgDnE+2+8lZ4XTbt9bJldMIRcge6Y0pbutPLDmIv7TVJsHH/HXi46fi/a7uJPueAfqK3hjD/msV5q/AV1w6AsjENGfFbgpzg/wVCzpJ0MXR7/g6jmULf6HSKOHzIPbiq84pmQF9T/dJN3NnltsfSeWja5b54sfNOKWxSUax13BktupjX0kCTn~-1~-1~-1; s_sess=%20s_cpc%3D0%3B%20s_sq%3D%3B%20s_cc%3Dtrue%3B%20s_ptc%3D0.01%255E%255E0.00%255E%255E0.00%255E%255E0.06%255E%255E0.47%255E%255E0.03%255E%255E0.96%255E%255E0.04%255E%255E1.55%3B%20s_tp%3D747%3B%20s_ppv%3DUE%25253A%252520Event%252520Details%25253A%252520Toggle%252520Splitscreen%25253A%252520FilterView%252C97%252C97%252C722%3B; s_tps=1852; s_pvs=11156; s_pers=%20s_dfa%3Dstubhub%252Cstubhubglobal%7C1563825633931%3B%20s_vs%3D1%7C1563825740531%3B%20gpv_v9%3DUE%253A%2520Event%2520Details%253A%2520Toggle%2520Splitscreen%253A%2520FilterView%7C1563825740534%3B%20s_nr%3D1563823940538-New%7C1597951940538%3B',
        'accept-encoding': 'gzip, deflate, br',
        'com-stubhub-dye-path': 'b6f68a2b93314168988edb2fcbc4cecd,0a0687fbc1274294adcc27e50ebfc02e',
        'accept-language': 'en-us',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'content-type': 'application/json',
        'accept': 'application/json',
        'referer': "https://www.stubhub.com/cleveland-indians-tickets-cleveland-indians-cleveland-progressive-field-7-30-2019/event/103822145/?sort=price+asc",
        'authority': 'www.stubhub.com',
        'x-requested-with': 'XMLHttpRequest',
        'x-distil-ajax': 'yyqvbuqewxtcufrxveb',
    }

    params = {
        'eventId': eventId,
        'start': '0',
        'sort': 'price asc,value desc',
        'edgeControlEnabled': 'true',
        'priceType': 'nonBundledPrice',
        'shstore': '1',
    }

    response = requests.get('https://www.stubhub.com/bfx/api/search/inventory/v2/listings', headers=headers,
                            params=params).json()

    jsonListings = response['listing']
    numListings = int(response['totalListings'])
    asyncResults = []

    for listingStart in range(100, numListings, 100):
        asyncResults.append(pool.apply_async(getListingByStart, args=(eventId, listingStart)))

    for r in asyncResults:
        jsonListings.extend(r.get()['listing'])

    return jsonListings

def getListingByStart(eventId, start):
    session = Session()

    headers = {
        'cookie': 'bff-activity=eaa1be29-551b-45f6-8e27-27e0ffa78c0a; SH_VI=d5d23139387a4046a12055161a0feaee; SH6_USER_PREF=%7B%22location%22%3A%7B%22geoNameId%22%3A4926563%2C%22city%22%3A%22South%20Bend%22%2C%22stateCode%22%3A%22IN%22%2C%22state%22%3A%22Indiana%22%2C%22countryCode%22%3A%22US%22%2C%22country%22%3A%22United%20States%22%2C%22latitude%22%3A41.68338%2C%22longitude%22%3A-86.25001%2C%22key%22%3A4926563%2C%22name%22%3A%22South%20Bend%2C%20IN%22%7D%7D; AKA_A2=A; ak_bmsc=A0B712FEB0F7550FC7373B342F8609F8173EE3B7005D00007905365D84AD6527~pls3kE3JuXUKGT+/T1L5dbrlqyZpBGM8h5qQp24fsDqakf+2d8RzA8oUv8dCyMYRbYylT/VXIU8rA2fqyihvmWuBalaFwVuQdvC2ijm3s5LW+lTzPO74dbwwf0SkqMTjQ8mjFgFx7Kw/hvZOgw5ZXAx8H/aRq9VzwQQaOsOiZ2TdkmTaITpbO8x5fahBgtUWRnDWDHTGhN7LmppBAVbXW6yz/8NluJpyHokTDokBmp0gk=; bm_sz=AF4E9010F179FFA791EBC167BDBA98B5~YAAQt+M+F2KAxd9rAQAAg2MFGwRnxdZuYxvCbW3BN9AH9HyHWOXpp8yHZmmcZ8VGbJJyQmD+rrdYylYxclxZJxXb3CYIuG7VMqrRjlO+t6+PWfyhEzDQ7xE5I1cB+3RiIluF8xwwnFQGxRbobeN9W/on2OSQze+t45GDwTYIZtYJps5NC8WRD7uhyKDVyJgB; _sim_si=744916ED-4F2E-4E47-BE71-DB3C05F1B046; _sim_uuid=BAC8BBFA-3C1A-4FAD-9A47-B53728E732B7; S_ACCT=stubhub%2Cstubhubglobal; _sim_li=YjQzYWQ5NWMtMDZmNS00MWM3LTk0M2UtODk0MjhhNjcwNzM2LmxvY2FsLDk4LjIyMy4yMzguNQ==; s_ecid=MCMID%7C83456816773556929564510389092603171315; AMCVS_1AEC46735278551A0A490D45%40AdobeOrg=1; AMCV_1AEC46735278551A0A490D45%40AdobeOrg=-1303530583%7CMCIDTS%7C18100%7CMCMID%7C83456816773556929564510389092603171315%7CMCAID%7CNONE%7CMCOPTOUT-1563828635s%7CNONE%7CvVersion%7C3.3.0; D_IID=714EB4A1-F4F6-3D6D-89CA-1A7EDECFCFF9; D_UID=2C0A5867-8D5D-38AB-9FAE-0FACA631F2EC; D_ZID=E5B05652-B3ED-3393-89BF-ED55AD5DB2C6; D_ZUID=F9B7094E-BD82-366F-A12A-4752BBA8E8D4; D_HID=4965CBA5-2B21-3841-86AB-9463B588832D; D_SID=98.223.238.5:yQQOZ392CHGU3UyLpkya8ESvCgGLCILEzgJHCTt8s5A; akacd_PCF_Prod=1563824103~rv=32~id=57f6e0b31187ae01b5c409dc6f7e4655; SH_AT=1XNOHCPxzhOmYfQsadRFfX%2FOMRCZ0KKzhzQg%2BzAtaxxW5pfv1Rx11KOIF7aMprwAi1zTpPFp2RZGReU5sKeZrDtPT322C9hLSzkANlrvaac%3D; DC=lvs01; S_ACCT=stubhub; SH_VI=d5d23139387a4046a12055161a0feaee; TLTHID=2DB5295EACB710AC048BB801C1813758; TLTSID=2DB5295EACB710AC048BB801C1813758; SH_BAU=%7B%22id%22%3A%221563824737.387a4046a1205516%22%2C%22key%22%3A%22EguJDGSwZkRx2w0D8RvmEvXKVm%2BvAq5J%2BdnOAfxBNss%3D%22%2C%22algorithm%22%3A%22sha256%22%7D; bm_sv=702870A87CEA67083DE52AD5AE64CED5~wEuMV0iJorCB1vJb5HV5Zdyi1N7ruepk+8lhie2ndmSXvxK3vS9dDoJ+aRYISusOaJIRpg19n8jTzKWtFs9hwF5d+Fd/da1J7L8oRN3OuC57EMMVpsE0AT0A/QXsQxNpKd++iJWynjVEFArbE0DWDQ7T6SDQHboU2zFxpI1iAz8=; _abck=08AF3A1204CEBF73A0579964DE827B4C~0~YAAQt+M+FwHKxd9rAQAAIJgrGwLX5qDngzRHIUukLgUYvVp0ZrZpJEg5Atgl8Y0ufUPwPn1lzq3s3FRnmQpP4Ugt7F3RkvTL8HtnnuyjTGW/f2BBL88NTY0c+LqKXv2Ox6tpgDnE+2+8lZ4XTbt9bJldMIRcge6Y0pbutPLDmIv7TVJsHH/HXi46fi/a7uJPueAfqK3hjD/msV5q/AV1w6AsjENGfFbgpzg/wVCzpJ0MXR7/g6jmULf6HSKOHzIPbiq84pmQF9T/dJN3NnltsfSeWja5b54sfNOKWxSUax13BktupjX0kCTn~-1~-1~-1; s_sess=%20s_cpc%3D0%3B%20s_sq%3D%3B%20s_cc%3Dtrue%3B%20s_ptc%3D0.01%255E%255E0.00%255E%255E0.00%255E%255E0.06%255E%255E0.47%255E%255E0.03%255E%255E0.96%255E%255E0.04%255E%255E1.55%3B%20s_tp%3D747%3B%20s_ppv%3DUE%25253A%252520Event%252520Details%25253A%252520Toggle%252520Splitscreen%25253A%252520FilterView%252C97%252C97%252C722%3B; s_tps=1852; s_pvs=11156; s_pers=%20s_dfa%3Dstubhub%252Cstubhubglobal%7C1563825633931%3B%20s_vs%3D1%7C1563825740531%3B%20gpv_v9%3DUE%253A%2520Event%2520Details%253A%2520Toggle%2520Splitscreen%253A%2520FilterView%7C1563825740534%3B%20s_nr%3D1563823940538-New%7C1597951940538%3B',
        'accept-encoding': 'gzip, deflate, br',
        'com-stubhub-dye-path': 'b6f68a2b93314168988edb2fcbc4cecd,0a0687fbc1274294adcc27e50ebfc02e',
        'accept-language': 'en-us',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'content-type': 'application/json',
        'accept': 'application/json',
        'referer': "https://www.stubhub.com/cleveland-indians-tickets-cleveland-indians-cleveland-progressive-field-7-30-2019/event/103822145/?sort=price+asc",
        'authority': 'www.stubhub.com',
        'x-requested-with': 'XMLHttpRequest',
        'x-distil-ajax': 'yyqvbuqewxtcufrxveb',
    }

    params = {
        'eventId': eventId,
        'start': start,
        'sort': 'price asc,value desc',
        'edgeControlEnabled': 'true',
        'priceType': 'nonBundledPrice',
        'shstore': '1',
    }
    return session.get('https://www.stubhub.com/bfx/api/search/inventory/v2/listings', headers=headers,
                                    params=params).json()

def processListings(jsonListings, gameId, pool:mp.Pool) -> (list, list):
    listings = []
    asyncResults = []

    for jsonListing in jsonListings:
        asyncResults.append(pool.apply_async(processListing, args=(jsonListing, gameId)))

    for r in asyncResults:
        listing = r.get()
        if listing is not None:
            listings.append(listing)

    return listings

def processListing(jsonListing, gameId):
    if 'sectionId' in jsonListing:
        listingTickets = []

        price = jsonListing["price"]["amount"]
        sectionId = jsonListing["sectionId"]
        sectionName = jsonListing["zoneName"]
        sectionNumber = jsonListing["sectionName"].split(" ")[-1]
        if not str.isdigit(sectionNumber):
            sectionNumber = None
        seatCount = len(jsonListing["seats"])
        listingId = jsonListing["seats"][0]["listingId"]

        for jsonTicket in jsonListing["seats"]:
            try:
                ticket = Ticket(listingId, jsonTicket["row"], jsonTicket["seatNumber"])
            except KeyError:
                ticket = Ticket(listingId, jsonTicket["row"])
            listingTickets.append(ticket)
        listing = Listing(listingId, price, sectionId, sectionName, sectionNumber, seatCount, gameId, listingTickets)
        return listing
    else:
        return None

def filterListings(cursor, listings):
    sql = "SELECT listing_id FROM (VALUES "
    for listing in listings:
        sql += f"({listing.listingId}),"
    sql = f"{sql[:-1]}) V(listing_id) EXCEPT SELECT listing_id FROM Listings"
    newListingIds = []
    cursor.execute(sql)
    row = cursor.fetchone()
    while row:
        newListingIds.append(row[0])
        row = cursor.fetchone()

    newListings = []
    for listing in listings:
        if listing.listingId in newListingIds:
            newListings.append(listing)
    return newListings

def addNewListingsToDb(cursor, listings):

    params = [(listing.listingId, listing.sectionId, listing.sectionName,
               listing.sectionNumber, listing.seatCount, listing.gameId) for listing in listings]

    cursor.executemany("INSERT INTO [Listings] (listing_id, section_id, section_name, section_number, seat_count, game_id) VALUES (?, ?, ?, ?, ?, ?)", params)
    cursor.commit()

def addNewTicketsToDb(cursor, listings):

    from datetime import datetime
    currentTime = datetime.utcnow()
    currentDate = f"{currentTime.year}-{currentTime.month:02d}-{currentTime.day:02d}"

    params = []
    for listing in listings:
        params.extend([(ticket.listingId, ticket.seatNumber if ticket.seatNumber and str.isdigit(ticket.seatNumber) else None,
                        ticket.seatRow, currentDate) for ticket in listing.tickets])

    cursor.executemany("INSERT INTO [Tickets] (listing_id, seat_number, seat_row, date_retrieved) VALUES (?, ?, ?, ?)", params)
    cursor.commit()

def addPricesToDb(cursor, listings):
    from datetime import datetime
    currentTime = datetime.utcnow()
    date = f"{currentTime.year}-{currentTime.month:02d}-{currentTime.day:02d}"
    currentTime = f"{currentTime.hour:02d}:{currentTime.minute:02d}:{currentTime.second:02d}"

    params = [(listing.price, listing.listingId, date, currentTime) for listing in listings]

    cursor.executemany("INSERT INTO [Prices] (price, listing_id, date_retrieved, time_retrieved) VALUES (?, ?, ?, ?)", params)
    cursor.commit()


def initialRun(cursor):
    teamDict = getTeamIds(cursor)
    for teamId in teamDict:
        time.sleep(random.choice(randomTimings))
        gamesForTeam = getGames(teamId)
        addGamesToTable(gamesForTeam, cursor)
        print("Success for " + str(teamId))

def dailyRun(cursor):
    games = getGamesPastNow(cursor)
    pool = mp.Pool(mp.cpu_count())
    startTime = time.time()
    lastTime = startTime
    gamesProcessed = 0
    for game in games:
        try:
            listings = processListings(getListingsParallel(game.gameId, pool), game.gameId, pool)
            if len(listings) == 0:
                print(f"NO LISTINGS RETRIEVED. STOPPING ON {game.gameId}")
                break
            newListings = filterListings(cursor, listings)
            addNewListingsToDb(cursor, newListings)
            addNewTicketsToDb(cursor, newListings)
            addPricesToDb(cursor, newListings)
            gamesProcessed += 1
            totalTime = round(time.time() - startTime, 2)
            processTime = round(time.time() - lastTime, 2)
            print(f"Success for {game.gameId}. Took {processTime} seconds for {len(newListings)} new listings. Average process time is {totalTime / gamesProcessed}.")
            print(f"Current total time pace is {totalTime / gamesProcessed * len(games)} with {totalTime / gamesProcessed * len(games) - totalTime} left.")
            lastTime = time.time()
        except Exception as e:
            print(f"FAILURE FOR {game.gameId}")
            print(str(e))

cnxn, cursor = connect()

#initialRun(cursor)
dailyRun(cursor)

cnxn.commit()
cursor.close()
cnxn.close()