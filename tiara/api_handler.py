import twitter

class FakeApiHandler:
    def __init__(self):
        self.statuses = ["s I am a status","s I like to eat you", "s you're weird","s I like bananas","s politics are republicans","s I'm still a twitter post"]
        self.replys = ["r3 hello john","r2 hello jo","r1 nice weather isn't it","r0 indeed it is"][-1::-1]
    
    def ShowStatus(self, status_id):
        if status_id < len(self.replys):
            u = twitter.Status()
            u.SetText(self.replys[status_id])
            if status_id + 1 < len(self.replys):
                u.SetInReplyToStatusId(status_id + 1)
            return u
        return None

    def ShowStatuses(self, user_id):
        if user_id == 0:
            result = []
            for st in self.statuses:
                u = twitter.Status()
                u.SetText(st)
                result.append(u)
            return result
        return None
