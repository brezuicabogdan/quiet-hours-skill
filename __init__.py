from mycroft import MycroftSkill, intent_file_handler


class QuietHours(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('hours.quiet.intent')
    def handle_hours_quiet(self, message):
        self.speak_dialog('hours.quiet')


def create_skill():
    return QuietHours()

