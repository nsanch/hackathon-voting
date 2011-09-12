#!/usr/bin/python

import cgi
import logging
import urllib2

from django.utils import simplejson

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
            
# config = {'phone': '(917) 310-5220'}

class Team(db.Model):
  name = db.StringProperty()
  number = db.IntegerProperty()

class Vote(db.Model):
  """Contains the votes."""
  phone = db.StringProperty()
  vote = db.IntegerProperty()

class ReceiveVote(webapp.RequestHandler):
  """Receive a vote from a phone number and store it."""
  def reply(self, resp):
    self.response.out.write('<Response><Sms>'+resp+'</Sms></Response>')

  def post(self):
    phone = self.request.get('From')
    try:
      choice = int(self.request.get('Body').strip())
    except:
      self.reply('Sorry, I couldn\'t parse that. :( Send 2, 2, or 3 depending on which team you\'re voting for.')
      return

    db.run_in_transaction(self.write_vote, phone, choice)

  def write_vote(self, phone, choice):
    previous_vote = Vote.get_by_key_name(phone)
    if previous_vote:
      previous_vote.vote = choice
      previous_vote.put()
      self.reply('Okay, updated your vote!')
    else:
      vote = Vote(key_name=phone)
      vote.vote = choice 
      vote.phone = phone
      vote.put()
      self.reply('Okay, got your vote!')


class FetchVotes(webapp.RequestHandler):
  """Fetches totals"""
  def get(self):
    all_votes = Vote.all().fetch(10000)
    all_teams = Team.all().fetch(100)
    reply = {}
    for team in all_teams:
      reply.update({str(team.number): {'name': 'Team %d - %s' % (team.number, team.name), 'total': 0}})
    for vote in all_votes:
      team = reply[str(vote.vote)]
      team['total'] = team['total'] + 1
    reply_json = simplejson.dumps([reply[k] for k in reply.keys()])
    self.response.out.write(reply_json)

application = webapp.WSGIApplication([('/receive', ReceiveVote),
                                      ('/fetch', FetchVotes)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
