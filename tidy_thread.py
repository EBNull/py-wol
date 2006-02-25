class Tidy_Thread(Thread):
    def __init__(self):
        Thread.__init__(self, group=None, target=None, name="Tidy Thread")
        Thread.setDaemon(self, True)
    def run(self):
        while True:
            time.sleep(5)
            for u in Connected_Users.getusers():
                if u.game != None:
                    if u.game.name != u.room:
                        DebugLog('tidy', None, "Tidying up %s, who was in room %s and game %s"%(u.name, u.room, game.name))
                        u.game.delplayer(u)
            for g in Games.g.values():
                for p in g.players:
                    if p.game != g:
                        DebugLog('tidy', None, "Tidying up %s, who claimed to hold %s but didn't"%(g.name, p.name))
                        g.players.remove(p)
                if len(g.players) == 0:
                    DebugLog('tidy', None, "Tidying up %s, which has no players."%(g.name))
                    Games.delgame(g.gid)
