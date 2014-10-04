import twitter

class FakeApiHandler:
    def __init__(self):
        self.statuses = ["I am a status","I like to eat you", "you're weird","I like bananas","politics are republicans","I'm still a twitter post"]
        self.replys = ["hello john","hello jo","nice weather isn't it","indeed it is"][-1::-1]
    
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
