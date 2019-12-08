# import sqlite3 as lite
# from sportsreference.ncaaf.roster import Roster
#
# con = None
# cur = None
#
# def stat_scraper(team = "Nebraska", year = 2018):
#     setupDBCon()
#     createStatsTable()
#     roster = Roster(team, year = year)
#
#     for player in roster.players:
#         stats = player.dataframe
#         if stats is not None:
#             for index, row in stats.iterrows():
#                 stat_dict = {'name': player.name, 'team_abbreviation': row.team_abbreviation, 'position': row.position, 'year': row.year, 'season': row.season, 'adjusted_yards_per_attempt': row.adjusted_yards_per_attempt, 'assists_on_tackles': row.assists_on_tackles, 'attempted_passes': row.attempted_passes, 'completed_passes': row.completed_passes, 'passing_yards': None, 'extra_points_made': row.extra_points_made, 'field_goals_made': row.field_goals_made, 'fumbles_forced': row.fumbles_forced, 'fumbles_recovered': row.fumbles_recovered, 'fumbles_recovered_for_touchdown': row.fumbles_recovered_for_touchdown, 'games': row.games, 'height': row.height, 'interceptions': row.interceptions, 'interceptions_returned_for_touchdown': row.interceptions_returned_for_touchdown, 'interceptions_thrown': row.interceptions_thrown, 'kickoff_return_touchdowns': row.kickoff_return_touchdowns, 'other_touchdowns': row.other_touchdowns, 'passes_defended': row.passes_defended,
#                              'passing_completion': row.passing_completion, 'passing_touchdowns': row.passing_touchdowns, 'passing_yards_per_attempt': row.passing_yards_per_attempt, 'player_id': row.player_id, 'plays_from_scrimmage': row.plays_from_scrimmage, 'points': row.points, 'punt_return_touchdowns': row.punt_return_touchdowns, 'quarterback_rating': row.quarterback_rating, 'receiving_touchdowns': row.receiving_touchdowns, 'receiving_yards': row.receiving_yards, 'receiving_yards_per_reception': row.receiving_yards_per_reception, 'receptions': row.receptions, 'rush_attempts': row.rush_attempts, 'rush_touchdowns': row.rush_touchdowns, 'rush_yards': row.rush_yards, 'rush_yards_per_attempt': row.rush_yards_per_attempt, 'rushing_and_receiving_touchdowns': row.rushing_and_receiving_touchdowns, 'sacks': row.sacks, 'safeties': row.safeties, 'solo_tackles': row.solo_tackles, 'tackles_for_loss': row.tackles_for_loss, 'total_tackles': row.total_tackles,
#                              'total_touchdowns': row.total_touchdowns, 'two_point_conversions': row.two_point_conversions, 'weight': row.weight, 'yards_from_scrimmage': row.yards_from_scrimmage, 'yards_from_scrimmage_per_play': row.yards_from_scrimmage_per_play, 'yards_recovered_from_fumble': row.yards_recovered_from_fumble, 'yards_returned_from_interceptions': row.yards_returned_from_interceptions, 'yards_returned_per_interception': row.yards_returned_per_interception}
#                 s = stat_dict
#                 cur.execute('INSERT INTO stats(\
#                 name,\
#                 team_abbreviation,\
#                 position,\
#                 year,\
#                 season,\
#                 adjusted_yards_per_attempt,\
#                 assists_on_tackles, \
#                 attempted_passes, \
#                 completed_passes, \
#                 passing_yards, \
#                 extra_points_made, \
#                 field_goals_made, \
#                 fumbles_forced, \
#                 fumbles_recovered, \
#                 fumbles_recovered_for_touchdown, \
#                 games, \
#                 height, \
#                 interceptions, \
#                 interceptions_returned_for_touchdown, \
#                 interceptions_thrown, \
#                 kickoff_return_touchdowns, \
#                 other_touchdowns, \
#                 passes_defended, \
#                 passing_completion, \
#                 passing_touchdowns, \
#                 passing_yards_per_attempt, \
#                 player_id, \
#                 plays_from_scrimmage, \
#                 points, \
#                 punt_return_touchdowns, \
#                 quarterback_rating, \
#                 receiving_touchdowns, \
#                 receiving_yards, \
#                 receiving_yards_per_reception, \
#                 receptions, \
#                 rush_attempts, \
#                 rush_touchdowns, \
#                 rush_yards, \
#                 rush_yards_per_attempt, \
#                 rushing_and_receiving_touchdowns, \
#                 sacks, \
#                 safeties, \
#                 solo_tackles, \
#                 tackles_for_loss, \
#                 total_tackles, \
#                 total_touchdowns, \
#                 two_point_conversions, \
#                 weight, \
#                 yards_from_scrimmage, \
#                 yards_from_scrimmage_per_play, \
#                 yards_recovered_from_fumble, \
#                 yards_returned_from_interceptions, \
#                 yards_returned_per_interception\
#                 ) \
#                 VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
#                 (s['name'], s['team_abbreviation'], s['position'], s['year'], s['season'], s['adjusted_yards_per_attempt'], s['assists_on_tackles'],
#                  s['attempted_passes'], s['completed_passes'], s['passing_yards'], s['extra_points_made'], s['field_goals_made'], s['fumbles_forced'],
#                  s['fumbles_recovered'], s['fumbles_recovered_for_touchdown'], s['games'], s['height'], s['interceptions'], s['interceptions_returned_for_touchdown'],
#                  s['interceptions_thrown'], s['kickoff_return_touchdowns'], s['other_touchdowns'], s['passes_defended'], s['passing_completion'],
#                  s['passing_touchdowns'], s['passing_yards_per_attempt'], s['player_id'], s['plays_from_scrimmage'], s['points'], s['punt_return_touchdowns'],
#                  s['quarterback_rating'], s['receiving_touchdowns'], s['receiving_yards'], s['receiving_yards_per_reception'], s['receptions'], s['rush_attempts'],
#                  s['rush_touchdowns'], s['rush_yards'], s['rush_yards_per_attempt'], s['rushing_and_receiving_touchdowns'], s['sacks'], s['safeties'], s['solo_tackles'], s['tackles_for_loss'],
#                  s['total_tackles'], s['total_touchdowns'], s['two_point_conversions'], s['weight'], s['yards_from_scrimmage'], s['yards_from_scrimmage_per_play'], s['yards_recovered_from_fumble'],
#                  s['yards_returned_from_interceptions'], s['yards_returned_per_interception']))
#                 con.commit()
#
#     closeDB()
#
#
# def createStatsTable():
#     cur.execute("CREATE TABLE If NOT EXISTS stats(id INTEGER PRIMARY KEY NOT NULL, \
#     name TEXT, \
#     team_abbreviation TEXT, \
#     position TEXT, \
#     year INTEGER, \
#     season TEXT, \
#     adjusted_yards_per_attempt FLOAT, \
#     assists_on_tackles INTEGER, \
#     attempted_passes INTEGER, \
#     completed_passes INTEGER, \
#     passing_yards INTEGER, \
#     extra_points_made INTEGER, \
#     field_goals_made INTEGER, \
#     fumbles_forced INTEGER, \
#     fumbles_recovered INTEGER, \
#     fumbles_recovered_for_touchdown INTEGER, \
#     games INTEGER, \
#     height TEXT, \
#     interceptions INTEGER, \
#     interceptions_returned_for_touchdown INTEGER, \
#     interceptions_thrown INTEGER, \
#     kickoff_return_touchdowns INTEGER, \
#     other_touchdowns INTEGER, \
#     passes_defended INTEGER, \
#     passing_completion FLOAT, \
#     passing_touchdowns INTEGER, \
#     passing_yards_per_attempt FLOAT, \
#     player_id TEXT, \
#     plays_from_scrimmage INTEGER, \
#     points INTEGER, \
#     punt_return_touchdowns INTEGER, \
#     quarterback_rating FLOAT, \
#     receiving_touchdowns INTEGER, \
#     receiving_yards INTEGER, \
#     receiving_yards_per_reception FLOAT, \
#     receptions INTEGER, \
#     rush_attempts INTEGER, \
#     rush_touchdowns INTEGER, \
#     rush_yards INTEGER, \
#     rush_yards_per_attempt FLOAT, \
#     rushing_and_receiving_touchdowns INTEGER, \
#     sacks FLOAT, \
#     safeties INTEGER, \
#     solo_tackles INTEGER, \
#     tackles_for_loss FLOAT, \
#     total_tackles FLOAT, \
#     total_touchdowns INTEGER, \
#     two_point_conversions INTEGER, \
#     weight FLOAT, \
#     yards_from_scrimmage INTEGER, \
#     yards_from_scrimmage_per_play FLOAT, \
#     yards_recovered_from_fumble INTEGER, \
#     yards_returned_from_interceptions INTEGER, \
#     yards_returned_per_interception FLOAT \
#     )")
#
# def setupDBCon():
#     global con
#     global cur
#     con = lite.connect('stats.db')
#     cur = con.cursor()
#
# def closeDB():
#     con.close()