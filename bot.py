import logging
import sys  # For fortune
import getpass  # For entering your password
from optparse import OptionParser
import sleekxmpp
import sqlite3
from collections import defaultdict
import subprocess  # For fortune
import os.path
from random import randint  # For BinaryGame


def repInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
points = {}
m = randint(1, 32)


def BinaryGame(n, requester):

    global m
    if n == m:
        m = randint(1, 32)
        if requester in points:
            points[requester] += 1
        else:
            points[requester] = 1
        return True
    else:
        return False


class MucBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("presence", self.muc_online)
        self.add_event_handler("ssl_invalid_cert", self.inv_cert)
        self.add_event_handler("ssl_expired_cert", self.exp_cert)
        self.add_event_handler("groupchat_message", self.muc_message)

        self.room = room
        self.nick = nick

    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        self.plugin['xep 0045'].joinMUC(self.room, self.nick, wait=True)

    def muc_online(self, presence):
        handle = str(presence['muc']['jid']).split('@')[0]
        nick = str(presence['muc']['nick'])
        userdata[nick] = handle
        print(handle)  # For debugging issues with users
        print(nick)

    def inv_cert(self, pem):
        return

    def exp_cret(self, cert):
        return

    def muc_message(self, msg):

        if msg['mucnick'] != self.nick and self.nick + " help" in msg['body']:
            helpmsg = self.nick + " XMPP bot commands are as follows: \n"
            helpmsg += self.nick + " help - displays this help message\n"
            helpmsg += self.nick + " jid - prints out your jabber id\n"
            helpmsg += self.nick + " stats - displays the number of points of the user\n"
            helpmsg += self.nick + " fortune - outputs the result of the 'fortune' command in linux\n"
            helpmsg += self.nick + " kickme - exactly what it says - kicks the user that asks me to\n"
#			helpmsg += self.nick + " transfer - REDACTED\n"
#			helpmsg += self.nick + " puzz - REDACTED\n"
            helpmsg += self.nick + " info-game - play a game with " + self.nick + "! :)\n"

            self.send_message(mto=msg['from'].bare, mbody=helpmsg, mtype='groupchat')

        if msg['mucnick'] != self.nick and msg['body'].startswith(self.nick + " jid"):
            self.send_message(mto=msg['from'].bare, mbody="Hello, %s" % userdata[msg['mucnick']], mtype='groupchat')

        if msg['mucnick'] != self.nick and msg['body'].startswith(self.nick + " stats"):

            requester = userdata[msg['mucnick']]  # Sets the requester to jid

            if requester not in points:
                statsmsg = "You have no points"
            else:
                statsmsg = requester + " has " + str(points[requester]) + " point(s)."

            self.send_message(mto=msg['from'].bare, mbody=statsmsg, mtype='groupchat')

        if msg['mucnick'] != self.nick and msg['body'].startswith(self.nick + " fortune"):

            res = subprocess.check_output(["fortune", ""])
            self.send_message(mto=msg['from'].bare, mbody=res.decode('utf-8'), mtype='groupchat')

        if msg['mucnick'] != self.nick and msg['body'].startswith(self.nick + " kickme"):
            self.send_message(mto=msg['from'].bare, mbody="/kick, %s" % userdata[msg['mucnick']], mtype='groupchat')

        if msg['mucnick'] != self.nick and msg['body'].startswith(self.nick + " info-game"):

            gamemsg = "Wanna play a game with me? Type " + self.nick + " game n\n"
            gamemsg += "where n is a number between 1 and 32 inclusive"
            gamemsg += ", and I will tell you if you are right or wrong."

            self.send_message(mto=msg['from'].bare, mbody=gamemsg, mtype='groupchat')

        if msg['mucnick'] != self.nick and msg['body'].startswith(self.nick + " game"):

            if len(msg['body'].split()) < 3:
                return
            else:
                if repInt(msg['body'].split()[2]):  # Checks if the input is an interger (valid)
                    n = int(msg['body'].split()[2])
                else:
                    self.send_message(mto=msg['from'].bare, mbody="Invalid use of game.", mtype='groupchat')
                    return
                requester = userdata[msg['mucnick']]  # Sets the requester to jid

                if BinaryGame(n, requester):
                    self.send_message(mto=msg['from'].bare, mbody=str(n) + " is correct! I now have a new number, wanna guess it?", mtype='groupchat')
                else:
                    if m > n:
                        self.send_message(mto=msg['from'].bare, mbody=str(n) + " is incorrect! (the answer is greater than " + str(n) + ") Try again?", mtype='groupchat')
                    if m < n:
                        self.send_message(mto=msg['from'].bare, mbody=str(n) + " is incorrect! (the answer is less than " + str(n) + ") Try again?", mtype='groupchat')

if __name__ == '__main__':

    optp = OptionParser()

    optp.add_option("-j", "--jid", dest="jid", help="JID to use")
    optp.add_option("-p", "--password", dest="password", help="password to use")
    optp.add_option("-r", "--rood", dest="room", help="chat room to join")
    optp.add_option("-n", "--nick", dest="nick", help="nickmname to use")

    opts, args = optp.parse_args()

    logging.basicConfig(level=logging.DEBUG, format='%(levelname) - 8s %(message)s')

    if opts.jid is None:
        opts.jid = input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.room is None:
        opts.room = input("MUC Room: ")
    if opts.nick is None:
        opts.nick = input("MUC Nickname: ")
    xmpp = MucBot(opts.jid, opts.password, opts.room, opts.nick)

    xmpp.register_plugin('xep_0030')
    xmpp.register_plugin('xep_0045')
    xmpp.register_plugin('xep_0199')

    if xmpp.connet():
        xmpp.process(block=True)
        print("Done")

    else:
        print("Connection failed")
